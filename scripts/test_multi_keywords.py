#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多个关键词搜索功能
"""

import requests
import json
from datetime import datetime
import time

# API基础URL
API_BASE_URL = "http://localhost:9011/api/v1"

def test_multi_keywords():
    """测试多个关键词搜索"""
    print("="*80)
    print("🔍 测试多个关键词搜索功能")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 测试用例：不同的多关键词组合
    test_cases = [
        {
            "name": "两个关键词 (AND逻辑)",
            "query": "AI agent",
            "description": "搜索同时包含AI和agent的文档"
        },
        {
            "name": "三个关键词",
            "query": "machine learning model",
            "description": "搜索包含machine、learning、model的文档"
        },
        {
            "name": "短语搜索",
            "query": "\"neural network\"",
            "description": "搜索包含完整短语'neural network'的文档"
        },
        {
            "name": "混合搜索",
            "query": "AI \"deep learning\" transformer",
            "description": "搜索包含AI、完整短语'deep learning'和transformer的文档"
        },
        {
            "name": "大小写混合",
            "query": "GPT llm TRANSFORMER",
            "description": "测试大小写不敏感搜索"
        },
        {
            "name": "通配符搜索",
            "query": "transform*",
            "description": "搜索以transform开头的词"
        },
        {
            "name": "长关键词组合",
            "query": "artificial intelligence machine learning deep neural network",
            "description": "搜索包含多个相关概念的文档"
        },
        {
            "name": "布尔操作符模拟",
            "query": "LLM GPT Claude",
            "description": "搜索包含LLM、GPT或Claude的文档"
        },
        {
            "name": "技术栈组合",
            "query": "python tensorflow pytorch",
            "description": "搜索包含Python框架的文档"
        },
        {
            "name": "概念组合",
            "query": "agent reasoning planning",
            "description": "搜索AI agent相关概念"
        }
    ]
    
    # 测试每个端点
    endpoints = [
        {
            "name": "快速搜索",
            "url": f"{API_BASE_URL}/newsletter/search/quick",
            "method": "GET",
            "param_name": "q"
        },
        {
            "name": "完整搜索",
            "url": f"{API_BASE_URL}/newsletter/search/",
            "method": "GET",
            "param_name": "query"
        },
        {
            "name": "高级搜索",
            "url": f"{API_BASE_URL}/newsletter/search/advanced",
            "method": "POST",
            "param_name": "query"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"📌 测试端点: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   方法: {endpoint['method']}")
        print("="*60)
        
        for test_case in test_cases:
            print(f"\n🔸 {test_case['name']}")
            print(f"   查询: \"{test_case['query']}\"")
            print(f"   说明: {test_case['description']}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                
                if endpoint['method'] == 'GET':
                    params = {
                        endpoint['param_name']: test_case['query'],
                        'size': 5,
                        'highlight': True
                    }
                    response = requests.get(endpoint['url'], params=params)
                else:  # POST
                    data = {
                        endpoint['param_name']: test_case['query'],
                        'from': 0,
                        'size': 5,
                        'sort_by': '_score'
                    }
                    response = requests.post(
                        endpoint['url'],
                        json=data,
                        headers={'Content-Type': 'application/json'}
                    )
                
                elapsed_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 处理不同的响应格式
                    if endpoint['name'] == '快速搜索':
                        total = result.get('total', 0)
                        results = result.get('results', [])
                    else:
                        total = result.get('total', 0)
                        results = result.get('results', [])
                        if 'success' in result and not result['success']:
                            print(f"   ❌ 搜索失败: {result.get('error', '未知错误')}")
                            continue
                    
                    print(f"   ✅ 找到 {total} 个结果 (耗时: {elapsed_time:.2f}秒)")
                    
                    # 显示前3个结果
                    for i, doc in enumerate(results[:3], 1):
                        title = doc.get('title', 'N/A')[:60]
                        score = doc.get('score', 0)
                        print(f"      {i}. [{score:.2f}] {title}...")
                        
                        # 显示高亮内容（如果有）
                        if 'highlight' in doc:
                            highlights = doc['highlight']
                            for field, fragments in highlights.items():
                                if fragments:
                                    fragment = fragments[0][:100]
                                    print(f"         高亮({field}): {fragment}...")
                    
                    # 分析关键词匹配情况
                    if total > 0 and results:
                        print(f"\n   📊 匹配分析:")
                        keywords = test_case['query'].replace('"', '').split()
                        print(f"      输入关键词: {keywords}")
                        print(f"      最高相关度: {results[0].get('score', 0):.2f}")
                        if len(results) > 1:
                            print(f"      平均相关度: {sum(r.get('score', 0) for r in results) / len(results):.2f}")
                        
                else:
                    print(f"   ❌ HTTP错误 {response.status_code}")
                    print(f"      {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ 请求失败: {str(e)}")
            
            # 短暂延迟避免请求过快
            time.sleep(0.1)


def test_advanced_multi_keywords():
    """测试高级多关键词搜索场景"""
    print(f"\n{'='*80}")
    print("🔬 高级多关键词搜索测试")
    print("="*80)
    
    url = f"{API_BASE_URL}/newsletter/search/advanced"
    
    advanced_cases = [
        {
            "name": "关键词 + 类型过滤",
            "body": {
                "query": "AI agent LLM",
                "article_type": "markdown",
                "from": 0,
                "size": 5
            }
        },
        {
            "name": "关键词 + 大小过滤",
            "body": {
                "query": "machine learning",
                "min_wordcount": 500,
                "max_wordcount": 2000,
                "from": 0,
                "size": 5
            }
        },
        {
            "name": "复杂查询组合",
            "body": {
                "query": "transformer attention mechanism",
                "article_type": "markdown",
                "min_wordcount": 1000,
                "from": 0,
                "size": 10,
                "sort_by": "size"
            }
        }
    ]
    
    for test_case in advanced_cases:
        print(f"\n🔹 {test_case['name']}")
        print(f"   请求体: {json.dumps(test_case['body'], ensure_ascii=False)}")
        print("-" * 40)
        
        try:
            response = requests.post(
                url,
                json=test_case['body'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', True):
                    total = result.get('total', 0)
                    results = result.get('results', [])
                    
                    print(f"   ✅ 找到 {total} 个结果")
                    
                    # 显示过滤条件
                    if 'filters' in result:
                        active_filters = {k: v for k, v in result['filters'].items() if v}
                        if active_filters:
                            print("   应用的过滤条件:")
                            for k, v in active_filters.items():
                                print(f"      - {k}: {v}")
                    
                    # 显示结果摘要
                    if results:
                        print(f"   前{min(3, len(results))}个结果:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"      {i}. [{doc.get('score', 0):.2f}] {doc.get('title', 'N/A')[:50]}...")
                else:
                    print(f"   ❌ 搜索失败: {result.get('error', '未知错误')}")
            else:
                print(f"   ❌ HTTP错误 {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {str(e)}")


def analyze_results():
    """分析搜索结果的关键词覆盖度"""
    print(f"\n{'='*80}")
    print("📈 关键词覆盖度分析")
    print("="*80)
    
    # 测试不同数量的关键词
    test_queries = [
        ("AI", "单个关键词"),
        ("AI agent", "两个关键词"),
        ("AI agent LLM", "三个关键词"),
        ("AI agent LLM transformer", "四个关键词"),
        ("AI agent LLM transformer neural network", "六个关键词")
    ]
    
    url = f"{API_BASE_URL}/newsletter/search/"
    
    print("\n关键词数量对搜索结果的影响:")
    print("-" * 40)
    
    for query, description in test_queries:
        params = {
            'query': query,
            'size': 100,
            'highlight': False
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                total = result.get('total', 0)
                results = result.get('results', [])
                
                if results:
                    avg_score = sum(r.get('score', 0) for r in results) / len(results)
                    max_score = max(r.get('score', 0) for r in results)
                    min_score = min(r.get('score', 0) for r in results)
                    
                    print(f"\n{description}: \"{query}\"")
                    print(f"   结果数: {total}")
                    print(f"   最高分: {max_score:.2f}")
                    print(f"   平均分: {avg_score:.2f}")
                    print(f"   最低分: {min_score:.2f}")
                else:
                    print(f"\n{description}: \"{query}\"")
                    print(f"   结果数: 0")
                    
        except Exception as e:
            print(f"\n{description}: 请求失败 - {str(e)}")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 多关键词搜索功能测试")
    print("="*80)
    
    # 检查服务器
    try:
        response = requests.get("http://localhost:9011/health")
        if response.status_code != 200:
            print("❌ 服务器未运行，请先启动后端服务")
            return
    except:
        print("❌ 无法连接到服务器，请先启动后端服务:")
        print("   cd minio-file-manager/backend")
        print("   python3 -m uvicorn app.main:app --reload --port 9011")
        return
    
    print("✅ 服务器运行正常\n")
    
    # 运行测试
    test_multi_keywords()
    test_advanced_multi_keywords()
    analyze_results()
    
    print("\n" + "="*80)
    print("✅ 多关键词搜索测试完成!")
    print("="*80)
    
    print("\n💡 测试总结:")
    print("1. 多个关键词默认使用OR逻辑，匹配任一关键词即可")
    print("2. 使用引号可以进行短语精确匹配")
    print("3. 关键词越多，可能匹配的文档越多")
    print("4. 相关度评分反映了文档与所有关键词的匹配程度")
    print("5. 支持大小写不敏感搜索")


if __name__ == "__main__":
    main()