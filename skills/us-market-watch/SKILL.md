---
name: us-market-watch
description: 美股外盘行情获取工具。获取美股三大指数（纳斯达克、标普500、道琼斯）、中概股ETF（KWEB/PGJ）、富时A50期指实时行情。国内可用、免费。Use when: (1) 查看美股收盘行情, (2) 监控中概股表现, (3) 分析外盘对A股影响
dependency:
  python:
    - urllib3
---

# 美股外盘行情监控工具

国内可用、完全免费的美股外盘行情获取工具，支持美股指数、中概股ETF、期指实时行情。

## 特点

- ✅ **国内直接访问** - 新浪财经接口，无需翻墙
- ✅ **完全免费** - 无 API Key，无使用限制
- ✅ **中概股支持** - 专门支持 KWEB、PGJ 等中概股ETF
- ✅ **A股关联** - 富时A50期指，预判A股开盘

## 支持的行情类型

### 美股三大指数
| 代码 | 名称 | 说明 |
|------|------|------|
| IXIC | 纳斯达克指数 | 科技股风向标 |
| SPX | 标普500 | 美股大盘基准 |
| DJI | 道琼斯 | 蓝筹股指数 |

### 中概股ETF
| 代码 | 名称 | 说明 |
|------|------|------|
| KWEB | 中概互联网ETF | 阿里、腾讯等中概互联股 |
| PGJ | 中国龙ETF | 中国概念股组合 |
| ASHR | 沪深300ETF | A股大盘指数ETF |

### 期指
| 代码 | 名称 | 说明 |
|------|------|------|
| FTSE_A50 | 富时中国A50期指 | 预判A股开盘涨跌 |

### 其他ETF
| 代码 | 名称 | 说明 |
|------|------|------|
| QQQ | 纳斯达克100ETF | 大型科技股 |
| SPY | 标普500ETF | 标普500指数基金 |

## 快速开始

### 获取默认关注列表（推荐）

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --watch
```

**输出示例：**
```
===========================================================================
📊 美股外盘行情
===========================================================================

【美股指数】
名称                    最新价          涨跌额        涨跌幅
---------------------------------------------------------------------------
纳斯达克指数        22,748.86  ▲    +80.65  (+0.36%)
标普500             5,860.50  ▼    -15.20  (-0.26%)
道琼斯             48,904.78  ▼    -73.14  (-0.15%)

【中概股ETF】
名称                    最新价          涨跌额        涨跌幅
---------------------------------------------------------------------------
中概互联网ETF         30.65  ▼     -0.41  (-1.32%)
中国龙ETF             27.51  ▼     -0.35  (-1.25%)

【期指】
名称                    最新价          涨跌额        涨跌幅
---------------------------------------------------------------------------
富时中国A50期指      13,250.00  ▲    +50.00  (+0.38%)
===========================================================================
```

### 查询特定指数

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py IXIC KWEB
```

### JSON格式输出

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --watch --json
```

### 带分析摘要

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --watch --analyze
```

**输出示例：**
```
💡 分析: 中概股承压，可能影响A股情绪
   美股整体: bearish
   中概情绪: bearish
```

### 列出所有支持的代码

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --list
```

## 使用场景

### 场景1：每日开盘前查看外盘

```bash
# 查看昨日美股收盘和中概股表现
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --watch --analyze
```

**分析要点：**
- 美股涨跌 → 影响全球市场情绪
- 中概股ETF → 反映外资对中资股态度
- 富时A50 → 预判A股开盘方向

### 场景2：对比中概股与美股大盘

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py IXIC KWEB PGJ
```

如果中概股跌幅 > 美股大盘跌幅 → 中概股承压

### 场景3：监控A50期指

```bash
python .agents/skills/us-market-watch/scripts/fetch_us_market.py FTSE_A50
```

A50期指常提前反映A股开盘走势

## 数据字段说明

| 字段 | 说明 |
|------|------|
| `name` | 指数/ETF名称 |
| `price` | 最新价 |
| `change` | 涨跌额 |
| `change_pct` | 涨跌幅 (%) |
| `open` | 开盘价 |
| `high` | 最高价 |
| `low` | 最低价 |
| `time` | 数据时间 |
| `type` | 类型 (index/cn_etf/etf/futures) |

## 分析逻辑

### 中概股与A股关联

```
中概股ETF表现 → 外资对中资股态度 → A股情绪

KWEB/PGJ 大涨 → 中概股受追捧 → A股可能高开
KWEB/PGJ 大跌 → 中概股承压 → A股可能低开
```

### 美股与A股关联

```
美股大涨 → 全球风险偏好上升 → A股正面影响
美股大跌 → 全球避险情绪上升 → A股负面影响
```

### 富时A50与A股关联

```
A50期指涨幅 ≈ A股开盘涨幅

A50 +1% → A股可能高开 +1%
A50 -1% → A股可能低开 -1%
```

## 故障排查

### Windows 乱码

```powershell
$env:PYTHONIOENCODING="utf-8"
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --watch
```

### 数据获取失败

- 检查网络连接
- 新浪财经服务器可能临时维护，稍后再试

## 与 sina-forex 配合使用

```bash
# 1. 查看美股外盘
python .agents/skills/us-market-watch/scripts/fetch_us_market.py --watch

# 2. 查看离岸人民币
python .agents/skills/sina-forex/scripts/fetch_forex.py USDCNH
```

**综合分析：**
- 美股涨 + 人民币升值 → A股利好
- 美股跌 + 人民币贬值 → A股利空
- 中概股跌 + 人民币贬值 → 双重利空

## 更新日志

- **v1.0.0** - 初始版本，支持美股指数、中概股ETF、A50期指
