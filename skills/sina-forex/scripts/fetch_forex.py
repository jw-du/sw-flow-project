#!/usr/bin/env python3
"""
新浪财经外汇行情获取工具
国内可用、免费、支持美元/人民币等多种货币对

数据源：新浪财经 (hq.sinajs.cn)
特点：
- 国内直接访问，无需翻墙
- 完全免费
- 实时更新
- 支持在岸/离岸人民币及主要货币对
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

# 货币对映射表 (新浪财经代码)
# 格式说明：fx_s{货币对}，如 fx_susdcny 表示 USD/CNY
FOREX_PAIRS = {
    # 人民币相关
    "USDCNY": {"sina_code": "fx_susdcny", "name": "美元/人民币", "desc": "美元兑在岸人民币"},
    "USDCNH": {"sina_code": "fx_susdcnh", "name": "美元/离岸人民币", "desc": "美元兑离岸人民币"},
    "EURCNY": {"sina_code": "fx_seurcny", "name": "欧元/人民币", "desc": "欧元兑人民币"},
    "GBPCNY": {"sina_code": "fx_sgbpcny", "name": "英镑/人民币", "desc": "英镑兑人民币"},
    "JPYCNY": {"sina_code": "fx_sjpy100cny", "name": "日元/人民币", "desc": "100日元兑人民币"},
    "HKDCNY": {"sina_code": "fx_shkdcny", "name": "港币/人民币", "desc": "港币兑人民币"},

    # 主要货币对
    "EURUSD": {"sina_code": "fx_seurusd", "name": "欧元/美元", "desc": "欧元兑美元"},
    "GBPUSD": {"sina_code": "fx_sgbpusd", "name": "英镑/美元", "desc": "英镑兑美元"},
    "USDJPY": {"sina_code": "fx_susdjpy", "name": "美元/日元", "desc": "美元兑日元"},
    "USDCHF": {"sina_code": "fx_susdchf", "name": "美元/瑞郎", "desc": "美元兑瑞士法郎"},
    "AUDUSD": {"sina_code": "fx_saudusd", "name": "澳元/美元", "desc": "澳元兑美元"},
    "USDCAD": {"sina_code": "fx_susdcad", "name": "美元/加元", "desc": "美元兑加元"},
    "NZDUSD": {"sina_code": "fx_snzdbusd", "name": "纽元/美元", "desc": "纽元兑美元"},

    # 其他重要货币对
    "XAUUSD": {"sina_code": "fx_sxauusd", "name": "黄金/美元", "desc": "现货黄金"},
    "XAGUSD": {"sina_code": "fx_sxagusd", "name": "白银/美元", "desc": "现货白银"},
}


def fetch_forex_data(pair_code: str) -> Optional[Dict]:
    """
    从新浪财经获取外汇实时行情

    Args:
        pair_code: 货币对代码，如 USDCNY

    Returns:
        包含汇率数据的字典，失败返回 None
    """
    if pair_code not in FOREX_PAIRS:
        raise ValueError(f"不支持的货币对: {pair_code}。支持的货币对: {', '.join(FOREX_PAIRS.keys())}")

    pair_info = FOREX_PAIRS[pair_code]
    sina_code = pair_info["sina_code"]

    # 新浪财经接口
    url = f"https://hq.sinajs.cn/list={sina_code}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)

        # 新浪返回 GBK 编码
        data = resp.read().decode("gbk")

        # 解析数据
        # 格式: var hq_str_fx_susdcny="15:05:17,6.8930,6.8948,6.9058,...,在岸人民币,-0.1723,-0.0119,...";
        if not data or "var hq_str_" not in data:
            return None

        # 提取引号内的数据
        start = data.find('"') + 1
        end = data.rfind('"')
        if start <= 0 or end <= start:
            return None

        content = data[start:end]
        if not content:
            return None

        fields = content.split(",")
        if len(fields) < 12:
            return None

        result = {
            "pair": pair_code,
            "symbol": pair_code,
            "name": pair_info["name"],
            "desc": pair_info["desc"],
            "sina_code": sina_code,
            "price": float(fields[2]) if fields[2] else None,
            "high": float(fields[3]) if fields[3] else None,
            "low": float(fields[5]) if fields[5] else None,
            "open": float(fields[6]) if fields[6] else None,
            "previous_close": float(fields[7]) if fields[7] else None,
            "bid": float(fields[8]) if fields[8] else None,
            "ask": float(fields[6]) if fields[6] else None,
            "change": float(fields[10]) if len(fields) > 10 and fields[10] else None,
            "change_pct": float(fields[11]) if len(fields) > 11 and fields[11] else None,
            "quote_time": f"{fields[17] if len(fields) > 17 else ''} {fields[0]}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if result["change_pct"] is None and result["price"] and result["previous_close"]:
            result["change_pct"] = round((result["price"] - result["previous_close"]) / result["previous_close"] * 100, 4)

        if result["change"] is None and result["price"] and result["previous_close"]:
            result["change"] = round(result["price"] - result["previous_close"], 4)

        return result

    except urllib.error.URLError as e:
        print(f"网络错误: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"获取数据错误: {e}", file=sys.stderr)
        return None


def fetch_multiple_pairs(pair_codes: List[str]) -> List[Dict]:
    results = []
    for code in pair_codes:
        try:
            data = fetch_forex_data(code)
            if data:
                results.append(data)
            else:
                results.append({
                    "pair": code,
                    "error": "获取数据失败",
                    "name": FOREX_PAIRS.get(code, {}).get("name", code)
                })
        except Exception as e:
            results.append({
                "pair": code,
                "error": str(e),
                "name": FOREX_PAIRS.get(code, {}).get("name", code)
            })
    return results


def format_output(data: Dict, use_json: bool = False) -> str:
    if use_json:
        return json.dumps(data, ensure_ascii=False, indent=2)

    lines = [
        "=" * 50,
        f"货币对: {data['name']} ({data['pair']})",
        "=" * 50,
    ]

    if data.get('price'):
        lines.append(f"最新价: {data['price']}")
    if data.get('bid'):
        lines.append(f"买入参考: {data['bid']}")
    if data.get('high') and data.get('low'):
        lines.append(f"最高/最低: {data['high']} / {data['low']}")
    if data.get('open') and data.get('previous_close'):
        lines.append(f"开盘/昨收: {data['open']} / {data['previous_close']}")
    if data.get('change') is not None:
        change_symbol = "▲" if data['change'] >= 0 else "▼"
        lines.append(f"涨跌额: {change_symbol}{data['change']}")
    if data.get('change_pct') is not None:
        change_symbol = "+" if data['change_pct'] >= 0 else ""
        lines.append(f"涨跌幅: {change_symbol}{data['change_pct']}%")
    if data.get('quote_time'):
        lines.append(f"报价时间: {data['quote_time']}")

    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="新浪财经外汇行情获取工具 - 国内可用、免费、支持美元人民币"
    )
    parser.add_argument(
        "pairs",
        nargs="*",
        help=f"货币对代码，支持: {', '.join(FOREX_PAIRS.keys())}"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="JSON格式输出"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有支持的货币对"
    )

    args = parser.parse_args()

    if args.list:
        print("支持的货币对列表:")
        print("=" * 60)
        for code, info in FOREX_PAIRS.items():
            print(f"{code:10} - {info['name']:15} ({info['desc']})")
        print("=" * 60)
        return

    if not args.pairs:
        print("错误: 请指定货币对代码，或使用 --list 查看支持的货币对", file=sys.stderr)
        print(f"\n示例: python fetch_forex.py USDCNY", file=sys.stderr)
        sys.exit(1)

    results = fetch_multiple_pairs(args.pairs)

    if args.json:
        if len(results) == 1:
            print(json.dumps(results[0], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for i, data in enumerate(results):
            if "error" in data:
                print(f"\n❌ {data['pair']}: {data['error']}")
            else:
                print(format_output(data, use_json=False))
            if i < len(results) - 1:
                print()


if __name__ == "__main__":
    main()
