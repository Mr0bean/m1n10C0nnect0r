#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的文章索引和文档格式
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys


async def test_index_creation():
    """测试索引是否创建成功"""
    print("=" * 60)
    print("1. 检查索引创建")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 获取所有索引
        async with session.get("http://localhost:8000/api/v1/elasticsearch/indices") as resp:
            if resp.status == 200:
                indices = await resp.json()
                minio_articles_found = False
                for index in indices:
                    if index['index'] == 'minio_articles':
                        minio_articles_found = True
                        print(f"✅ 找到索引: minio_articles")
                        print(f"   文档数: {index.get('docsCount', 0)}")
                        print(f"   状态: {index.get('status', 'unknown')}")
                        break
                
                if not minio_articles_found:
                    print("❌ 未找到 minio_articles 索引")
                    print("   可能需要重启应用以创建索引")
            else:
                print(f"❌ 无法获取索引列表: {resp.status}")


async def test_upload_document():
    """测试上传文档到MinIO并索引到ES"""
    print("\n" + "=" * 60)
    print("2. 测试文档上传和索引")
    print("=" * 60)
    
    # 创建测试文档
    test_md_content = """# 深度学习入门教程

这是一篇关于深度学习的入门教程，将帮助您理解神经网络的基本概念。

## 什么是深度学习？

深度学习是机器学习的一个子领域，它使用多层神经网络来学习数据的复杂模式。
与传统的机器学习方法相比，深度学习能够自动从原始数据中提取特征。

## 神经网络的基本组成

1. **输入层**: 接收原始数据
2. **隐藏层**: 进行特征提取和转换
3. **输出层**: 产生最终预测结果

## 示例代码

```python
import tensorflow as tf
from tensorflow import keras

# 创建简单的神经网络
model = keras.Sequential([
    keras.layers.Dense(128, activation='relu', input_shape=(784,)),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(10, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])
```

## 深度学习的应用

- 计算机视觉
- 自然语言处理
- 语音识别
- 推荐系统

## 总结

深度学习正在改变我们处理复杂数据的方式，从图像识别到自然语言理解，
它的应用无处不在。掌握深度学习的基础知识将帮助您在AI时代保持竞争力。

标签: deep learning, neural network, tensorflow, machine learning, AI
作者: AI教程编辑部
发布日期: 2024-01-08
"""
    
    async with aiohttp.ClientSession() as session:
        # 创建测试bucket（如果不存在）
        bucket_name = "test-articles"
        
        # 创建bucket
        async with session.post(
            "http://localhost:8000/api/v1/buckets",
            json={"bucket_name": bucket_name}
        ) as resp:
            if resp.status in [200, 201]:
                print(f"✅ 创建或使用存储桶: {bucket_name}")
            elif resp.status == 409 or resp.status == 400:
                print(f"ℹ️  存储桶已存在: {bucket_name}")
            else:
                print(f"❌ 创建存储桶失败: {resp.status}")
                error_text = await resp.text()
                print(f"   错误: {error_text}")
                # 继续测试，因为桶可能已经存在
        
        # 设置bucket为公开
        async with session.put(
            f"http://localhost:8000/api/v1/buckets/{bucket_name}/make-public"
        ) as resp:
            if resp.status == 200:
                print(f"✅ 设置存储桶为公开")
            else:
                print(f"⚠️  设置公开失败，但继续测试")
        
        # 上传文档
        file_name = f"deep_learning_tutorial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 创建FormData
        data = aiohttp.FormData()
        data.add_field('file',
                      test_md_content.encode('utf-8'),
                      filename=file_name,
                      content_type='text/markdown')
        
        async with session.post(
            f"http://localhost:8000/api/v1/objects/{bucket_name}/upload",
            data=data
        ) as resp:
            if resp.status in [200, 201]:
                result = await resp.json()
                print(f"✅ 文件上传成功: {file_name}")
                print(f"   MinIO上传: {result.get('minio_upload', False)}")
                print(f"   ES索引: {result.get('es_indexed', False)}")
                if result.get('es_document_id'):
                    print(f"   文档ID: {result['es_document_id']}")
                if result.get('public_url'):
                    print(f"   公开URL: {result['public_url']}")
                if result.get('index_name'):
                    print(f"   索引名: {result['index_name']}")
                return result
            else:
                print(f"❌ 文件上传失败: {resp.status}")
                error_text = await resp.text()
                print(f"   错误: {error_text}")
                return None


async def test_search():
    """测试搜索功能"""
    print("\n" + "=" * 60)
    print("3. 测试搜索功能")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 搜索 "深度学习"
        search_query = "深度学习"
        
        async with session.get(
            f"http://localhost:8000/api/v1/elasticsearch/search",
            params={
                "index": "minio_articles",
                "query": search_query,
                "size": 10,
                "fuzzy": "true"
            }
        ) as resp:
            if resp.status == 200:
                results = await resp.json()
                if 'hits' in results:
                    total = results.get('total', {}).get('value', 0)
                    print(f"✅ 搜索 '{search_query}' 找到 {total} 个结果")
                    
                    if total > 0 and 'hits' in results:
                        for i, hit in enumerate(results['hits'][:3], 1):
                            doc = hit.get('_source', {})
                            print(f"\n   结果 {i}:")
                            print(f"   标题: {doc.get('title', '未知')}")
                            print(f"   分类: {doc.get('category', '未知')}")
                            print(f"   标签: {', '.join(doc.get('tags', []))}")
                            print(f"   字数: {doc.get('word_count', 0)}")
                            print(f"   评分: {hit.get('_score', 0):.2f}")
                else:
                    print(f"⚠️  搜索返回格式异常")
            else:
                print(f"❌ 搜索失败: {resp.status}")
                error_text = await resp.text()
                print(f"   错误: {error_text}")


async def test_document_structure():
    """测试文档结构是否符合新映射"""
    print("\n" + "=" * 60)
    print("4. 检查文档结构")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # 获取索引映射
        async with session.get(
            f"http://localhost:8000/api/v1/elasticsearch/indices/minio_articles/mapping"
        ) as resp:
            if resp.status == 200:
                mapping = await resp.json()
                
                # 预期的字段
                expected_fields = [
                    'id', 'title', 'summary', 'content', 'category', 'tags',
                    'author', 'publish_date', 'upload_time', 'last_modified',
                    'read_time', 'view_count', 'like_count', 'word_count',
                    'featured', 'member_only', 'is_published',
                    'bucket_name', 'object_name', 'file_path', 'minio_public_url',
                    'content_hash', 'file_type', 'file_size', 'content_type',
                    'metadata', 'description', 'keywords', 'searchable_content'
                ]
                
                # 检查映射结构
                if 'mappings' in mapping:
                    properties = mapping['mappings'].get('properties', {})
                elif 'minio_articles' in mapping:
                    properties = mapping['minio_articles'].get('mappings', {}).get('properties', {})
                else:
                    properties = {}
                
                if properties:
                    print(f"✅ 找到索引映射，包含 {len(properties)} 个字段")
                    
                    # 检查预期字段
                    missing_fields = []
                    for field in expected_fields:
                        if field not in properties:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"⚠️  缺少以下字段: {', '.join(missing_fields)}")
                    else:
                        print(f"✅ 所有预期字段都存在")
                    
                    # 检查中文分词器
                    title_analyzer = properties.get('title', {}).get('analyzer')
                    if title_analyzer in ['ik_max_word', 'ik_smart']:
                        print(f"✅ 标题字段使用IK分词器: {title_analyzer}")
                    else:
                        print(f"⚠️  标题字段未使用IK分词器: {title_analyzer}")
                else:
                    print(f"❌ 映射结构异常")
            else:
                print(f"❌ 无法获取索引映射: {resp.status}")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("测试新的文章索引和文档格式")
    print("=" * 60)
    
    # 1. 检查索引
    await test_index_creation()
    
    # 2. 上传文档
    upload_result = await test_upload_document()
    
    # 等待ES索引刷新
    if upload_result and upload_result.get('es_indexed'):
        print("\n⏳ 等待3秒让ES索引刷新...")
        await asyncio.sleep(3)
    
    # 3. 测试搜索
    await test_search()
    
    # 4. 检查文档结构
    await test_document_structure()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())