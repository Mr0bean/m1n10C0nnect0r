#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的Tags功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


async def test_fixed_tags_feature():
    """测试修复后的tags功能"""
    
    # API基础URL
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 测试修复后的Tags功能")
        print("=" * 60)
        
        # 测试1: 空query + 空tags = match_all
        print("\n1️⃣ 测试空query + 空tags = match_all...")
        try:
            async with session.get(f"{base_url}/?query=&tags=") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query + 空tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: (空)")
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
        
        # 测试2: 空query + 有效tags
        print("\n2️⃣ 测试空query + 有效tags...")
        try:
            async with session.get(f"{base_url}/?query=&tags=ai") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 空query + 有效tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: ai")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了tags过滤
                    if data.get('total') < 423:
                        print("   ✅ 正确使用了tags过滤")
                    else:
                        print("   ⚠️  可能没有使用tags过滤")
                else:
                    print(f"❌ 空query + 有效tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 空query + 有效tags搜索异常: {str(e)}")
        
        # 测试3: 有效query + 空tags
        print("\n3️⃣ 测试有效query + 空tags...")
        try:
            async with session.get(f"{base_url}/?query=agent&tags=") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 有效query + 空tags搜索成功")
                    print(f"   查询词: agent")
                    print(f"   Tags: (空)")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了关键词搜索
                    if data.get('query') == 'agent':
                        print("   ✅ 正确使用了关键词搜索")
                    else:
                        print("   ⚠️  可能没有使用关键词搜索")
                else:
                    print(f"❌ 有效query + 空tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 有效query + 空tags搜索异常: {str(e)}")
        
        # 测试4: 有效query + 有效tags
        print("\n4️⃣ 测试有效query + 有效tags...")
        try:
            async with session.get(f"{base_url}/?query=agent&tags=ai") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 有效query + 有效tags搜索成功")
                    print(f"   查询词: agent")
                    print(f"   Tags: ai")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否同时使用了关键词搜索和tags过滤
                    if data.get('query') == 'agent' and data.get('tags') == ['ai']:
                        print("   ✅ 正确使用了关键词搜索 + tags过滤")
                    else:
                        print("   ⚠️  可能没有正确组合搜索")
                else:
                    print(f"❌ 有效query + 有效tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 有效query + 有效tags搜索异常: {str(e)}")
        
        # 测试5: 不存在的tags
        print("\n5️⃣ 测试不存在的tags...")
        try:
            async with session.get(f"{base_url}/?query=&tags=gpt-5") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 不存在tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: gpt-5")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    if data.get('total') == 0:
                        print("   ✅ 正确返回0个结果（标签不存在）")
                    else:
                        print("   ⚠️  返回了结果，可能有问题")
                else:
                    print(f"❌ 不存在tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 不存在tags搜索异常: {str(e)}")
        
        # 测试6: 多个tags
        print("\n6️⃣ 测试多个tags...")
        try:
            async with session.get(f"{base_url}/?query=&tags=ai&tags=Top") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 多个tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: ai, Top")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 显示前3个结果
                    results = data.get('results', [])
                    if results:
                        print("   前3个结果:")
                        for i, doc in enumerate(results[:3], 1):
                            print(f"   {i}. {doc.get('title', '无标题')} (评分: {doc.get('score', 0):.2f})")
                else:
                    print(f"❌ 多个tags搜索失败: {response.status}")
        except Exception as e:
            print(f"❌ 多个tags搜索异常: {str(e)}")
        
        # 测试7: POST接口 - 空tags
        print("\n7️⃣ 测试POST接口 - 空tags...")
        try:
            payload = {
                "query": "",
                "tags": [""],
                "size": 5
            }
            
            async with session.post(f"{base_url}/", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ POST接口空tags搜索成功")
                    print(f"   查询词: (空)")
                    print(f"   Tags: [\"\"]")
                    print(f"   返回文档数量: {data.get('total', 0)}")
                    print(f"   实际结果数量: {len(data.get('results', []))}")
                    
                    # 检查是否使用了match_all
                    if data.get('total') == 423:
                        print("   ✅ 正确使用了match_all，过滤了空tags")
                    else:
                        print("   ⚠️  可能没有正确处理空tags")
                else:
                    print(f"❌ POST接口空tags搜索失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ POST接口空tags搜索异常: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 修复后的Tags功能测试完成")


if __name__ == "__main__":
    print("🚀 开始测试修复后的Tags功能")
    asyncio.run(test_fixed_tags_feature())
