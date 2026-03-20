#!/usr/bin/env python3
"""
美股外盘行情获取工具
获取美股三大指数、中概股ETF、富时A50期指实时行情

数据源：新浪财经 (国内可用、免费)
特点：
- 国内直接访问，无需翻墙
- 完全免费
- 实时更新
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

# 美股代码映射 (新浪财经代码)
MARKET_SYMBOLS = {
    # 美股指数
    "IXIC": {"sina_code": "gb_ixic", "name": "纳斯达克指数", "type": "index", "data_type": "us_stock"},
    "SPX": {"sina_code": "gb_inx", "name": "标普500", "type": "index", "data_type": "us_stock"},
    "DJI": {"sina_code": "gb_dji", "name": "道琼斯", "type": "index", "data_type": "us_stock"},
    
    # 中概股ETF
    "KWEB": {"sina_code": "gb_kweb", "name": "中概互联网ETF", "type": "cn_etf", "data_type": "us_stock"},
    "PGJ": {"sina_code": "gb_pgj", "name": "中国龙ETF", "type": "cn_etf", "data_type": "us_stock"},
    "ASHR": {"sina_code": "gb_ashr", "name": "沪深300ETF", "type": "cn_etf", "data_type": "us_stock"},
    
    # 其他重要ETF
    "QQQ": {"sina_code": "gb_qqq", "name": "纳斯达克100ETF", "type": "etf", "data_type": "us_stock"},
    "SPY": {"sina_code": "gb_spy", "name": "标普500ETF", "type": "etf", "data_type": "us_stock"},
    
    # 富时A50相关 (期货数据格式不同)
    "FTSE_A50": {"sina_code": "hf_CHA50CFD", "name": "富时中国A50期指", "type": "futures", "data_type": "futures"},
}


def fetch_sina_data(sina_code: str, data_type: str = "us_stock") -> Optional[Dict]:
    """
    从新浪财经获取数据
    
    Args:
        sina_code: 新浪财经代码
        data_type: 数据类型 (us_stock/futures)
        
    Returns:
        数据字典，失败返回 None
    """
    url = f"https://hq.sinajs.cn/list={sina_code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn",
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read().decode("gbk")
        
        start = data.find('"') + 1
        end = data.rfind('"')
        if start <= 0 or end <= start:
            return None
        
        content = data[start:end]
        if not content:
            return None
        
        fields = content.split(",")
        if len(fields) < 5:
            return None
        
        if data_type == "futures":
            # 期货数据格式 (如富时A50):
            # [0]: 最新价
            # [1]: (空)
            # [2]: 买入价
            # [3]: 卖出价
            # [4]: 最高价
            # [5]: 最低价
            # [6]: 时间
            # [7]: 昨收价
            # [8]: 开盘价
            # [9]: 持仓量
            # [10]: 买量
            # [11]: 卖量
            # [12]: 日期
            # [13]: 名称
            # [14]: 成交量
            price = float(fields[0]) if fields[0] else None
            previous_close = float(fields[7]) if len(fields) > 7 and fields[7] else None
            
            # 计算涨跌额和涨跌幅
            change = None
            change_pct = None
            if price is not None and previous_close is not None and previous_close > 0:
                change = price - previous_close
                change_pct = (change / previous_close) * 100
            
            return {
                "name": fields[13] if len(fields) > 13 else "",
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "time": f"{fields[12]} {fields[6]}" if len(fields) > 12 else fields[6] if len(fields) > 6 else "",
                "open": float(fields[8]) if len(fields) > 8 and fields[8] else None,
                "high": float(fields[4]) if len(fields) > 4 and fields[4] else None,
                "low": float(fields[5]) if len(fields) > 5 and fields[5] else None,
            }
        else:
            # 美股/ETF数据格式:
            # [0]: 名称
            # [1]: 最新价
            # [2]: 涨跌幅%
            # [3]: 日期时间
            # [4]: 涨跌额
            # [5]: 开盘价
            # [6]: 最高价
            # [7]: 最低价
            return {
                "name": fields[0],
                "price": float(fields[1]) if fields[1] else None,
                "change_pct": float(fields[2]) if len(fields) > 2 and fields[2] else None,
                "time": fields[3] if len(fields) > 3 else "",
                "change": float(fields[4]) if len(fields) > 4 and fields[4] else None,
                "open": float(fields[5]) if len(fields) > 5 and fields[5] else None,
                "high": float(fields[6]) if len(fields) > 6 and fields[6] else None,
                "low": float(fields[7]) if len(fields) > 7 and fields[7] else None,
            }
    except Exception as e:
        return None


def fetch_quote(symbol: str) -> Optional[Dict]:
    """
    获取指定市场数据 (alias for fetch_market_data, for backward compatibility)
    
    Args:
        symbol: 代码，如 IXIC, KWEB
        
    Returns:
        完整数据字典
    """
    return fetch_market_data(symbol)


def fetch_market_data(symbol: str) -> Optional[Dict]:
    """
    获取指定市场数据
    
    Args:
        symbol: 代码，如 IXIC, KWEB
        
    Returns:
        完整数据字典
    """
    if symbol not in MARKET_SYMBOLS:
        raise ValueError(f"不支持的代码: {symbol}。支持的代码: {', '.join(MARKET_SYMBOLS.keys())}")
    
    info = MARKET_SYMBOLS[symbol]
    data_type = info.get("data_type", "us_stock")
    data = fetch_sina_data(info["sina_code"], data_type)
    
    if not data:
        return None
    
    return {
        "symbol": symbol,
        "sina_code": info["sina_code"],
        "name": info["name"],
        "type": info["type"],
        **data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_multiple(symbols: List[str]) -> List[Dict]:
    """批量获取多个代码数据"""
    results = []
    for symbol in symbols:
        try:
            data = fetch_market_data(symbol)
            if data:
                results.append(data)
            else:
                results.append({
                    "symbol": symbol,
                    "name": MARKET_SYMBOLS.get(symbol, {}).get("name", symbol),
                    "error": "获取数据失败"
                })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "name": MARKET_SYMBOLS.get(symbol, {}).get("name", symbol),
                "error": str(e)
            })
    return results


def format_output(data: Dict, use_json: bool = False) -> str:
    """格式化输出"""
    if use_json:
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    if "error" in data:
        return f"{data['symbol']:10} 错误: {data['error']}"
    
    price = data.get('price')
    change = data.get('change', 0)
    change_pct = data.get('change_pct', 0)
    
    if price is None:
        return f"{data['name']:12} 数据获取失败"
    
    symbol = "▲" if change >= 0 else "▼"
    return f"{data['name']:15} {price:>12,.2f}  {symbol}{change:>+10,.2f}  ({change_pct:>+.2f}%)"


def get_default_watchlist() -> Dict[str, List[str]]:
    """获取默认关注列表"""
    return {
        "indices": ["IXIC", "SPX", "DJI"],
        "cn_etfs": ["KWEB", "PGJ"],
        "futures": ["FTSE_A50"],
    }


def analyze_market(results: List[Dict]) -> Dict:
    """分析市场整体情况"""
    analysis = {
        "us_market": "neutral",
        "cn_sentiment": "neutral",
        "summary": "",
    }
    
    # 美股分析
    indices_up = 0
    indices_down = 0
    
    # 中概股分析
    cn_etfs_up = 0
    cn_etfs_down = 0
    
    for item in results:
        if "error" in item:
            continue
        
        change = item.get("change", 0)
        item_type = item.get("type", "")
        
        if item_type == "index":
            if change > 0:
                indices_up += 1
            elif change < 0:
                indices_down += 1
        elif item_type == "cn_etf":
            if change > 0:
                cn_etfs_up += 1
            elif change < 0:
                cn_etfs_down += 1
    
    # 判断美股整体
    if indices_up > indices_down:
        analysis["us_market"] = "bullish"
    elif indices_down > indices_up:
        analysis["us_market"] = "bearish"
    
    # 判断中概股情绪
    if cn_etfs_up > cn_etfs_down:
        analysis["cn_sentiment"] = "bullish"
    elif cn_etfs_down > cn_etfs_up:
        analysis["cn_sentiment"] = "bearish"
    
    # 生成摘要
    if analysis["cn_sentiment"] == "bearish":
        analysis["summary"] = "中概股承压，可能影响A股情绪"
    elif analysis["cn_sentiment"] == "bullish":
        analysis["summary"] = "中概股表现良好，对A股有正面影响"
    else:
        analysis["summary"] = "中概股表现中性"
    
    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="美股外盘行情获取工具 - 国内可用、免费"
    )
    parser.add_argument(
        "symbols",
        nargs="*",
        help=f"代码，支持: {', '.join(MARKET_SYMBOLS.keys())}"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="获取默认关注列表(美股指数+中概股ETF)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="JSON格式输出"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有支持的代码"
    )
    parser.add_argument(
        "--analyze", "-a",
        action="store_true",
        help="分析市场整体情况"
    )
    
    args = parser.parse_args()
    
    # 列出支持的代码
    if args.list:
        print("支持的代码列表:")
        print("=" * 60)
        print("\n【美股指数】")
        for code, info in MARKET_SYMBOLS.items():
            if info["type"] == "index":
                print(f"  {code:8} - {info['name']}")
        
        print("\n【中概股ETF】")
        for code, info in MARKET_SYMBOLS.items():
            if info["type"] == "cn_etf":
                print(f"  {code:8} - {info['name']}")
        
        print("\n【其他ETF】")
        for code, info in MARKET_SYMBOLS.items():
            if info["type"] == "etf":
                print(f"  {code:8} - {info['name']}")
        
        print("\n【期指】")
        for code, info in MARKET_SYMBOLS.items():
            if info["type"] == "futures":
                print(f"  {code:8} - {info['name']}")
        print("=" * 60)
        return
    
    # 获取数据
    if args.watch:
        # 获取默认关注列表
        watchlist = get_default_watchlist()
        symbols = watchlist["indices"] + watchlist["cn_etfs"] + watchlist["futures"]
    elif args.symbols:
        symbols = args.symbols
    else:
        print("错误: 请指定代码，或使用 --watch 获取默认关注列表", file=sys.stderr)
        print(f"\n示例:", file=sys.stderr)
        print(f"  python fetch_us_market.py --watch", file=sys.stderr)
        print(f"  python fetch_us_market.py IXIC KWEB", file=sys.stderr)
        sys.exit(1)
    
    # 批量获取
    results = fetch_multiple(symbols)
    
    # 分析
    if args.analyze:
        analysis = analyze_market(results)
    
    # 输出
    if args.json:
        output = {
            "data": results,
            "count": len(results),
        }
        if args.analyze:
            output["analysis"] = analysis
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 分组输出
        indices = [r for r in results if r.get("type") == "index"]
        cn_etfs = [r for r in results if r.get("type") == "cn_etf"]
        futures = [r for r in results if r.get("type") == "futures"]
        others = [r for r in results if r.get("type") not in ["index", "cn_etf", "futures"]]
        
        print("=" * 75)
        print("📊 美股外盘行情")
        print("=" * 75)
        
        if indices:
            print("\n【美股指数】")
            print(f"{'名称':15} {'最新价':>12} {'涨跌额':>12} {'涨跌幅':>10}")
            print("-" * 75)
            for item in indices:
                print(format_output(item))
        
        if cn_etfs:
            print("\n【中概股ETF】")
            print(f"{'名称':15} {'最新价':>12} {'涨跌额':>12} {'涨跌幅':>10}")
            print("-" * 75)
            for item in cn_etfs:
                print(format_output(item))
        
        if futures:
            print("\n【期指】")
            print(f"{'名称':15} {'最新价':>12} {'涨跌额':>12} {'涨跌幅':>10}")
            print("-" * 75)
            for item in futures:
                print(format_output(item))
        
        if others:
            print("\n【其他】")
            print(f"{'名称':15} {'最新价':>12} {'涨跌额':>12} {'涨跌幅':>10}")
            print("-" * 75)
            for item in others:
                print(format_output(item))
        
        print("=" * 75)
        
        # 分析摘要
        if args.analyze:
            print(f"\n💡 分析: {analysis['summary']}")
            print(f"   美股整体: {analysis['us_market']}")
            print(f"   中概情绪: {analysis['cn_sentiment']}")


if __name__ == "__main__":
    main()
