#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Newsletter搜索API端点脚本
"""

import requests
import json
from datetime import datetime

# API基础URL
API_BASE_URL = "http://localhost:9011/api/v1"

def test_quick_search():
    """测试快速搜索API"""
    print("\n" + "="*60)
    print("🔍 测试快速搜索API")
    print("="*60)
    
    url = f"{API_BASE_URL}/newsletter/search/quick"
    
    test_queries = ["AI", "agent", "GPT", "LLM", "深度学习"]
    
    for query in test_queries:
        print(f"\n搜索: '{query}'")
        print("-" * 40)
        
        try:
            response = requests.get(url, params={"q": query})
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功! 找到 {data.get('total', 0)} 个结果")
                
                # 显示前3个结果
                for i, result in enumerate(data.get('results', [])[:3], 1):
                    print(f"\n  {i}. {result.get('title', 'N/A')[:60]}...")
                    print(f"     评分: {result.get('score', 0):.2f}")
                    
                    # 显示高亮
                    highlight = result.get('highlight', {})
                    if highlight.get('title'):
                        print(f"     高亮: {highlight['title'][0][:80]}...")
            else:
                print(f"❌ 错误: HTTP {response.status_code}")
                print(f"     {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")


def test_full_search():
    """测试完整搜索API"""
    print("\n" + "="*60)
    print("📝 测试完整搜索API")
    print("="*60)
    
    url = f"{API_BASE_URL}/newsletter/search/"
    
    # 测试不同的参数组合
    test_cases = [
        {
            "name": "基本搜索",
            "params": {
                "query": "machine learning",
                "from": 0,
                "size": 5,
                "sort_by": "_score",
                "highlight": True
            }
        },
        {
            "name": "分页搜索",
            "params": {
                "query": "AI",
                "from": 10,
                "size": 5,
                "sort_by": "_score",
                "highlight": False
            }
        },
        {
            "name": "按大小排序",
            "params": {
                "query": "neural",
                "from": 0,
                "size": 5,
                "sort_by": "size",
                "highlight": True
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.get(url, params=test_case['params'])
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ 成功! 找到 {data.get('total', 0)} 个结果")
                    print(f"   查询: {data.get('query')}")
                    print(f"   返回: {len(data.get('results', []))} 条")
                else:
                    print(f"⚠️  搜索失败: {data.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")


def test_advanced_search():
    """测试高级搜索API"""
    print("\n" + "="*60)
    print("🔬 测试高级搜索API")
    print("="*60)
    
    url = f"{API_BASE_URL}/newsletter/search/advanced"
    
    test_cases = [
        {
            "name": "仅关键词搜索",
            "body": {
                "query": "transformer",
                "from": 0,
                "size": 5,
                "sort_by": "_score"
            }
        },
        {
            "name": "按类型过滤",
            "body": {
                "article_type": "markdown",
                "from": 0,
                "size": 5,
                "sort_by": "_score"
            }
        },
        {
            "name": "组合条件",
            "body": {
                "query": "AI",
                "min_wordcount": 100,
                "max_wordcount": 2000,
                "from": 0,
                "size": 5,
                "sort_by": "size"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print("-" * 40)
        print(f"请求体: {json.dumps(test_case['body'], ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(
                url,
                json=test_case['body'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ 成功! 找到 {data.get('total', 0)} 个结果")
                    
                    # 显示应用的过滤条件
                    filters = data.get('filters', {})
                    active_filters = {k: v for k, v in filters.items() if v is not None}
                    if active_filters:
                        print("应用的过滤条件:")
                        for key, value in active_filters.items():
                            print(f"  - {key}: {value}")
                else:
                    print(f"⚠️  搜索失败: {data.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")


def check_server():
    """检查服务器是否运行"""
    try:
        # 修复健康检查URL
        health_url = "http://localhost:9011/health"
        response = requests.get(health_url)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {str(e)}")
        print(f"   请确保后端服务在 http://localhost:9011 运行")
        return False


def main():
    """主函数"""
    print("="*80)
    print("🚀 Newsletter搜索API测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API地址: {API_BASE_URL}")
    print("="*80)
    
    # 检查服务器
    if not check_server():
        print("\n请先启动后端服务:")
        print("  cd minio-file-manager/backend")
        print("  python -m uvicorn app.main:app --reload --port 9011")
        return
    
    # 运行测试
    test_quick_search()
    test_full_search()
    test_advanced_search()
    
    print("\n" + "="*80)
    print("✅ API测试完成!")
    print("="*80)
    
    # 显示API文档地址
    print("\n📚 API文档地址:")
    print(f"  - Swagger UI: {API_BASE_URL[:API_BASE_URL.rfind('/')]}/docs")
    print(f"  - ReDoc: {API_BASE_URL[:API_BASE_URL.rfind('/')]}/redoc")


if __name__ == "__main__":
    main()