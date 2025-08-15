#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试空query+categories不再使用match_all的功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


async def test_empty_query_categories():
    """测试空query+categories不再使用match_all"""
    
    # API基础URL
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 测试空query+categories不再使用match_all")
        print("=" * 60)
        
        # 测试1: 空query + categories
        print("\n1️⃣ 测试空query + categories...")
        try:
            async with session.get(f"{base_url}/?query=&categories=AI&categories=GPT") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query + categories搜索成功")
                    print(f"   原始query: {data.get('original_query', 'N/A')}")
                    print(f"   最终query: {data.get('query', 'N/A')}")
                    print(f"   Categories: {data.get('categories', [])}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    if data.get('query') == '':
                        print("   ⚠️  使用了match_all查询")
                    else:
                        print("   ✅ 使用了关键词查询，不是match_all")
                    
                    # 显示前3个结果
                    results = data.get('results', [])
                    if results:
                        print("   前3个结果:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 空query + categories搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 空query + categories搜索异常: {str(e)}")
        
        # 测试2: 对比 - 纯空query
        print("\n2️⃣ 对比测试 - 纯空query...")
        try:
            async with session.get(f"{base_url}/?query=") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 纯空query搜索成功")
                    print(f"   最终query: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    if data.get('query') == '':
                        print("   ✅ 使用了match_all查询（正确）")
                    else:
                        print("   ⚠️  使用了关键词查询，应该是match_all")
                else:
                    print(f"❌ 纯空query搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 纯空query搜索异常: {str(e)}")
        
        # 测试3: POST接口 - 空query + categories
        print("\n3️⃣ 测试POST接口 - 空query + categories...")
        try:
            payload = {
                "query": "",
                "categories": ["AI", "机器学习"],
                "size": 5
            }
            
            async with session.post(f"{base_url}/", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ POST接口空query + categories搜索成功")
                    print(f"   原始query: {data.get('original_query', 'N/A')}")
                    print(f"   最终query: {data.get('query', 'N/A')}")
                    print(f"   Categories: {data.get('categories', [])}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    if data.get('query') == '':
                        print("   ⚠️  使用了match_all查询")
                    else:
                        print("   ✅ 使用了关键词查询，不是match_all")
                else:
                    print(f"❌ POST接口空query + categories搜索失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ POST接口空query + categories搜索异常: {str(e)}")
        
        # 测试4: 高级搜索 - 空query + categories
        print("\n4️⃣ 测试高级搜索 - 空query + categories...")
        try:
            payload = {
                "query": "",
                "categories": ["AI", "GPT"],
                "article_type": "newsletter",
                "size": 5
            }
            
            async with session.post(f"{base_url}/advanced", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 高级搜索空query + categories成功")
                    print(f"   原始query: {data.get('filters', {}).get('original_query', 'N/A')}")
                    print(f"   最终query: {data.get('filters', {}).get('query', 'N/A')}")
                    print(f"   Categories: {data.get('filters', {}).get('categories', [])}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    filters = data.get('filters', {})
                    if filters.get('query') == '':
                        print("   ⚠️  使用了match_all查询")
                    else:
                        print("   ✅ 使用了关键词查询，不是match_all")
                else:
                    print(f"❌ 高级搜索空query + categories失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ 高级搜索空query + categories异常: {str(e)}")
        
        # 测试5: 快速搜索 - 空query + categories
        print("\n5️⃣ 测试快速搜索 - 空query + categories...")
        try:
            async with session.get(f"{base_url}/quick?q=&categories=AI&categories=GPT") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 快速搜索空query + categories成功")
                    print(f"   原始query: {data.get('original_query', 'N/A')}")
                    print(f"   最终query: {data.get('query', 'N/A')}")
                    print(f"   Categories: {data.get('categories', [])}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    if data.get('query') == '':
                        print("   ⚠️  使用了match_all查询")
                    else:
                        print("   ✅ 使用了关键词查询，不是match_all")
                else:
                    print(f"❌ 快速搜索空query + categories失败: {response.status}")
        except Exception as e:
            print(f"❌ 快速搜索空query + categories异常: {str(e)}")
        
        # 测试6: 验证搜索结果的相关性
        print("\n6️⃣ 验证搜索结果的相关性...")
        try:
            # 搜索包含AI和GPT关键词的文档
            async with session.get(f"{base_url}/?query=AI GPT&size=3") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 直接搜索'AI GPT'成功")
                    print(f"   查询词: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {len(data.get('results', []))}")
                    
                    # 显示结果
                    results = data.get('results', [])
                    if results:
                        print("   搜索结果:")
                        for i, doc in enumerate(results, 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 直接搜索'AI GPT'失败: {response.status}")
        except Exception as e:
            print(f"❌ 直接搜索'AI GPT'异常: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 空query+categories功能测试完成")


if __name__ == "__main__":
    print("🚀 开始测试空query+categories不再使用match_all功能")
    asyncio.run(test_empty_query_categories())
