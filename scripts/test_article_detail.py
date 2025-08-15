#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试根据ID获取文章详情的API
"""

import asyncio
import aiohttp
import json
from typing import Optional

# API基础URL
BASE_URL = "http://localhost:8000/api/newsletter/search"


async def search_articles(query: str = "AI") -> Optional[str]:
    """先搜索文章，获取一个文章ID"""
    url = f"{BASE_URL}/quick"
    params = {"q": query}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("results"):
                        # 返回第一个文章的ID
                        return result["results"][0].get("id")
                    else:
                        print("搜索没有返回结果")
                        return None
                else:
                    print(f"搜索失败: {response.status}")
                    return None
        except Exception as e:
            print(f"搜索请求失败: {e}")
            return None


async def get_article_by_id(article_id: str):
    """根据ID获取文章详情"""
    url = f"{BASE_URL}/{article_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"\n获取文章详情: ID = {article_id}")
            print(f"请求URL: {url}")
            print("=" * 50)
            
            async with session.get(url) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("✅ 获取成功!")
                    print(f"状态码: {response.status}")
                    
                    if result.get("success"):
                        article = result.get("article", {})
                        
                        # 打印文章基本信息
                        print("\n📄 文章信息:")
                        print(f"  - ID: {article.get('id')}")
                        print(f"  - 标题: {article.get('title')}")
                        print(f"  - 副标题: {article.get('subtitle')}")
                        print(f"  - 类型: {article.get('document_type')}")
                        print(f"  - 大小: {article.get('size')} bytes")
                        print(f"  - MinIO URL: {article.get('minio_public_url')}")
                        
                        # 打印内容预览
                        content = article.get('content') or article.get('content_full', '')
                        if content:
                            preview = content[:200] + '...' if len(content) > 200 else content
                            print(f"\n📝 内容预览:")
                            print(f"  {preview}")
                        
                        # 打印标签
                        tags = article.get('tags', [])
                        if tags:
                            print(f"\n🏷️ 标签: {', '.join(tags)}")
                        
                        # 打印统计信息
                        statistics = article.get('statistics', {})
                        if statistics:
                            print(f"\n📊 统计信息:")
                            for key, value in statistics.items():
                                print(f"  - {key}: {value}")
                        
                        # 打印是否有embeddings
                        if article.get('has_embeddings'):
                            print(f"\n✨ 包含向量嵌入")
                        
                    else:
                        print(f"❌ 响应表示失败: {result.get('error')}")
                    
                elif response.status == 404:
                    print(f"❌ 文章不存在: {article_id}")
                    print(f"错误信息: {result.get('detail')}")
                    
                else:
                    print(f"❌ 请求失败")
                    print(f"状态码: {response.status}")
                    print(f"错误信息: {result}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")


async def test_invalid_id():
    """测试无效的文章ID"""
    invalid_id = "invalid_article_id_12345"
    print(f"\n测试无效ID: {invalid_id}")
    print("=" * 50)
    await get_article_by_id(invalid_id)


async def main():
    print("🔍 测试根据ID获取文章详情API")
    print("=" * 50)
    
    # 1. 先搜索获取一个有效的文章ID
    print("\n步骤1: 搜索文章获取ID...")
    article_id = await search_articles("AI")
    
    if article_id:
        # 2. 使用获取到的ID测试详情接口
        print(f"\n步骤2: 获取文章详情 (ID: {article_id})...")
        await get_article_by_id(article_id)
    else:
        print("无法获取文章ID，请确保:")
        print("1. 后端服务正在运行")
        print("2. Elasticsearch中有数据")
    
    # 3. 测试无效ID的情况
    print("\n步骤3: 测试无效ID...")
    await test_invalid_id()


if __name__ == "__main__":
    asyncio.run(main())