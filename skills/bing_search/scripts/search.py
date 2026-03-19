#!/usr/bin/env python3
"""
Bing Search Skill - 修复版
支持中文搜索，正确解析搜索结果
"""
import sys
import os
import json
import ssl
import gzip
import io
import urllib.request
import urllib.parse
from typing import List, Dict, Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("错误: 缺少 beautifulsoup4。请运行: pip install beautifulsoup4", file=sys.stderr)
    sys.exit(1)


# 修复 Windows 控制台编码
if sys.platform == 'win32':
    import codecs
    # 设置 stdout 和 stderr 为 UTF-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


# 默认不过滤任何域名，如需过滤可手动添加
# 示例: ['zhihu.com', 'baidu.com']
DEFAULT_EXCLUDED_DOMAINS = []

# 请求头配置
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Accept-Encoding': 'identity',  # 不请求压缩，简化处理
    'Referer': 'https://www.bing.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def decode_response(response) -> str:
    """解码响应内容，处理可能的压缩"""
    data = response.read()
    
    # 检查 Content-Encoding
    encoding = response.headers.get('Content-Encoding', '').lower()
    
    if encoding == 'gzip':
        try:
            data = gzip.decompress(data)
        except:
            pass
    
    # 尝试检测编码
    charset = response.headers.get_content_charset()
    if charset:
        return data.decode(charset, errors='ignore')
    
    # 默认 UTF-8
    return data.decode('utf-8', errors='ignore')


def search_bing(query: str, proxy: Optional[str] = None, num_results: int = 10, exclude_domains: Optional[List[str]] = None) -> Dict:
    """
    使用 Bing 执行网页搜索
    
    Args:
        query: 搜索关键词（支持中文）
        proxy: 代理服务器地址
        num_results: 返回结果数量
        exclude_domains: 要过滤的域名列表（如 ['zhihu.com']）
        
    Returns:
        包含搜索结果的字典
    """
    # 对查询词进行 URL 编码（使用 quote_plus 处理空格）
    encoded_query = urllib.parse.quote_plus(query)
    
    # 构建 Bing 搜索 URL
    # setmkt=zh-CN 强制使用中文市场，setlang=zh 强制中文界面
    url = f"https://www.bing.com/search?q={encoded_query}&setmkt=zh-CN&setlang=zh&FORM=BEHPTB"
    
    # 创建请求
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    
    # 配置代理
    proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else None
    
    # SSL 上下文（禁用证书验证以兼容性）
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 构建 opener
    opener = urllib.request.build_opener(
        proxy_handler or urllib.request.ProxyHandler(),
        urllib.request.HTTPSHandler(context=ctx)
    )
    
    try:
        with opener.open(req, timeout=30) as resp:
            html = decode_response(resp)
        
        # 使用 BeautifulSoup 解析
        soup = BeautifulSoup(html, 'html.parser')
        
        # 处理过滤域名
        if exclude_domains is None:
            exclude_domains = DEFAULT_EXCLUDED_DOMAINS
        else:
            exclude_domains = [d.lower() for d in exclude_domains]
        
        # 提取搜索结果
        results = []
        seen_urls = set()
        filtered_count = 0
        
        # Bing 搜索结果通常在 .b_algo 类的 li 元素中
        search_results = soup.find_all('li', class_='b_algo')
        
        for item in search_results:
            if len(results) >= num_results:
                break
            
            try:
                # 提取标题和链接
                title_tag = item.find('h2')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href', '')
                
                # 跳过无效链接
                if not link or not link.startswith('http'):
                    continue
                
                # 跳过 Bing 自身和已处理的链接
                if any(x in link.lower() for x in ['bing.com', 'microsoft.com', 'r.bing.com']):
                    continue
                
                if link in seen_urls:
                    continue
                
                # 跳过过滤列表中的域名
                link_lower = link.lower()
                is_excluded = False
                for domain in exclude_domains:
                    if domain in link_lower:
                        is_excluded = True
                        filtered_count += 1
                        break
                if is_excluded:
                    continue
                
                # 提取摘要
                snippet = ""
                # 尝试多种可能的摘要容器
                for selector in ['.b_caption p', '.b_snippet', '.b_algo p', 'p']:
                    snippet_tag = item.select_one(selector)
                    if snippet_tag:
                        snippet = snippet_tag.get_text(strip=True)
                        if len(snippet) > 20:  # 确保摘要有意义
                            break
                
                # 提取来源/显示链接
                source = ""
                cite_tag = item.find('cite')
                if cite_tag:
                    source = cite_tag.get_text(strip=True)
                else:
                    # 从链接提取域名
                    parsed = urllib.parse.urlparse(link)
                    source = parsed.netloc
                
                result = {
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "source": source,
                    "position": len(results) + 1
                }
                
                results.append(result)
                seen_urls.add(link)
                
            except Exception as e:
                continue
        
        return {
            "status": "success",
            "query": query,
            "num_requested": num_results,
            "num_returned": len(results),
            "filtered_count": filtered_count,
            "excluded_domains": exclude_domains,
            "results": results
        }
        
    except urllib.error.URLError as e:
        return {
            "status": "error",
            "query": query,
            "num_requested": num_results,
            "message": f"网络错误: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "num_requested": num_results,
            "message": f"处理错误: {str(e)}",
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Bing 搜索工具 - 支持中文，自动过滤知乎等低质量来源',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python search.py "美联储议息会议 2026"
  python search.py "人工智能新闻" 10
  python search.py "Python教程" --no-filter
  python search.py "股票分析" --exclude baidu.com,weibo.com
        """
    )
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('num_results', nargs='?', type=int, default=10, 
                        help='返回结果数量（默认10）')
    parser.add_argument('--no-filter', action='store_true',
                        help='不过滤任何域名')
    parser.add_argument('--exclude', type=str, metavar='DOMAINS',
                        help='额外过滤的域名，逗号分隔（如 baidu.com,weibo.com）')
    parser.add_argument('--include-zhihu', action='store_true',
                        help='保留知乎结果（默认过滤知乎）')
    
    args = parser.parse_args()
    
    query = args.query
    num_results = args.num_results
    proxy = os.environ.get("ALL_PROXY") or os.environ.get("HTTP_PROXY")
    
    # 处理过滤域名
    exclude_domains = []
    if not args.no_filter:
        if args.include_zhihu:
            # 不排除知乎，只保留其他默认排除项（如果有的话）
            exclude_domains = [d for d in DEFAULT_EXCLUDED_DOMAINS if 'zhihu' not in d]
        else:
            # 默认过滤知乎
            exclude_domains = DEFAULT_EXCLUDED_DOMAINS.copy()
        
        # 添加额外过滤域名
        if args.exclude:
            extra_domains = [d.strip().lower() for d in args.exclude.split(',')]
            exclude_domains.extend(extra_domains)
    
    result = search_bing(query, proxy, num_results, exclude_domains if exclude_domains else None)
    
    # 输出到文件避免控制台编码问题
    output_file = "bing_search_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    status = result.get("status", "unknown")
    query_text = result.get("query", query)
    print(f"搜索完成: {query_text} (status={status})", file=sys.stderr)
    print(f"找到 {result.get('num_returned', 0)} 条结果", file=sys.stderr)
    if status != "success":
        print(f"错误信息: {result.get('message', '')}", file=sys.stderr)
    print(f"详细结果已保存到: {output_file}", file=sys.stderr)
    
    # 输出 JSON 到 stdout（用于管道）
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
