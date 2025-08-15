#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newsletter搜索功能演示程序
展示所有常用的搜索方式和使用场景
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum

# API配置
API_BASE_URL = "http://localhost:9011/api/v1"
QUICK_SEARCH_URL = f"{API_BASE_URL}/newsletter/search/quick"
FULL_SEARCH_URL = f"{API_BASE_URL}/newsletter/search/"
ADVANCED_SEARCH_URL = f"{API_BASE_URL}/newsletter/search/advanced"


class SearchMode(Enum):
    """搜索模式枚举"""
    SINGLE_KEYWORD = "单关键词搜索"
    MULTI_KEYWORDS = "多关键词搜索"
    PHRASE_SEARCH = "短语精确搜索"
    WILDCARD = "通配符搜索"
    MIXED = "混合搜索"
    CASE_INSENSITIVE = "大小写不敏感"
    WITH_FILTERS = "带过滤条件"
    PAGINATION = "分页搜索"
    SORTED = "排序搜索"
    COMPLEX = "复杂组合搜索"


class NewsletterSearchDemo:
    """Newsletter搜索演示类"""
    
    def __init__(self):
        self.results_cache = []
        self.test_stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "total_time": 0
        }
    
    def check_server(self) -> bool:
        """检查服务器是否运行"""
        try:
            response = requests.get("http://localhost:9011/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def format_result(self, result: Dict[str, Any], max_title_length: int = 60) -> str:
        """格式化单个搜索结果"""
        title = result.get('title', 'N/A')[:max_title_length]
        score = result.get('score', 0)
        size = result.get('size', 0)
        
        # 格式化文件大小
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f}MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f}KB"
        else:
            size_str = f"{size}B"
        
        return f"[{score:6.2f}] {title:<60} ({size_str})"
    
    def print_results(self, results: List[Dict], limit: int = 5, show_highlight: bool = True):
        """打印搜索结果"""
        if not results:
            print("     没有找到结果")
            return
        
        for i, result in enumerate(results[:limit], 1):
            print(f"     {i}. {self.format_result(result)}")
            
            # 显示高亮内容
            if show_highlight and 'highlight' in result:
                highlights = result['highlight']
                for field, fragments in highlights.items():
                    if fragments:
                        fragment = fragments[0][:100]
                        print(f"        💡 {field}: {fragment}...")
    
    def search_with_timing(self, 
                          endpoint: str, 
                          params: Dict = None, 
                          data: Dict = None,
                          method: str = "GET") -> Dict:
        """执行搜索并记录时间"""
        start_time = time.time()
        self.test_stats["total_searches"] += 1
        
        try:
            if method == "GET":
                response = requests.get(endpoint, params=params, timeout=10)
            else:  # POST
                response = requests.post(endpoint, json=data, 
                                       headers={'Content-Type': 'application/json'},
                                       timeout=10)
            
            elapsed_time = time.time() - start_time
            self.test_stats["total_time"] += elapsed_time
            
            if response.status_code == 200:
                self.test_stats["successful_searches"] += 1
                result = response.json()
                result['_elapsed_time'] = elapsed_time
                return result
            else:
                self.test_stats["failed_searches"] += 1
                return {"error": f"HTTP {response.status_code}", "_elapsed_time": elapsed_time}
                
        except Exception as e:
            self.test_stats["failed_searches"] += 1
            elapsed_time = time.time() - start_time
            return {"error": str(e), "_elapsed_time": elapsed_time}
    
    # ============ 搜索模式演示方法 ============
    
    def demo_single_keyword(self):
        """演示：单关键词搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.SINGLE_KEYWORD.value}")
        print("="*70)
        print("使用场景：快速查找包含特定概念的文档")
        print("-"*70)
        
        keywords = ["AI", "transformer", "neural", "GPT"]
        
        for keyword in keywords:
            print(f"\n🔍 搜索: '{keyword}'")
            
            # 使用快速搜索接口
            result = self.search_with_timing(
                QUICK_SEARCH_URL,
                params={"q": keyword}
            )
            
            if 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个结果 (耗时: {result['_elapsed_time']:.2f}秒)")
                self.print_results(result.get('results', []), limit=3)
            else:
                print(f"   ❌ 错误: {result['error']}")
    
    def demo_multi_keywords(self):
        """演示：多关键词搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.MULTI_KEYWORDS.value}")
        print("="*70)
        print("使用场景：查找同时涉及多个概念的文档")
        print("-"*70)
        
        queries = [
            ("AI agent", "AI智能体相关"),
            ("machine learning model", "机器学习模型"),
            ("deep neural network", "深度神经网络"),
            ("LLM GPT Claude", "大语言模型")
        ]
        
        for query, description in queries:
            print(f"\n🔍 搜索: '{query}' ({description})")
            
            result = self.search_with_timing(
                FULL_SEARCH_URL,
                params={
                    "query": query,
                    "size": 5,
                    "highlight": True
                }
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个结果 (耗时: {result['_elapsed_time']:.2f}秒)")
                self.print_results(result.get('results', []), limit=3)
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def demo_phrase_search(self):
        """演示：短语精确搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.PHRASE_SEARCH.value}")
        print("="*70)
        print("使用场景：查找包含特定短语的文档")
        print("技巧：使用引号包围短语进行精确匹配")
        print("-"*70)
        
        phrases = [
            '"neural network"',
            '"machine learning"',
            '"language model"',
            '"AI agent"'
        ]
        
        for phrase in phrases:
            print(f"\n🔍 搜索短语: {phrase}")
            
            result = self.search_with_timing(
                FULL_SEARCH_URL,
                params={
                    "query": phrase,
                    "size": 5,
                    "highlight": True
                }
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个精确匹配 (耗时: {result['_elapsed_time']:.2f}秒)")
                self.print_results(result.get('results', []), limit=2)
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def demo_wildcard_search(self):
        """演示：通配符搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.WILDCARD.value}")
        print("="*70)
        print("使用场景：查找以特定前缀开头的词")
        print("技巧：使用*作为通配符")
        print("-"*70)
        
        patterns = [
            ("transform*", "所有transform开头的词"),
            ("learn*", "所有learn开头的词"),
            ("neural*", "所有neural开头的词")
        ]
        
        for pattern, description in patterns:
            print(f"\n🔍 搜索模式: {pattern} ({description})")
            
            result = self.search_with_timing(
                FULL_SEARCH_URL,
                params={
                    "query": pattern,
                    "size": 5,
                    "highlight": False
                }
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个匹配 (耗时: {result['_elapsed_time']:.2f}秒)")
                self.print_results(result.get('results', []), limit=3, show_highlight=False)
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def demo_mixed_search(self):
        """演示：混合搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.MIXED.value}")
        print("="*70)
        print("使用场景：组合使用关键词和短语")
        print("-"*70)
        
        mixed_queries = [
            ('AI "deep learning"', '关键词+短语'),
            ('"neural network" transformer', '短语+关键词'),
            ('GPT "language model" transformer', '多种组合')
        ]
        
        for query, description in mixed_queries:
            print(f"\n🔍 混合搜索: {query} ({description})")
            
            result = self.search_with_timing(
                FULL_SEARCH_URL,
                params={
                    "query": query,
                    "size": 5,
                    "highlight": True
                }
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个结果 (耗时: {result['_elapsed_time']:.2f}秒)")
                self.print_results(result.get('results', []), limit=2)
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def demo_case_insensitive(self):
        """演示：大小写不敏感搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.CASE_INSENSITIVE.value}")
        print("="*70)
        print("使用场景：不确定关键词大小写时")
        print("-"*70)
        
        case_tests = [
            ("gpt", "小写"),
            ("GPT", "大写"),
            ("GpT", "混合大小写")
        ]
        
        print("\n测试同一关键词的不同大小写形式:")
        for query, case_type in case_tests:
            print(f"\n🔍 搜索: '{query}' ({case_type})")
            
            result = self.search_with_timing(
                QUICK_SEARCH_URL,
                params={"q": query}
            )
            
            if 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个结果")
                # 只显示第一个结果证明大小写不敏感
                results = result.get('results', [])
                if results:
                    print(f"     首个结果: {results[0].get('title', 'N/A')[:60]}...")
            else:
                print(f"   ❌ 错误: {result['error']}")
    
    def demo_filtered_search(self):
        """演示：带过滤条件的搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.WITH_FILTERS.value}")
        print("="*70)
        print("使用场景：精确控制搜索范围")
        print("-"*70)
        
        filter_cases = [
            {
                "name": "按文档类型过滤",
                "body": {
                    "query": "AI",
                    "article_type": "markdown",
                    "from": 0,
                    "size": 5
                }
            },
            {
                "name": "按文件大小过滤",
                "body": {
                    "query": "neural",
                    "min_wordcount": 1000,  # 约10KB
                    "max_wordcount": 5000,  # 约50KB
                    "from": 0,
                    "size": 5
                }
            },
            {
                "name": "组合过滤",
                "body": {
                    "query": "transformer",
                    "article_type": "markdown",
                    "min_wordcount": 500,
                    "from": 0,
                    "size": 5,
                    "sort_by": "size"
                }
            }
        ]
        
        for case in filter_cases:
            print(f"\n🔍 {case['name']}")
            print(f"   过滤条件: {json.dumps(case['body'], ensure_ascii=False, indent=2)}")
            
            result = self.search_with_timing(
                ADVANCED_SEARCH_URL,
                data=case['body'],
                method="POST"
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个符合条件的结果 (耗时: {result['_elapsed_time']:.2f}秒)")
                
                # 显示应用的过滤器
                if 'filters' in result:
                    active_filters = {k: v for k, v in result['filters'].items() if v}
                    if active_filters:
                        print("   应用的过滤器:")
                        for k, v in active_filters.items():
                            print(f"     - {k}: {v}")
                
                self.print_results(result.get('results', []), limit=3, show_highlight=False)
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def demo_pagination(self):
        """演示：分页搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.PAGINATION.value}")
        print("="*70)
        print("使用场景：处理大量搜索结果")
        print("-"*70)
        
        query = "AI"
        page_size = 5
        
        print(f"\n🔍 搜索 '{query}' 并分页显示 (每页{page_size}条)")
        
        # 获取前3页
        for page in range(3):
            from_index = page * page_size
            print(f"\n📄 第 {page + 1} 页 (from={from_index}, size={page_size})")
            
            result = self.search_with_timing(
                FULL_SEARCH_URL,
                params={
                    "query": query,
                    "from": from_index,
                    "size": page_size,
                    "highlight": False
                }
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                total_pages = (total + page_size - 1) // page_size
                print(f"   共 {total} 条记录，{total_pages} 页")
                
                results = result.get('results', [])
                for i, doc in enumerate(results, 1):
                    global_index = from_index + i
                    title = doc.get('title', 'N/A')[:50]
                    score = doc.get('score', 0)
                    print(f"     {global_index:3}. [{score:6.2f}] {title}...")
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
                break
    
    def demo_sorted_search(self):
        """演示：排序搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.SORTED.value}")
        print("="*70)
        print("使用场景：按不同维度查看结果")
        print("-"*70)
        
        query = "transformer"
        sort_options = [
            ("_score", "相关度排序（默认）"),
            ("size", "文件大小排序")
        ]
        
        for sort_by, description in sort_options:
            print(f"\n🔍 搜索 '{query}' - {description}")
            
            result = self.search_with_timing(
                FULL_SEARCH_URL,
                params={
                    "query": query,
                    "size": 5,
                    "sort_by": sort_by,
                    "highlight": False
                }
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"   ✅ 找到 {total} 个结果 (排序: {sort_by})")
                
                results = result.get('results', [])
                for i, doc in enumerate(results[:5], 1):
                    title = doc.get('title', 'N/A')[:50]
                    score = doc.get('score', 0)
                    size = doc.get('size', 0)
                    
                    if sort_by == "_score":
                        print(f"     {i}. [相关度:{score:6.2f}] {title}...")
                    else:
                        size_kb = size / 1024
                        print(f"     {i}. [大小:{size_kb:7.1f}KB] {title}...")
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def demo_complex_search(self):
        """演示：复杂组合搜索"""
        print(f"\n{'='*70}")
        print(f"📌 {SearchMode.COMPLEX.value}")
        print("="*70)
        print("使用场景：精确定位特定内容")
        print("-"*70)
        
        complex_cases = [
            {
                "name": "多关键词+过滤+排序",
                "body": {
                    "query": "AI agent LLM",
                    "article_type": "markdown",
                    "min_wordcount": 1000,
                    "from": 0,
                    "size": 10,
                    "sort_by": "size"
                },
                "description": "查找包含AI、agent、LLM的大型markdown文档"
            },
            {
                "name": "短语+通配符+过滤",
                "body": {
                    "query": '"neural network" transform*',
                    "min_wordcount": 500,
                    "max_wordcount": 3000,
                    "from": 0,
                    "size": 5,
                    "sort_by": "_score"
                },
                "description": "查找讨论神经网络和transformer的中等长度文档"
            }
        ]
        
        for case in complex_cases:
            print(f"\n🔍 {case['name']}")
            print(f"   描述: {case['description']}")
            print(f"   查询参数:")
            for k, v in case['body'].items():
                print(f"     - {k}: {v}")
            
            result = self.search_with_timing(
                ADVANCED_SEARCH_URL,
                data=case['body'],
                method="POST"
            )
            
            if result.get('success', True) and 'error' not in result:
                total = result.get('total', 0)
                print(f"\n   ✅ 找到 {total} 个结果 (耗时: {result['_elapsed_time']:.2f}秒)")
                
                results = result.get('results', [])
                if results:
                    print("   匹配的文档:")
                    self.print_results(results, limit=5, show_highlight=False)
                    
                    # 统计信息
                    if len(results) > 1:
                        avg_score = sum(r.get('score', 0) for r in results) / len(results)
                        avg_size = sum(r.get('size', 0) for r in results) / len(results)
                        print(f"\n   📊 统计:")
                        print(f"     平均相关度: {avg_score:.2f}")
                        print(f"     平均大小: {avg_size/1024:.1f}KB")
            else:
                print(f"   ❌ 错误: {result.get('error', '搜索失败')}")
    
    def print_statistics(self):
        """打印测试统计信息"""
        print(f"\n{'='*70}")
        print("📊 测试统计")
        print("="*70)
        print(f"总搜索次数: {self.test_stats['total_searches']}")
        print(f"成功次数: {self.test_stats['successful_searches']}")
        print(f"失败次数: {self.test_stats['failed_searches']}")
        if self.test_stats['total_searches'] > 0:
            success_rate = (self.test_stats['successful_searches'] / 
                          self.test_stats['total_searches']) * 100
            avg_time = self.test_stats['total_time'] / self.test_stats['total_searches']
            print(f"成功率: {success_rate:.1f}%")
            print(f"平均响应时间: {avg_time:.3f}秒")
            print(f"总耗时: {self.test_stats['total_time']:.2f}秒")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("="*80)
        print("🚀 Newsletter搜索功能完整演示")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not self.check_server():
            print("\n❌ 服务器未运行！")
            print("请先启动后端服务:")
            print("  cd minio-file-manager/backend")
            print("  python3 -m uvicorn app.main:app --reload --port 9011")
            return
        
        print("\n✅ 服务器运行正常")
        print("\n开始演示各种搜索模式...")
        
        # 运行所有演示
        demos = [
            self.demo_single_keyword,
            self.demo_multi_keywords,
            self.demo_phrase_search,
            self.demo_wildcard_search,
            self.demo_mixed_search,
            self.demo_case_insensitive,
            self.demo_filtered_search,
            self.demo_pagination,
            self.demo_sorted_search,
            self.demo_complex_search
        ]
        
        for demo in demos:
            try:
                demo()
                time.sleep(0.5)  # 避免请求过快
            except Exception as e:
                print(f"\n❌ 演示出错: {str(e)}")
        
        # 打印统计信息
        self.print_statistics()
        
        print("\n" + "="*80)
        print("✅ 所有演示完成！")
        print("="*80)
        
        # 使用建议
        print("\n💡 使用建议:")
        print("1. 单关键词搜索: 适合快速查找")
        print("2. 多关键词搜索: 适合查找相关主题")
        print("3. 短语搜索: 使用引号进行精确匹配")
        print("4. 通配符搜索: 使用*匹配词前缀")
        print("5. 过滤搜索: 通过类型、大小等缩小范围")
        print("6. 分页搜索: 处理大量结果时使用")
        print("7. 排序搜索: 按相关度或大小排序")
        print("8. 复杂搜索: 组合多种条件精确定位")
        
        print("\n📚 API文档:")
        print(f"  Swagger UI: http://localhost:9011/docs")
        print(f"  ReDoc: http://localhost:9011/redoc")


def main():
    """主函数"""
    demo = NewsletterSearchDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()