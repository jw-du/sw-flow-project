---
name: bing_search
description: Bing search skill for all users. No API key needed. Supports Chinese and English search.
dependency:
  python:
    - beautifulsoup4>=4.11.0
---

# Bing Search Skill

简单的 Bing 网页搜索 Skill，**无需 API Key**。

## 特性
- ✅ 无需 API Key
- ✅ 支持中文搜索（已修复编码问题）
- ✅ 返回结构化结果（标题、链接、摘要、来源）
- ✅ 自动处理 gzip 压缩

## 依赖安装
```bash
pip install beautifulsoup4
```

## 使用方法

### 基本用法（自动过滤知乎）
```bash
python .agents/skills/bing_search/scripts/search.py "搜索关键词"
```

### 指定结果数量
```bash
python .agents/skills/bing_search/scripts/search.py "搜索关键词" 10
```

### 高级选项

**推荐使用：过滤特定域名**

当搜索结果包含过多低质量或无关网站时，使用 `--exclude` 过滤：
```bash
# 过滤知乎（如果不需要知乎内容）
python .agents/skills/bing_search/scripts/search.py "搜索关键词" --exclude "zhihu.com,zhuanlan.zhihu.com"

# 过滤多个域名
python .agents/skills/bing_search/scripts/search.py "搜索关键词" --exclude "baidu.com,weibo.com,sogou.com"

# 仅过滤知乎，保留其他来源
python .agents/skills/bing_search/scripts/search.py "搜索关键词" --exclude "zhihu.com"
```

**保留知乎结果（不过滤）**
```bash
python .agents/skills/bing_search/scripts/search.py "搜索关键词" --include-zhihu
```

**关闭所有过滤（获取最全结果）**
```bash
python .agents/skills/bing_search/scripts/search.py "搜索关键词" --no-filter
```

### 示例

**中文搜索：**
```bash
python .agents/skills/bing_search/scripts/search.py "美联储议息会议 2026" 5
```

**英文搜索：**
```bash
python .agents/skills/bing_search/scripts/search.py "FOMC meeting 2026 schedule" 5
```

## 输出格式
```json
{
  "status": "success",
  "query": "搜索关键词",
  "num_requested": 5,
  "num_returned": 5,
  "filtered_count": 3,
  "excluded_domains": ["zhihu.com", "zhuanlan.zhihu.com"],
  "results": [
    {
      "title": "结果标题",
      "link": "https://example.com/article",
      "snippet": "结果摘要...",
      "source": "example.com",
      "position": 1
    }
  ]
}
```

### 新增字段说明
| 字段 | 说明 |
|------|------|
| `filtered_count` | 被过滤的结果数量 |
| `excluded_domains` | 当前过滤的域名列表 |

## 环境变量
- `HTTP_PROXY` / `ALL_PROXY`: 设置代理服务器（可选）

## 注意事项
1. 结果会同时保存到 `bing_search_result.json` 文件
2. 中文搜索已修复编码问题，支持正常显示
3. 默认返回 10 条结果，最多可自定义
4. **默认自动过滤知乎（zhihu.com）结果**，提高搜索质量
5. **Windows 用户如遇到中文乱码，请设置环境变量**：`$env:PYTHONIOENCODING="utf-8"`

## Windows 中文显示设置

如果在 Windows PowerShell 中看到中文乱码（`����`），请在执行前设置 Python 环境变量：

```powershell
# PowerShell
$env:PYTHONIOENCODING="utf-8"
python .agents/skills/bing_search/scripts/search.py "搜索关键词" 10
```

或在 CMD 中：
```cmd
set PYTHONIOENCODING=utf-8
python .agents/skills/bing_search/scripts/search.py "搜索关键词" 10
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| 缺少依赖 | `pip install beautifulsoup4` |
| 返回 0 条结果 | 检查网络连接，或尝试更换搜索词 |
| 中文显示乱码 | 设置 `$env:PYTHONIOENCODING="utf-8"` 后重试 |
