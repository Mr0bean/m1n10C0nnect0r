#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Tags作为搜索词的功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


async def test_tags_as_search_terms():
    """测试tags作为搜索词的功能"""
    
    # API基础URL
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 测试Tags作为搜索词的功能")
        print("=" * 60)
        
        # 测试1: 空query + tags=GPT
        print("\n1️⃣ 测试空query + tags=GPT...")
        try:
            async with session.get(f"{base_url}/?query=&tags=GPT") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query + tags=GPT搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: GPT")
                    print(f"   最终查询: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了GPT作为搜索词
                    if data.get('query') == 'GPT':
                        print("   ✅ 正确使用GPT作为搜索词")
                    else:
                        print(f"   ⚠️  最终查询词: {data.get('query')}")
                else:
                    print(f"❌ 空query + tags=GPT搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 空query + tags=GPT搜索异常: {str(e)}")
        
        # 测试2: query=AI + tags=GPT
        print("\n2️⃣ 测试query=AI + tags=GPT...")
        try:
            async with session.get(f"{base_url}/?query=AI&tags=GPT") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ query=AI + tags=GPT搜索成功")
                    print(f"   查询词: AI")
                    print(f"   Tags: GPT")
                    print(f"   最终查询: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了"AI GPT"作为搜索词
                    if data.get('query') == 'AI GPT':
                        print("   ✅ 正确使用AI GPT作为搜索词")
                    else:
                        print(f"   ⚠️  最终查询词: {data.get('query')}")
                else:
                    print(f"❌ query=AI + tags=GPT搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ query=AI + tags=GPT搜索异常: {str(e)}")
        
        # 测试3: 空query + 空tags = match_all
        print("\n3️⃣ 测试空query + 空tags = match_all...")
        try:
            async with session.get(f"{base_url}/?query=&tags=") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query + 空tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: (空)")
                    print(f"   最终查询: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    if data.get('total') == 423:
                        print("   ✅ 正确使用了match_all，返回所有文档")
                    else:
                        print("   ⚠️  可能没有使用match_all")
                else:
                    print(f"❌ 空query + 空tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 空query + 空tags搜索异常: {str(e)}")
        
        # 测试4: 多个tags
        print("\n4️⃣ 测试多个tags...")
        try:
            async with session.get(f"{base_url}/?query=&tags=GPT&tags=AI") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 多个tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: GPT, AI")
                    print(f"   最终查询: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了"GPT AI"作为搜索词
                    if data.get('query') == 'GPT AI':
                        print("   ✅ 正确使用GPT AI作为搜索词")
                    else:
                        print(f"   ⚠️  最终查询词: {data.get('query')}")
                else:
                    print(f"❌ 多个tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 多个tags搜索异常: {str(e)}")
        
        # 测试5: query + categories + tags
        print("\n5️⃣ 测试query + categories + tags...")
        try:
            async with session.get(f"{base_url}/?query=agent&categories=AI&tags=GPT") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ query + categories + tags搜索成功")
                    print(f"   查询词: agent")
                    print(f"   Categories: AI")
                    print(f"   Tags: GPT")
                    print(f"   最终查询: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了"agent AI GPT"作为搜索词
                    if data.get('query') == 'agent AI GPT':
                        print("   ✅ 正确使用agent AI GPT作为搜索词")
                    else:
                        print(f"   ⚠️  最终查询词: {data.get('query')}")
                else:
                    print(f"❌ query + categories + tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ query + categories + tags搜索异常: {str(e)}")
        
        # 测试6: POST接口测试
        print("\n6️⃣ 测试POST接口...")
        try:
            payload = {
                "query": "machine",
                "tags": ["learning", "AI"],
                "size": 5
            }
            
            async with session.post(f"{base_url}/", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ POST接口搜索成功")
                    print(f"   查询词: machine")
                    print(f"   Tags: learning, AI")
                    print(f"   最终查询: {data.get('query', 'N/A')}")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了"machine learning AI"作为搜索词
                    if data.get('query') == 'machine learning AI':
                        print("   ✅ 正确使用machine learning AI作为搜索词")
                    else:
                        print(f"   ⚠️  最终查询词: {data.get('query')}")
                else:
                    print(f"❌ POST接口搜索失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ POST接口搜索异常: {str(e)}")
        
        # 测试7: 显示搜索结果示例
        print("\n7️⃣ 显示搜索结果示例...")
        try:
            async with session.get(f"{base_url}/?query=&tags=GPT&size=3") as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    if results:
                        print("   GPT相关文章示例:")
                        for i, doc in enumerate(results, 1):
                            title = doc.get('title', '无标题')
                            score = doc.get('score', 0)
                            print(f"   {i}. {title} (评分: {score:.2f})")
                    else:
                        print("   没有找到相关结果")
                else:
                    print(f"❌ 获取示例失败: {response.status}")
        except Exception as e:
            print(f"❌ 获取示例异常: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 Tags作为搜索词功能测试完成")


if __name__ == "__main__":
    print("🚀 开始测试Tags作为搜索词功能")
    asyncio.run(test_tags_as_search_terms())
