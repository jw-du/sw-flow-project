---
name: sina-forex
description: "新浪财经外汇行情获取工具。国内可用、完全免费，支持美元/人民币等主流货币对实时行情查询。Use when: (1) 查询外汇实时汇率, (2) 监控美元人民币汇率, (3) 获取在岸/离岸人民币行情, (4) 查看主要货币对走势"
skill_type: execution
inputs:
  symbol:
    type: string
    description: 货币对代码，如 USDCNH
    required: true
outputs:
  description: 外汇行情结构化数据
  fields:
    - symbol
    - price
    - change_pct
dependency:
  python:
    - urllib3
---

# 新浪财经外汇行情工具

国内可用、完全免费的实时外汇行情查询工具，支持美元/人民币（USDCNY/USDCNH）等主流货币对。

## 特点

- ✅ **国内直接访问** - 无需翻墙，境内网络即可使用
- ✅ **完全免费** - 新浪财经公开接口，无使用限制
- ✅ **实时更新** - 与银行外汇市场同步
- ✅ **支持人民币** - 特别强调 USD/CNY 和 USD/CNH 行情

## 支持的货币对

### 人民币相关（重点）
| 代码 | 名称 | 说明 |
|------|------|------|
| **USDCNY** | 美元/在岸人民币 | 美元兑境内人民币 |
| **USDCNH** | 美元/离岸人民币 | 美元兑香港离岸人民币 |
| **EURCNY** | 欧元/人民币 | 欧元兑人民币 |
| **GBPCNY** | 英镑/人民币 | 英镑兑人民币 |
| **JPYCNY** | 日元/人民币 | 100日元兑人民币 |
| **HKDCNY** | 港币/人民币 | 港币兑人民币 |

### 主要国际货币对
| 代码 | 名称 | 说明 |
|------|------|------|
| EURUSD | 欧元/美元 | 欧元兑美元 |
| GBPUSD | 英镑/美元 | 英镑兑美元 |
| USDJPY | 美元/日元 | 美元兑日元 |
| USDCHF | 美元/瑞郎 | 美元兑瑞士法郎 |
| AUDUSD | 澳元/美元 | 澳元兑美元 |
| USDCAD | 美元/加元 | 美元兑加元 |
| NZDUSD | 纽元/美元 | 纽元兑美元 |

### 贵金属
| 代码 | 名称 | 说明 |
|------|------|------|
| XAUUSD | 黄金/美元 | 现货黄金 |
| XAGUSD | 白银/美元 | 现货白银 |

## 快速开始

### 查询美元人民币汇率

```bash
python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNY
```

**输出示例：**
```
==================================================
货币对: 美元/人民币 (USDCNY)
==================================================
最新价: 7.2023
买入价: 7.2001  卖出价: 7.2045
最高价: 7.2150  最低价: 7.1950
开盘价: 7.1980  昨收价: 7.1950
涨跌额: ▲0.0073
涨跌幅: +0.10%
报价时间: 2026-03-03 15:30:00
==================================================
```

### 查询多个货币对

```bash
python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNY USDCNH EURUSD
```

### JSON格式输出

```bash
python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNY --json
```

**JSON输出示例：**
```json
{
  "pair": "USDCNY",
  "name": "美元/人民币",
  "desc": "美元兑在岸人民币",
  "sina_code": "fx_susdcny",
  "bid": 7.2001,
  "price": 7.2023,
  "ask": 7.2045,
  "high": 7.2150,
  "low": 7.1950,
  "open": 7.1980,
  "previous_close": 7.1950,
  "change": 0.0073,
  "change_pct": 0.10,
  "quote_time": "2026-03-03 15:30:00",
  "timestamp": "2026-03-03 15:32:15"
}
```

### 列出所有支持的货币对

```bash
python .agents/skills/sina-forex/scripts/fetch_forex.py --list
```

## 使用场景

### 场景1：监控美元人民币汇率

```bash
# 对比在岸 vs 离岸人民币
python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNY USDCNH
```

### 场景2：获取主要货币对行情

```bash
# 美元指数相关
python .agents/skills/sina-forex/scripts/fetch_forex.py EURUSD GBPUSD USDJPY
```

### 场景3：贵金属价格

```bash
# 黄金、白银
python .agents/skills/sina-forex/scripts/fetch_forex.py XAUUSD XAGUSD
```

## 数据来源

- **接口提供商**：新浪财经 (sina.com.cn)
- **接口地址**：`https://hq.sinajs.cn/list={code}`
- **更新频率**：实时（与银行间外汇市场同步）
- **数据精度**：小数点后4位

## 数据字段说明

| 字段 | 说明 |
|------|------|
| `pair` | 货币对代码 |
| `name` | 货币对名称 |
| `price` | 最新汇率 |
| `bid` | 买入价 (银行买入) |
| `ask` | 卖出价 (银行卖出) |
| `high` | 当日最高价 |
| `low` | 当日最低价 |
| `open` | 当日开盘价 |
| `previous_close` | 昨日收盘价 |
| `change` | 涨跌额 |
| `change_pct` | 涨跌幅 (%) |
| `quote_time` | 数据报价时间 |
| `timestamp` | 获取时间戳 |

## 注意事项

1. **买卖价差**：`ask` 是银行卖出价（客户买入价），`bid` 是银行买入价（客户卖出价），买卖价差是银行利润
2. **在岸 vs 离岸**：USDCNY 是在岸人民币（境内），USDCNH 是离岸人民币（香港），两者可能有微小价差
3. **交易时间**：外汇市场 24小时交易，但数据更新在周末可能延迟
4. **数据延迟**：通常为实时或几秒钟延迟

## 故障排查

### 无法获取数据

```bash
# 检查网络连接
ping finance.sina.com.cn

# 确认货币对代码正确
python .agents/skills/sina-forex/scripts/fetch_forex.py --list
```

### 返回空数据

可能是新浪财经服务器临时问题，请稍后再试。

### 编码问题（Windows）

如果在 Windows PowerShell 中看到乱码，请设置：
```powershell
$env:PYTHONIOENCODING="utf-8"
python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNY
```

## 与其他 Skill 对比

| 特性 | sina-forex | yahoo-finance-forex |
|------|------------|---------------------|
| 国内访问 | ✅ 直接访问 | ⚠️ 可能需要翻墙 |
| 免费 | ✅ 是 | ✅ 是 |
| USD/CNY 支持 | ✅ 支持 | ❌ 不支持 |
| USD/CNH 支持 | ✅ 支持 | ❌ 不支持 |
| 新闻数据 | ❌ 无 | ✅ 有 |
| 情感分析 | ❌ 无 | ✅ 有 |

**选择建议：**
- 需要人民币行情 → 使用 `sina-forex`
- 需要外汇新闻分析 → 使用 `yahoo-finance-forex`（如果能访问）

## 示例脚本

### 定时监控美元汇率

```bash
#!/bin/bash
# 每小时记录一次美元汇率
while true; do
    python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNY --json >> usdcny_log.json
    sleep 3600
done
```

### Python 调用示例

```python
import subprocess
import json

result = subprocess.run(
    ['python', '.agents/skills/sina-forex/scripts/fetch_forex.py', 'USDCNY', '--json'],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
print(f"当前汇率: {data['price']}")
```

## 更新日志

- **v1.0.0** - 初始版本，支持17个主要货币对，特别强调 USD/CNY 和 USD/CNH
