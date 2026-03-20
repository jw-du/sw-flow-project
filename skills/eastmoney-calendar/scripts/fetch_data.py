import requests
import json
import argparse
import sys
import math


def fetch_eastmoney_calendar(start_date, end_date, event_type="", page_index=1, page_size=100):
    """
    Fetch economic calendar data from Eastmoney H5 interface.
    """
    url = "https://emdatah5.eastmoney.com/dc/CJRL/GetIndexData"

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7",
        "dnt": "1",
        "priority": "u=1, i",
        "referer": "https://emdatah5.eastmoney.com/dc/cjrl/index",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    cookies = {
        "qgqp_b_id": "879c4f66c6ca22b232555391bfdc53fc",
        "st_nvi": "k9wzs68SMYUqkFqdNvkJN0549",
        "nid18": "0960422f276dd5936ecd7ee29674407d",
        "nid18_create_time": "1765351044932",
        "gviem": "csuggzz12bs7A-3dyN6kab82a",
        "gviem_create_time": "1765351044933",
        "st_si": "66414181469454",
        "st_asi": "delete",
        "fullscreengg": "1",
        "fullscreengg2": "1",
        "has_jump_to_web": "1",
        "st_pvi": "68652862989888",
        "st_sp": "2025-11-25%2016%3A06%3A57",
        "st_inirUrl": "https%3A%2F%2Fcn.bing.com%2F",
        "st_sn": "17",
        "st_psi": "20260227161957660-113300304203-2001243538"
    }

    params = {
        "startDate": start_date,
        "endDate": end_date,
        "type": event_type,
        "pIndex": page_index,
        "pSize": page_size
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}


def fetch_calendar_data(start_date, end_date, event_type="", page_size=100):
    """
    Fetch economic calendar data for the given range (wrapper for fetch_all_eastmoney_calendar).
    This function provides a simple interface for external imports.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        event_type: Event type filter (optional)
        page_size: Items per page (default: 100)
        
    Returns:
        Dictionary with TotalCount and Data keys
    """
    return fetch_all_eastmoney_calendar(start_date, end_date, event_type, page_size)


def fetch_all_eastmoney_calendar(start_date, end_date, event_type="", page_size=100):
    """
    Fetch ALL economic calendar data for the given range by handling pagination automatically.
    """
    all_data = []
    page_index = 1
    total_count = 0

    # First request to get total count and first batch
    first_batch = fetch_eastmoney_calendar(start_date, end_date, event_type, page_index, page_size)

    if "error" in first_batch:
        return first_batch

    # Check if first_batch is a dictionary; if it's a list, handle accordingly
    if not isinstance(first_batch, dict):
        if isinstance(first_batch, list):
            return {"TotalCount": len(first_batch), "Data": first_batch}
        return {"error": "Unexpected response format", "details": str(first_batch)}

    total_count = int(first_batch.get("TotalCount", 0))
    current_data = first_batch.get("Data", [])

    if not current_data:
        return {"TotalCount": 0, "Data": []}

    all_data.extend(current_data)

    # Calculate total pages needed
    total_pages = math.ceil(total_count / page_size)

    # Fetch remaining pages
    for p in range(2, total_pages + 1):
        batch = fetch_eastmoney_calendar(start_date, end_date, event_type, p, page_size)
        if "Data" in batch and isinstance(batch, dict):
            all_data.extend(batch["Data"])

    return {
        "TotalCount": total_count,
        "Data": all_data
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch Eastmoney Economic Calendar Data")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--type", default="", help="Event type filter")
    parser.add_argument("--size", type=int, default=100, help="Items per page (default: 100)")
    parser.add_argument("--output", "-o", default="", help="Output file path (optional, e.g., result.json)")

    args = parser.parse_args()

    data = fetch_all_eastmoney_calendar(args.start_date, args.end_date, args.type, args.size)

    # Output to file if specified, otherwise print to stdout
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"数据已保存到: {args.output}")
        print(f"共获取 {data.get('TotalCount', 0)} 条记录")
    else:
        # Print JSON output to stdout for integration with other tools
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
