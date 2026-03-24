#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

MARKET_SYMBOLS = {
    "IXIC": {"sina_code": "gb_ixic", "name": "纳斯达克指数", "type": "index", "data_type": "us_stock"},
    "SPX": {"sina_code": "gb_inx", "name": "标普500", "type": "index", "data_type": "us_stock"},
    "DJI": {"sina_code": "gb_dji", "name": "道琼斯", "type": "index", "data_type": "us_stock"},
    "KWEB": {"sina_code": "gb_kweb", "name": "中概互联网ETF", "type": "cn_etf", "data_type": "us_stock"},
    "PGJ": {"sina_code": "gb_pgj", "name": "中国龙ETF", "type": "cn_etf", "data_type": "us_stock"},
    "ASHR": {"sina_code": "gb_ashr", "name": "沪深300ETF", "type": "cn_etf", "data_type": "us_stock"},
    "QQQ": {"sina_code": "gb_qqq", "name": "纳斯达克100ETF", "type": "etf", "data_type": "us_stock"},
    "SPY": {"sina_code": "gb_spy", "name": "标普500ETF", "type": "etf", "data_type": "us_stock"},
    "FTSE_A50": {"sina_code": "hf_CHA50CFD", "name": "富时中国A50期指", "type": "futures", "data_type": "futures"},
}


def fetch_sina_data(sina_code: str, data_type: str = "us_stock") -> Optional[Dict]:
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
            price = float(fields[0]) if fields[0] else None
            previous_close = float(fields[7]) if len(fields) > 7 and fields[7] else None
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
    except Exception:
        return None


def fetch_market_data(symbol: str) -> Optional[Dict]:
    if symbol not in MARKET_SYMBOLS:
        raise ValueError(f"不支持的代码: {symbol}")
    info = MARKET_SYMBOLS[symbol]
    data = fetch_sina_data(info["sina_code"], info.get("data_type", "us_stock"))
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
    results = []
    for symbol in symbols:
        try:
            data = fetch_market_data(symbol)
            if data:
                results.append(data)
            else:
                results.append({"symbol": symbol, "name": MARKET_SYMBOLS.get(symbol, {}).get("name", symbol), "error": "获取数据失败"})
        except Exception as e:
            results.append({"symbol": symbol, "name": MARKET_SYMBOLS.get(symbol, {}).get("name", symbol), "error": str(e)})
    return results


def get_default_watchlist() -> List[str]:
    return ["IXIC", "SPX", "DJI", "KWEB", "PGJ", "FTSE_A50"]


def analyze_market(results: List[Dict]) -> Dict:
    indices_up = 0
    indices_down = 0
    cn_etfs_up = 0
    cn_etfs_down = 0
    for item in results:
        if "error" in item:
            continue
        change = item.get("change", 0) or 0
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
    us_market = "neutral"
    cn_sentiment = "neutral"
    if indices_up > indices_down:
        us_market = "bullish"
    elif indices_down > indices_up:
        us_market = "bearish"
    if cn_etfs_up > cn_etfs_down:
        cn_sentiment = "bullish"
    elif cn_etfs_down > cn_etfs_up:
        cn_sentiment = "bearish"
    summary = "中概股表现中性"
    if cn_sentiment == "bearish":
        summary = "中概股承压，可能影响A股情绪"
    elif cn_sentiment == "bullish":
        summary = "中概股表现良好，对A股有正面影响"
    return {"us_market": us_market, "cn_sentiment": cn_sentiment, "summary": summary}


def main():
    parser = argparse.ArgumentParser(description="美股外盘行情获取工具")
    parser.add_argument("symbols", nargs="*", help=f"代码，支持: {', '.join(MARKET_SYMBOLS.keys())}")
    parser.add_argument("--watch", "-w", action="store_true", help="获取默认关注列表")
    parser.add_argument("--json", "-j", action="store_true", help="JSON格式输出")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有支持的代码")
    parser.add_argument("--analyze", "-a", action="store_true", help="分析市场整体情况")
    args = parser.parse_args()

    if args.list:
        print("支持的代码列表:")
        for code, info in MARKET_SYMBOLS.items():
            print(f"{code:10} - {info['name']}")
        return

    if args.watch:
        symbols = get_default_watchlist()
    elif args.symbols:
        symbols = args.symbols
    else:
        symbols = get_default_watchlist()

    quotes = fetch_multiple(symbols)
    analysis = analyze_market(quotes)
    summary = analysis.get("summary", "")

    if args.json:
        print(json.dumps({"quotes": quotes, "summary": summary, "analysis": analysis}, ensure_ascii=False, indent=2))
        return

    for item in quotes:
        if "error" in item:
            print(f"{item.get('symbol')}: {item.get('error')}")
        else:
            print(f"{item.get('name')} {item.get('price')} {item.get('change_pct')}")
    if args.analyze:
        print(summary)


if __name__ == "__main__":
    main()
