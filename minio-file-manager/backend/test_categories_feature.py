#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Categories功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


async def test_categories_feature():
    """测试categories功能"""
    
    # API基础URL
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 测试Categories功能")
        print("=" * 60)
        
        # 测试1: GET接口 - 基本categories功能
        print("\n1️⃣ 测试GET接口 - 基本categories功能...")
        try:
            # 不带categories的搜索
            async with session.get(f"{base_url}/?query=agent") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 不带categories搜索成功")
                    print(f"   查询词: agent")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示前3个结果
                    results = data.get('results', [])
                    if results:
                        print("   前3个结果:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 不带categories搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 不带categories搜索异常: {str(e)}")
        
        # 带categories的搜索
        try:
            async with session.get(f"{base_url}/?query=agent&categories=AI&categories=机器学习") as response:
                if response.status == 200:
                    data = await response.json()
                    print("\n✅ 带categories搜索成功")
                    print(f"   查询词: agent")
                    print(f"   Categories: AI, 机器学习")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示前3个结果
                    results = data.get('results', [])
                    if results:
                        print("   前3个结果:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 带categories搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 带categories搜索异常: {str(e)}")
        
        # 测试2: POST接口 - categories功能
        print("\n2️⃣ 测试POST接口 - categories功能...")
        try:
            payload = {
                "query": "GPT",
                "categories": ["AI", "LLM", "深度学习"],
                "size": 5
            }
            
            async with session.post(f"{base_url}/", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ POST接口categories搜索成功")
                    print(f"   查询词: GPT")
                    print(f"   Categories: AI, LLM, 深度学习")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示结果
                    results = data.get('results', [])
                    if results:
                        print("   搜索结果:")
                        for i, doc in enumerate(results, 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ POST接口categories搜索失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ POST接口categories搜索异常: {str(e)}")
        
        # 测试3: 高级搜索 - categories功能
        print("\n3️⃣ 测试高级搜索 - categories功能...")
        try:
            payload = {
                "query": "paper",
                "categories": ["研究", "论文"],
                "article_type": "newsletter",
                "size": 5
            }
            
            async with session.post(f"{base_url}/advanced", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 高级搜索categories功能成功")
                    print(f"   查询词: paper")
                    print(f"   Categories: 研究, 论文")
                    print(f"   文章类型: newsletter")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示过滤条件
                    filters = data.get('filters', {})
                    print(f"   过滤条件: {filters}")
                else:
                    print(f"❌ 高级搜索categories功能失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ 高级搜索categories功能异常: {str(e)}")
        
        # 测试4: 快速搜索 - categories功能
        print("\n4️⃣ 测试快速搜索 - categories功能...")
        try:
            async with session.get(f"{base_url}/quick?q=learning&categories=AI&categories=机器学习") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 快速搜索categories功能成功")
                    print(f"   原始查询词: {data.get('original_query', 'N/A')}")
                    print(f"   最终查询词: {data.get('query', 'N/A')}")
                    print(f"   Categories: {data.get('categories', [])}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示结果
                    results = data.get('results', [])
                    if results:
                        print("   搜索结果:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 快速搜索categories功能失败: {response.status}")
        except Exception as e:
            print(f"❌ 快速搜索categories功能异常: {str(e)}")
        
        # 测试5: 空query + categories
        print("\n5️⃣ 测试空query + categories...")
        try:
            async with session.get(f"{base_url}/?query=&categories=AI&categories=GPT") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query + categories搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Categories: AI, GPT")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
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
        
        # 测试6: 对比测试 - 验证categories确实影响了搜索结果
        print("\n6️⃣ 对比测试 - 验证categories影响...")
        try:
            # 只搜索"agent"
            async with session.get(f"{base_url}/?query=agent&size=3") as response1:
                if response1.status == 200:
                    data1 = await response1.json()
                    results1 = data1.get('results', [])
                    
                    # 搜索"agent" + categories
                    async with session.get(f"{base_url}/?query=agent&categories=AI&size=3") as response2:
                        if response2.status == 200:
                            data2 = await response2.json()
                            results2 = data2.get('results', [])
                            
                            print("✅ 对比测试完成")
                            print(f"   只搜索'agent': {len(results1)} 个结果")
                            print(f"   搜索'agent' + 'AI': {len(results2)} 个结果")
                            
                            # 检查结果是否不同
                            if len(results1) != len(results2):
                                print("   📊 结果数量不同，categories确实影响了搜索")
                            else:
                                print("   📊 结果数量相同，但相关度可能不同")
                            
                            # 显示第一个结果对比
                            if results1 and results2:
                                print(f"   第一个结果对比:")
                                print(f"   仅agent: {results1[0].get('title', 'N/A')} (评分: {results1[0].get('score', 0):.2f})")
                                print(f"   agent+AI: {results2[0].get('title', 'N/A')} (评分: {results2[0].get('score', 0):.2f})")
                        else:
                            print(f"❌ 带categories对比搜索失败: {response2.status}")
                else:
                    print(f"❌ 不带categories对比搜索失败: {response1.status}")
        except Exception as e:
            print(f"❌ 对比测试异常: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 Categories功能测试完成")


if __name__ == "__main__":
    print("🚀 开始测试Categories功能")
    asyncio.run(test_categories_feature())
