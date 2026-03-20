---
name: eastmoney-calendar
description: 爬取东方财富财经日历经济数据；当用户需要获取全球财经日历、经济指标数据、财经事件信息时使用
dependency:
  python:
    - requests>=2.25.0
---

# 东方财富财经日历爬取工具

## 任务目标
- 本 Skill 用于从东方财富网财经日历接口获取全球经济事件数据
- 能力包含：获取指定日期范围的财经事件、自动处理分页、输出结构化 JSON 数据
- 触发条件：用户需要财经日历数据、经济指标发布信息、全球财经事件时

## 前置准备
- Python 依赖：
  ```
  requests>=2.25.0
  ```

## 操作步骤

### 标准流程
1. **执行数据爬取**
   - 调用 `scripts/fetch_data.py` 脚本
   - 必需参数：start_date（开始日期），end_date（结束日期）
   - 格式：YYYY-MM-DD
   - 示例：`python scripts/fetch_data.py 2026-02-27 2026-03-27`

2. **处理返回数据**
   - 脚本返回 JSON 格式数据
   - 包含字段：TotalCount（总数），Data（事件列表）
   - 事件字段包括：REPORT_DATE（报告日期）、COUNTRY（国家）、EVENT_NAME（事件名称）、ACTUAL_PRICE（实际值）、PRE_PRICE（前值）、PUBLISH_PRICE（预测值）等

3. **数据使用**
   - 保存为 JSON 文件或进行进一步分析
   - 根据需要筛选特定国家或事件类型

### 可选参数
- `--type`：事件类型过滤（可选）
- `--size`：每页数据条数（默认 100）
- `--output` / `-o`：输出文件路径（可选，推荐用于 Windows 避免编码问题）

## Windows 编码问题解决方案

在 Windows 环境下，直接输出到控制台可能出现中文乱码。有两种解决方案：

### 方案一：设置 Python 环境变量（推荐，简单快捷）

在 PowerShell 中执行：
```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/fetch_data.py 2026-03-01 2026-03-10
```

或在 CMD 中执行：
```cmd
set PYTHONIOENCODING=utf-8
python scripts/fetch_data.py 2026-03-01 2026-03-10
```

### 方案二：使用 --output 参数保存到文件

```bash
python scripts/fetch_data.py 2026-03-01 2026-03-10 --output result.json
```

然后使用支持 UTF-8 的编辑器（如 VS Code）打开查看，或让 AI 助手读取分析。

### 方案三：修改控制台编码（临时生效）

```powershell
# PowerShell
chcp 65001
$env:PYTHONIOENCODING="utf-8"
python scripts/fetch_data.py 2026-03-01 2026-03-10
```

```cmd
:: CMD
chcp 65001
set PYTHONIOENCODING=utf-8
python scripts/fetch_data.py 2026-03-01 2026-03-10
```

## 资源索引
- 核心脚本：[scripts/fetch_data.py](scripts/fetch_data.py)
  - 用途：爬取东方财富财经日历数据
  - 参数：start_date, end_date, [--type], [--size], [--output]
  - 自动处理分页，获取完整数据

## 注意事项
- 爬取的是东方财富网公开数据，无需授权凭证
- 请求包含模拟浏览器 Headers 和 Cookies
- 网络异常时会返回错误信息
- 建议合理设置日期范围，避免请求数据量过大

## 使用示例

### 示例 1：获取单周财经日历（输出到控制台）
```bash
python scripts/fetch_data.py 2026-02-27 2026-03-06
```

### 示例 2：获取特定类型事件
```bash
python scripts/fetch_data.py 2026-02-27 2026-03-27 --type 2
```

### 示例 3：获取月度完整数据（增加每页条数）
```bash
python scripts/fetch_data.py 2026-02-01 2026-02-28 --size 200
```

### 示例 4：保存到文件（避免编码问题）
```bash
python scripts/fetch_data.py 2026-03-01 2026-03-10 --output calendar_data.json
```

### 示例 5：保存到指定路径
```bash
python scripts/fetch_data.py 2026-03-01 2026-03-10 -o D:/data/economic_calendar.json
```

## 故障排查

### 中文乱码问题
**症状**：控制台显示 `����` 等乱码
**原因**：Windows 控制台默认使用 GBK 编码，与 Python 输出的 UTF-8 不兼容
**解决**：设置 `PYTHONIOENCODING=utf-8` 环境变量

```powershell
# PowerShell（推荐）
$env:PYTHONIOENCODING="utf-8"
python scripts/fetch_data.py 2026-03-01 2026-03-10

# 或在 CMD 中
set PYTHONIOENCODING=utf-8
python scripts/fetch_data.py 2026-03-01 2026-03-10
```

备选方案：使用 `--output` 参数保存到文件
```bash
python scripts/fetch_data.py 2026-03-01 2026-03-10 --output result.json
```

### 网络请求失败
**症状**：返回错误信息或超时
**解决**：检查网络连接，稍后重试，或减小日期范围
