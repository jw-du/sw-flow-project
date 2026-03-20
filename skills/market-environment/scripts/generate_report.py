#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场环境分析报告生成器
整合日历效应、外盘风向、国内情绪三个维度，生成决策矩阵和策略建议

Usage:
    python generate_report.py
    python generate_report.py --output ./my_report.md
"""

import argparse
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

# 确保依赖已安装
try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("[INFO] 正在安装依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "fuzzywuzzy", "python-Levenshtein"])


def get_timestamp_filename(prefix: str, suffix: str = '.md') -> str:
    """生成带时间戳的文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}{suffix}"


def get_default_output_path() -> Path:
    """获取默认输出路径"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    output_dir = project_root / 'data' / 'market-environment'
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = get_timestamp_filename('market_environment_report', '.md')
    return output_dir / filename


def get_calendar_data() -> dict:
    """获取日历数据"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'eastmoney-calendar' / 'scripts'))
        from fetch_data import fetch_calendar_data
        
        today = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + pd.Timedelta(days=7)).strftime('%Y-%m-%d')
        result = fetch_calendar_data(today, end_date)
        
        events = []
        # Handle nested structure: Data[0]['Data'] contains the actual events
        if result and 'Data' in result and len(result['Data']) > 0:
            # The actual event data is nested inside the first Data item
            nested_data = result['Data'][0]
            if isinstance(nested_data, dict) and 'Data' in nested_data:
                actual_data = nested_data['Data']
            else:
                actual_data = result['Data']
            
            # Process all events to calculate risk level
            for item in actual_data:
                if isinstance(item, dict):
                    events.append({
                        'date': item.get('STARTDATE', '').split(' ')[0] if item.get('STARTDATE') else '',
                        'name': item.get('FINNAME', ''),
                        'type': item.get('TYPENAME', '')
                    })
        
        # Calculate risk level based on all events
        risk_level = assess_calendar_risk(events)
        
        # Sort events by risk level (high risk first) and return top 15 for display
        high_risk_keywords = ['美联储', '议息', 'FOMC', '地缘政治', '战争', '冲突', '央行', '利率决议']
        mid_risk_keywords = ['两会', '政治局', '假期', '长假']
        
        def get_event_priority(event):
            name = event.get('name', '') + event.get('type', '')
            for kw in high_risk_keywords:
                if kw in name:
                    return 0  # High priority
            for kw in mid_risk_keywords:
                if kw in name:
                    return 1  # Medium priority
            return 2  # Low priority
        
        sorted_events = sorted(events, key=get_event_priority)
        return {'events': sorted_events[:15], 'risk_level': risk_level}
    except Exception as e:
        print(f"[WARN] 获取日历数据失败: {e}")
        return {'events': [], 'risk_level': 0.5}


def assess_calendar_risk(events: list) -> float:
    """评估日历风险系数"""
    risk_keywords = {
        '高风险': ['美联储', '议息', 'FOMC', '地缘政治', '战争', '冲突'],
        '中风险': ['两会', '政治局会议', '假期', '长假'],
        '低风险': ['数据公布', '会议', '论坛']
    }
    
    high_risk_count = 0
    mid_risk_count = 0
    
    for event in events:
        name = event.get('name', '')
        for keyword in risk_keywords['高风险']:
            if keyword in name:
                high_risk_count += 1
        for keyword in risk_keywords['中风险']:
            if keyword in name:
                mid_risk_count += 1
    
    if high_risk_count > 0:
        return 0.8
    elif mid_risk_count > 0:
        return 0.6
    return 0.3


def get_us_market_data() -> dict:
    """获取美股数据"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'us-market-watch' / 'scripts'))
        from fetch_us_market import fetch_quote
        
        indices = ['IXIC', 'SPX', 'DJI', 'KWEB', 'FTSE_A50']
        data = {}
        
        for idx in indices:
            try:
                quote = fetch_quote(idx)
                if quote:
                    data[idx] = {
                        'name': quote.get('name', idx),
                        'price': quote.get('price', 0),
                        'change_pct': quote.get('change_pct', 0)
                    }
            except:
                pass
        
        return calculate_us_market_score(data)
    except Exception as e:
        print(f"[WARN] 获取美股数据失败: {e}")
        return {'score': 0.5, 'data': {}, 'status': 'unknown'}


def calculate_us_market_score(data: dict) -> dict:
    """计算外盘得分"""
    if not data:
        return {'score': 0.5, 'data': {}, 'status': 'unknown'}
    
    # 纳斯达克权重最高
    nasdaq_change = data.get('IXIC', {}).get('change_pct', 0)
    kweb_change = data.get('KWEB', {}).get('change_pct', 0)
    a50_change = data.get('FTSE_A50', {}).get('change_pct', 0)
    
    # 评分逻辑
    if nasdaq_change > 2 or kweb_change > 3:
        score = 1.0
        status = '大涨'
    elif nasdaq_change > 0.5 or kweb_change > 1:
        score = 0.7
        status = '上涨'
    elif nasdaq_change < -2 or kweb_change < -3:
        score = 0.0
        status = '大跌'
    elif nasdaq_change < -0.5 or kweb_change < -1:
        score = 0.3
        status = '下跌'
    else:
        score = 0.5
        status = '震荡'
    
    return {'score': score, 'data': data, 'status': status}


def get_forex_data() -> dict:
    """获取汇率数据"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'sina-forex' / 'scripts'))
        from fetch_forex import fetch_forex_data
        
        data = fetch_forex_data('USDCNH')
        if data:
            change_pct = data.get('change_pct', 0)
            price = data.get('price', 0)
            
            # 人民币升值为利好
            if change_pct < -0.5:
                sentiment = '利好'
            elif change_pct > 0.5:
                sentiment = '利空'
            else:
                sentiment = '中性'
            
            return {
                'price': price,
                'change_pct': change_pct,
                'sentiment': sentiment
            }
    except Exception as e:
        print(f"[WARN] 获取汇率数据失败: {e}")
    
    return {'price': 7.0, 'change_pct': 0, 'sentiment': '中性'}


def get_policy_news() -> dict:
    """获取政策新闻情绪"""
    # 简化处理，实际应该调用 news-policy-fetcher
    return {
        'score': 0.5,
        'events': [],
        'sentiment': '中性'
    }


def calculate_domestic_sentiment() -> dict:
    """计算国内情绪得分"""
    policy = get_policy_news()
    
    score = policy['score']
    
    if score >= 0.8:
        level = '重磅利好'
    elif score >= 0.5:
        level = '普通利好'
    elif score >= 0.3:
        level = '中性'
    else:
        level = '利空'
    
    return {
        'score': score,
        'level': level,
        'policy': policy
    }


def calculate_total_score(calendar: dict, us_market: dict, domestic: dict) -> dict:
    """计算总分和策略建议"""
    # 基础分 = 外盘 + 国内情绪
    base_score = us_market['score'] + domestic['score']
    
    # 日历效应调整
    risk_coefficient = calendar.get('risk_level', 0.5)
    if risk_coefficient > 0.6:
        adjusted_score = base_score - 0.5
    elif risk_coefficient > 0.4:
        adjusted_score = base_score - 0.3
    else:
        adjusted_score = base_score
    
    # 确保在0-2范围内
    adjusted_score = max(0, min(2, adjusted_score))
    
    # 策略档位
    if adjusted_score >= 1.5:
        strategy = '进攻'
        position = '70-90%'
    elif adjusted_score >= 1.0:
        strategy = '均衡'
        position = '50-70%'
    elif adjusted_score >= 0.5:
        strategy = '结构性'
        position = '30-50%'
    else:
        strategy = '防守'
        position = '0-30%'
    
    # 日历风险限制
    if risk_coefficient > 0.6:
        position = f"{position.split('-')[0]}-{min(int(position.split('-')[1].rstrip('%')), 50)}%"
    
    return {
        'base_score': base_score,
        'adjusted_score': adjusted_score,
        'risk_coefficient': risk_coefficient,
        'strategy': strategy,
        'position': position
    }


def generate_markdown_report(calendar: dict, us_market: dict, forex: dict, 
                            domestic: dict, total: dict) -> str:
    """生成Markdown格式报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# 市场环境分析报告
## 生成时间：{now}

---

## 一、宏观天气预报矩阵

| 维度 | 关键指标 | 表现状态 | 得分 (0-1) | 判读逻辑 |
| :--- | :--- | :--- | :--- | :--- |
| **日历效应** | 风险系数 | {'高' if total['risk_coefficient'] > 0.6 else '中' if total['risk_coefficient'] > 0.4 else '低'}风险 | N/A | 风险系数: {total['risk_coefficient']:.1f} |
| **外盘风向** | 美股/中概股/A50 | {us_market['status']} | {us_market['score']:.1f} | {'外盘强劲' if us_market['score'] >= 0.7 else '外盘疲软' if us_market['score'] <= 0.3 else '外盘震荡'} |
| **国内情绪** | 政策面 | {domestic['level']} | {domestic['score']:.1f} | {domestic['level']} |
| **综合结论** | **总分: {total['adjusted_score']:.1f}/2.0** | **{total['strategy']}** | - | **{total['strategy']}型策略** |

---

## 二、详细数据分析

### 2.1 日历效应（风险系数: {total['risk_coefficient']:.1f}）

**近期重要事件：**

"""
    
    # 添加日历事件
    if calendar['events']:
        for event in calendar['events'][:5]:
            report += f"- **{event['date']}** | {event['type'] or '事件'}: {event['name']}\n"
    else:
        report += "- 近期无重大事件\n"
    
    report += f"""
**风险评估：**
- 风险系数 {total['risk_coefficient']:.1f} ({'高' if total['risk_coefficient'] > 0.6 else '中' if total['risk_coefficient'] > 0.4 else '低'}风险)
- {'市场观望情绪浓厚，建议控制仓位' if total['risk_coefficient'] > 0.6 else '市场波动可能加大，注意风险' if total['risk_coefficient'] > 0.4 else '市场环境平稳，可正常交易'}

---

### 2.2 外盘风向（得分: {us_market['score']:.1f}）

"""
    
    # 添加外盘数据
    if us_market['data']:
        report += "| 指数/ETF | 涨跌幅 | 状态 |\n"
        report += "|----------|--------|------|\n"
        
        for code, data in us_market['data'].items():
            change = data.get('change_pct', 0)
            status = '▲ 上涨' if change > 0 else '▼ 下跌' if change < 0 else '→ 平盘'
            report += f"| {data.get('name', code)} | {change:+.2f}% | {status} |\n"
    else:
        report += "*外盘数据获取失败*\n"
    
    # 汇率
    report += f"""
**汇率情况：**
- 离岸人民币 (USD/CNH): {forex['price']:.4f} ({forex['change_pct']:+.2f}%)
- 解读: {forex['sentiment']} ({'人民币升值，利好A股' if forex['sentiment'] == '利好' else '人民币贬值，利空A股' if forex['sentiment'] == '利空' else '汇率稳定'})

---

### 2.3 国内情绪（得分: {domestic['score']:.1f}）

- **情绪等级**: {domestic['level']}
- **政策面**: {domestic['policy']['sentiment']}

---

## 三、决策逻辑框架

### 综合得分: {total['adjusted_score']:.1f}/2.0

### 策略建议: **{total['strategy']}**

**仓位参考**: {total['position']}

### 特殊情况处理
"""
    
    # 日历效应处理
    if total['risk_coefficient'] > 0.6:
        report += "- **日历效应**: 高风险期，仓位上限降至50%，以避险为主\n"
    elif total['risk_coefficient'] > 0.4:
        report += "- **日历效应**: 中风险期，适当控制仓位\n"
    else:
        report += "- **日历效应**: 低风险，正常交易\n"
    
    # 外盘影响
    if us_market['score'] >= 0.7:
        report += "- **外盘影响**: 外盘大涨，对A股开盘形成正面引导\n"
    elif us_market['score'] <= 0.3:
        report += "- **外盘影响**: 外盘大跌，A股可能低开，注意风险\n"
    else:
        report += "- **外盘影响**: 外盘震荡，对A股影响有限\n"
    
    # 国内情绪
    report += f"- **国内情绪**: {domestic['level']}，{'可关注政策受益板块' if domestic['score'] >= 0.5 else '需等待政策明朗'}\n"
    
    report += """
### 风险控制
- 单一板块不超过 25-30%
- 止损线设置在 -6% ~ -8%
- 总仓位不超过建议仓位上限

---

## 四、操作建议

"""
    
    if total['strategy'] == '进攻':
        report += """
1. **仓位控制**: 积极进攻仓位（70-90%）
2. **配置方向**: 成长型板块为主，把握主线机会
3. **操作节奏**: 逢低加仓，持仓待涨
"""
    elif total['strategy'] == '均衡':
        report += """
1. **仓位控制**: 均衡仓位（50-70%）
2. **配置方向**: 蓝筹+成长均衡配置
3. **操作节奏**: 高抛低吸，动态调整
"""
    elif total['strategy'] == '结构性':
        report += """
1. **仓位控制**: 控制仓位（30-50%）
2. **配置方向**: 精选板块，防守型ETF+行业驱动ETF
3. **操作节奏**: 严格止损，快进快出
"""
    else:
        report += """
1. **仓位控制**: 防守仓位（0-30%），保留现金
2. **配置方向**: 现金、货币基金、债券ETF为主
3. **操作节奏**: 空仓观望，等待机会
"""
    
    report += f"""
---

*报告由 market-environment skill 自动生成*
*数据时间: {datetime.now().strftime('%Y-%m-%d')}*
"""
    
    return report


def save_report(report: str, output_path: Path):
    """保存报告到文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[OK] 报告已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="市场环境分析报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 生成报告，自动保存到 data/market-environment/market_environment_report_YYYYMMDD_HHMMSS.md
  python generate_report.py

  # 指定输出路径
  python generate_report.py --output ./my_report.md
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        help='输出Markdown文件路径 (默认: data/market-environment/market_environment_report_YYYYMMDD_HHMMSS.md)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("                    市场环境分析报告生成器")
    print("=" * 80)
    
    # 收集数据
    print("\n[1/4] 获取日历数据...")
    calendar = get_calendar_data()
    
    print("[2/4] 获取外盘数据...")
    us_market = get_us_market_data()
    
    print("[3/4] 获取汇率数据...")
    forex = get_forex_data()
    
    print("[4/4] 评估国内情绪...")
    domestic = calculate_domestic_sentiment()
    
    # 计算总分 - 修复：只传3个参数
    print("\n[计算] 生成决策矩阵...")
    total = calculate_total_score(calendar, us_market, domestic)
    
    # 生成报告
    report = generate_markdown_report(calendar, us_market, forex, domestic, total)
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_default_output_path()
    
    # 保存报告
    save_report(report, output_path)
    
    # 打印摘要
    print("\n" + "=" * 80)
    print("                    报告摘要")
    print("=" * 80)
    print(f"\n日历风险系数: {total['risk_coefficient']:.1f}")
    print(f"外盘得分: {us_market['score']:.1f}")
    print(f"国内情绪: {domestic['score']:.1f} ({domestic['level']})")
    print(f"\n综合得分: {total['adjusted_score']:.1f}/2.0")
    print(f"策略建议: {total['strategy']} ({total['position']})")
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
