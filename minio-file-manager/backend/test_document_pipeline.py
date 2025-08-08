#!/usr/bin/env python3
"""
测试文档处理管道功能
测试MD/HTML文件上传到MinIO并同时索引到Elasticsearch
"""

import asyncio
import aiohttp
import json
from pathlib import Path
import tempfile

API_BASE_URL = "http://localhost:9011/api/v1"


async def create_test_files():
    """创建测试文件"""
    test_files = []
    
    # 创建测试Markdown文件
    md_content = """# 项目文档

## 概述
这是一个测试项目的技术文档。

## 功能特性
- 支持Markdown格式
- 自动索引到Elasticsearch
- 支持模糊搜索
- 公开URL访问

## 代码示例
```python
def hello_world():
    print("Hello, World!")
```

## 链接
- [项目主页](https://example.com)
- [API文档](https://api.example.com)

## 总结
这个文档展示了pipeline的功能。
"""
    
    md_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    md_file.write(md_content)
    md_file.close()
    test_files.append(('markdown', md_file.name, 'test_project.md'))
    
    # 创建测试HTML文件
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>测试HTML文档</title>
    <meta name="description" content="这是一个测试HTML文档，用于演示pipeline功能">
    <meta name="keywords" content="测试,HTML,pipeline,elasticsearch">
    <meta name="author" content="测试作者">
</head>
<body>
    <h1>HTML文档测试</h1>
    <p>这是一个HTML格式的文档，会被自动处理并索引。</p>
    <h2>功能列表</h2>
    <ul>
        <li>自动提取文本内容</li>
        <li>解析meta标签</li>
        <li>生成搜索索引</li>
    </ul>
    <p>访问链接：<a href="https://example.org">示例网站</a></p>
</body>
</html>"""
    
    html_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    html_file.write(html_content)
    html_file.close()
    test_files.append(('html', html_file.name, 'test_document.html'))
    
    # 创建普通文本文件（不会被pipeline处理）
    txt_content = """这是一个普通的文本文件。
它不会被pipeline处理，只会上传到MinIO。"""
    
    txt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    txt_file.write(txt_content)
    txt_file.close()
    test_files.append(('text', txt_file.name, 'normal_text.txt'))
    
    return test_files


async def ensure_bucket_exists(session, bucket_name):
    """确保存储桶存在"""
    # 检查存储桶是否存在
    async with session.get(f"{API_BASE_URL}/buckets") as resp:
        if resp.status == 200:
            buckets = await resp.json()
            if not any(b['name'] == bucket_name for b in buckets):
                # 创建存储桶
                async with session.post(
                    f"{API_BASE_URL}/buckets",
                    json={"bucket_name": bucket_name}
                ) as create_resp:
                    if create_resp.status in [200, 201]:
                        print(f"✅ 创建存储桶: {bucket_name}")
                    else:
                        print(f"❌ 创建存储桶失败: {await create_resp.text()}")
            else:
                print(f"✅ 存储桶已存在: {bucket_name}")


async def upload_file(session, bucket_name, file_path, object_name):
    """上传文件到MinIO"""
    with open(file_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=object_name)
        
        async with session.post(
            f"{API_BASE_URL}/objects/{bucket_name}/upload",
            data=data,
            params={'object_name': object_name, 'use_pipeline': 'true'}
        ) as resp:
            if resp.status in [200, 201]:
                result = await resp.json()
                return result
            else:
                print(f"❌ 上传失败: {await resp.text()}")
                return None


async def search_documents(session, query, fuzzy=True):
    """搜索文档"""
    params = {
        'query': query,
        'fuzzy': str(fuzzy).lower(),
        'size': 10
    }
    
    async with session.get(
        f"{API_BASE_URL}/documents/search",
        params=params
    ) as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print(f"❌ 搜索失败: {await resp.text()}")
            return None


async def get_similar_documents(session, document_id):
    """获取相似文档"""
    async with session.get(
        f"{API_BASE_URL}/documents/similar/{document_id}",
        params={'size': 5}
    ) as resp:
        if resp.status == 200:
            return await resp.json()
        elif resp.status == 404:
            print(f"❌ 文档未找到: {document_id}")
            return None
        else:
            print(f"❌ 获取相似文档失败: {await resp.text()}")
            return None


async def get_document_stats(session):
    """获取文档统计"""
    async with session.get(f"{API_BASE_URL}/documents/stats") as resp:
        if resp.status == 200:
            return await resp.json()
        else:
            print(f"❌ 获取统计失败: {await resp.text()}")
            return None


async def main():
    """主测试流程"""
    print("=" * 60)
    print("测试文档处理管道（Pipeline）")
    print("=" * 60)
    
    bucket_name = "test-documents"
    
    async with aiohttp.ClientSession() as session:
        # 1. 确保存储桶存在
        print("\n1. 准备存储桶")
        print("-" * 40)
        await ensure_bucket_exists(session, bucket_name)
        
        # 2. 创建并上传测试文件
        print("\n2. 上传测试文件")
        print("-" * 40)
        test_files = await create_test_files()
        uploaded_docs = []
        
        for file_type, file_path, object_name in test_files:
            print(f"\n上传 {file_type} 文件: {object_name}")
            result = await upload_file(session, bucket_name, file_path, object_name)
            if result:
                print(f"  ✅ 上传成功")
                print(f"  📦 存储桶: {result.get('bucket')}")
                print(f"  📄 对象名: {result.get('object_name')}")
                if result.get('es_indexed'):
                    print(f"  🔍 已索引到ES: {result.get('es_document_id')}")
                    uploaded_docs.append(result.get('es_document_id'))
                if result.get('public_url'):
                    print(f"  🌐 公开URL: {result.get('public_url')}")
                print(f"  💬 消息: {result.get('message', '上传成功')}")
            
            # 清理临时文件
            Path(file_path).unlink()
        
        # 等待ES索引
        print("\n⏳ 等待Elasticsearch索引...")
        await asyncio.sleep(2)
        
        # 3. 测试搜索功能
        print("\n3. 测试文档搜索")
        print("-" * 40)
        
        # 精确搜索
        print("\n📍 精确搜索: 'Elasticsearch'")
        search_result = await search_documents(session, "Elasticsearch", fuzzy=False)
        if search_result:
            print(f"  找到 {search_result['total']} 个文档")
            for doc in search_result['documents'][:3]:
                print(f"  - {doc.get('title', doc.get('object_name'))}")
                print(f"    评分: {doc.get('_score', 0):.2f}")
                if '_highlight' in doc:
                    print(f"    高亮: {doc['_highlight']}")
        
        # 模糊搜索
        print("\n🔍 模糊搜索: 'elasicsearch' (故意拼错)")
        fuzzy_result = await search_documents(session, "elasicsearch", fuzzy=True)
        if fuzzy_result:
            print(f"  找到 {fuzzy_result['total']} 个文档（通过模糊匹配）")
            for doc in fuzzy_result['documents'][:3]:
                print(f"  - {doc.get('title', doc.get('object_name'))}")
        
        # 4. 测试相似文档推荐
        if uploaded_docs:
            print("\n4. 测试相似文档推荐")
            print("-" * 40)
            doc_id = uploaded_docs[0]
            print(f"\n获取与文档 {doc_id[:8]}... 相似的文档")
            similar = await get_similar_documents(session, doc_id)
            if similar:
                print(f"  找到 {len(similar['similar_documents'])} 个相似文档")
                for doc in similar['similar_documents']:
                    print(f"  - {doc.get('title', doc.get('object_name'))}")
                    print(f"    相似度评分: {doc.get('_score', 0):.2f}")
        
        # 5. 获取统计信息
        print("\n5. 文档索引统计")
        print("-" * 40)
        stats = await get_document_stats(session)
        if stats:
            print(f"  📊 总文档数: {stats['total_documents']}")
            print(f"  📁 按类型统计:")
            for type_stat in stats['by_document_type']:
                print(f"    - {type_stat['type']}: {type_stat['count']} 个")
            print(f"  🗂️ 按存储桶统计:")
            for bucket_stat in stats['by_bucket']:
                print(f"    - {bucket_stat['bucket']}: {bucket_stat['count']} 个")
            if stats.get('average_word_count'):
                print(f"  📝 平均字数: {stats['average_word_count']}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())