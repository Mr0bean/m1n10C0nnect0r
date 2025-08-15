#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试空query返回所有文档的功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


async def test_empty_query():
    """测试空query返回所有文档"""
    
    # API基础URL
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 测试空query返回所有文档功能")
        print("=" * 60)
        
        # 测试1: 空query
        print("\n1️⃣ 测试空query...")
        try:
            async with session.get(f"{base_url}/?query=") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query查询成功")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示前5个结果
                    results = data.get('results', [])
                    if results:
                        print("   前5个文档:")
                        for i, doc in enumerate(results[:5], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (ID: {doc.get('id', 'N/A')})")
                    else:
                        print("   ⚠️  没有返回任何文档")
                else:
                    print(f"❌ 空query查询失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ 空query查询异常: {str(e)}")
        
        # 测试2: 空格query
        print("\n2️⃣ 测试空格query...")
        try:
            async with session.get(f"{base_url}/?query=%20") as response:  # %20是空格
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空格query查询成功")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                else:
                    print(f"❌ 空格query查询失败: {response.status}")
        except Exception as e:
            print(f"❌ 空格query查询异常: {str(e)}")
        
        # 测试3: 有query的情况（对比）
        print("\n3️⃣ 测试有query的情况（对比）...")
        try:
            async with session.get(f"{base_url}/?query=ai") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 有query查询成功")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示前3个结果
                    results = data.get('results', [])
                    if results:
                        print("   前3个匹配文档:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 有query查询失败: {response.status}")
        except Exception as e:
            print(f"❌ 有query查询异常: {str(e)}")
        
        # 测试4: 空query + 分页
        print("\n4️⃣ 测试空query + 分页...")
        try:
            async with session.get(f"{base_url}/?query=&from=0&size=5") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query分页查询成功")
                    print(f"   总文档数量: {data.get('total', 0)}")
                    print(f"   当前页结果数量: {len(data.get('results', []))}")
                    print(f"   分页参数: from={data.get('from', 0)}, size={data.get('size', 0)}")
                    
                    # 显示结果
                    results = data.get('results', [])
                    if results:
                        print("   当前页文档:")
                        for i, doc in enumerate(results, 1):
                            print(f"   {i}. {doc.get('title', '无标题')}")
                else:
                    print(f"❌ 空query分页查询失败: {response.status}")
        except Exception as e:
            print(f"❌ 空query分页查询异常: {str(e)}")
        
        # 测试5: 空query + 排序
        print("\n5️⃣ 测试空query + 按大小排序...")
        try:
            async with session.get(f"{base_url}/?query=&sort_by=size&size=5") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query排序查询成功")
                    print(f"   返回文档数量: {len(data.get('results', []))}")
                    
                    # 显示按大小排序的结果
                    results = data.get('results', [])
                    if results:
                        print("   按大小排序的文档:")
                        for i, doc in enumerate(results, 1):
                            size = doc.get('size', 0)
                            size_kb = size / 1024 if size > 0 else 0
                            print(f"   {i}. {doc.get('title', '无标题')} ({size_kb:.1f}KB)")
                else:
                    print(f"❌ 空query排序查询失败: {response.status}")
        except Exception as e:
            print(f"❌ 空query排序查询异常: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 空query功能测试完成")


async def test_advanced_search_empty_query():
    """测试高级搜索中的空query功能"""
    
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("\n🔍 测试高级搜索中的空query功能")
        print("=" * 60)
        
        # 测试高级搜索空query
        print("\n1️⃣ 测试高级搜索空query...")
        try:
            payload = {
                "query": "",  # 空query
                "from": 0,
                "size": 10
            }
            
            async with session.post(f"{base_url}/advanced", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 高级搜索空query成功")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示过滤条件
                    filters = data.get('filters', {})
                    print(f"   过滤条件: {filters}")
                else:
                    print(f"❌ 高级搜索空query失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ 高级搜索空query异常: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 高级搜索空query功能测试完成")


if __name__ == "__main__":
    print("🚀 开始测试空query返回所有文档功能")
    
    # 测试基本搜索的空query功能
    asyncio.run(test_empty_query())
    
    # 测试高级搜索的空query功能
    asyncio.run(test_advanced_search_empty_query())
