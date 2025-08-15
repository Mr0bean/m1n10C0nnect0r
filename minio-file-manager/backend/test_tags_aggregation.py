#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Tags聚合接口
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


async def test_tags_aggregation():
    """测试tags聚合接口"""
    
    # API基础URL
    base_url = "http://localhost:9011/api/v1/newsletter/search"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 测试Tags聚合接口")
        print("=" * 50)
        
        # 测试1: 基本聚合
        print("\n1️⃣ 测试基本tags聚合...")
        try:
            async with session.get(f"{base_url}/tags/aggregate") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 基本聚合成功")
                    print(f"   总tags数量: {data.get('total_tags', 0)}")
                    print(f"   总文档数量: {data.get('total_documents', 0)}")
                    
                    # 显示前10个tags
                    tags = data.get('tags', [])
                    if tags:
                        print("   Top 10 Tags:")
                        for i, tag_info in enumerate(tags[:10], 1):
                            print(f"   {i:2d}. {tag_info['tag']}: {tag_info['count']} 篇文章")
                    else:
                        print("   ⚠️  没有找到任何tags")
                else:
                    print(f"❌ 基本聚合失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
        except Exception as e:
            print(f"❌ 基本聚合异常: {str(e)}")
        
        # 测试2: 限制返回数量
        print("\n2️⃣ 测试限制返回数量...")
        try:
            async with session.get(f"{base_url}/tags/aggregate?size=5") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 限制数量聚合成功")
                    print(f"   返回tags数量: {data.get('total_tags', 0)}")
                    
                    tags = data.get('tags', [])
                    if tags:
                        print("   返回的Tags:")
                        for i, tag_info in enumerate(tags, 1):
                            print(f"   {i}. {tag_info['tag']}: {tag_info['count']} 篇文章")
                else:
                    print(f"❌ 限制数量聚合失败: {response.status}")
        except Exception as e:
            print(f"❌ 限制数量聚合异常: {str(e)}")
        
        # 测试3: 设置最小文档数量阈值
        print("\n3️⃣ 测试最小文档数量阈值...")
        try:
            async with session.get(f"{base_url}/tags/aggregate?min_doc_count=2") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 阈值过滤聚合成功")
                    print(f"   过滤后tags数量: {data.get('total_tags', 0)}")
                    
                    tags = data.get('tags', [])
                    if tags:
                        print("   过滤后的Tags (至少2篇文章):")
                        for i, tag_info in enumerate(tags[:10], 1):
                            print(f"   {i:2d}. {tag_info['tag']}: {tag_info['count']} 篇文章")
                    else:
                        print("   ⚠️  没有找到符合条件的tags")
                else:
                    print(f"❌ 阈值过滤聚合失败: {response.status}")
        except Exception as e:
            print(f"❌ 阈值过滤聚合异常: {str(e)}")
        
        # 测试4: 组合参数
        print("\n4️⃣ 测试组合参数...")
        try:
            async with session.get(f"{base_url}/tags/aggregate?size=10&min_doc_count=1") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 组合参数聚合成功")
                    print(f"   返回tags数量: {data.get('total_tags', 0)}")
                    
                    tags = data.get('tags', [])
                    if tags:
                        print("   组合参数返回的Tags:")
                        for i, tag_info in enumerate(tags, 1):
                            print(f"   {i:2d}. {tag_info['tag']}: {tag_info['count']} 篇文章")
                else:
                    print(f"❌ 组合参数聚合失败: {response.status}")
        except Exception as e:
            print(f"❌ 组合参数聚合异常: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Tags聚合接口测试完成")


async def test_es_connection():
    """测试ES连接"""
    print("🔍 测试Elasticsearch连接...")
    
    try:
        import requests
        response = requests.get("http://localhost:9200/_cluster/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ ES连接正常 - 状态: {health.get('status')}")
            print(f"   集群名称: {health.get('cluster_name')}")
            print(f"   节点数量: {health.get('number_of_nodes')}")
        else:
            print(f"❌ ES连接失败: {response.status_code}")
    except Exception as e:
        print(f"❌ ES连接异常: {str(e)}")


if __name__ == "__main__":
    print("🚀 开始测试Tags聚合功能")
    
    # 先测试ES连接
    asyncio.run(test_es_connection())
    
    # 然后测试API接口
    asyncio.run(test_tags_aggregation())
