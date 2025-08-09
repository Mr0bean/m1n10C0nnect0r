#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PostgreSQL集成的完整工作流
MinIO -> PostgreSQL -> Elasticsearch
"""

import asyncio
import os
from datetime import datetime
from app.services.article_processing_service import article_processing_service
from app.services.postgresql_service import postgresql_service
from app.core.config import get_settings
from elasticsearch import AsyncElasticsearch


async def test_complete_workflow():
    """测试完整的工作流程"""
    
    print("=" * 50)
    print("测试 MinIO -> PostgreSQL -> Elasticsearch 工作流")
    print("=" * 50)
    
    # 测试数据
    test_content = """
# 测试文章标题

这是一个测试文章的摘要内容，用于验证完整的数据处理流程。

## 主要内容

本文介绍了如何使用Python进行数据处理，包括以下几个方面：

1. 数据导入和清洗
2. 数据转换和处理
3. 数据存储和索引

### 代码示例

```python
def process_data(data):
    # 处理数据
    return processed_data
```

## 总结

通过本文的介绍，我们了解了完整的数据处理流程。
    """.encode('utf-8')
    
    bucket_name = "test-bucket"
    object_name = f"test_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    print(f"\n1. 准备上传文件: {object_name}")
    print(f"   存储桶: {bucket_name}")
    print(f"   文件大小: {len(test_content)} bytes")
    
    # 执行处理流程
    print("\n2. 执行处理流程...")
    result = await article_processing_service.process_and_index(
        bucket_name=bucket_name,
        object_name=object_name,
        file_content=test_content,
        content_type="text/markdown",
        author="测试作者"
    )
    
    if result['success']:
        print("   ✅ 处理成功!")
        print(f"   - PostgreSQL ID: {result.get('pg_id')}")
        print(f"   - Elasticsearch ID: {result.get('doc_id')}")
        print(f"   - 索引名称: {result.get('index')}")
        print(f"   - MinIO URL: {result.get('public_url')}")
        print(f"   - 是否重复: {result.get('is_duplicate', False)}")
        
        # 验证PostgreSQL记录
        print("\n3. 验证PostgreSQL记录...")
        pg_id = result.get('pg_id')
        if pg_id:
            pg_record = await postgresql_service.get_newsletter_by_id(pg_id)
            if pg_record:
                print("   ✅ PostgreSQL记录已创建")
                print(f"   - ID: {pg_record['id']}")
                print(f"   - 标题: {pg_record['title']}")
                print(f"   - 分类: {pg_record['category']}")
                print(f"   - 创建时间: {pg_record['createdAt']}")
            else:
                print("   ❌ PostgreSQL记录未找到")
        
        # 验证Elasticsearch记录
        print("\n4. 验证Elasticsearch记录...")
        settings = get_settings()
        scheme = "https" if settings.elasticsearch_use_ssl else "http"
        host = f"{scheme}://{settings.elasticsearch_host}:{settings.elasticsearch_port}"
        
        if settings.elasticsearch_username and settings.elasticsearch_password:
            auth = (settings.elasticsearch_username, settings.elasticsearch_password)
        else:
            auth = None
        
        es_client = AsyncElasticsearch(
            [host],
            basic_auth=auth,
            verify_certs=settings.elasticsearch_use_ssl,
            ssl_show_warn=False
        )
        
        try:
            es_doc = await es_client.get(
                index="minio_articles",
                id=result.get('doc_id')
            )
            
            if es_doc:
                print("   ✅ Elasticsearch记录已创建")
                print(f"   - 索引: {es_doc['_index']}")
                print(f"   - ID: {es_doc['_id']}")
                print(f"   - pg_id字段: {es_doc['_source'].get('pg_id')}")
                print(f"   - 标题: {es_doc['_source'].get('title')}")
                
                # 验证pg_id是否正确关联
                if es_doc['_source'].get('pg_id') == pg_id:
                    print("   ✅ pg_id正确关联!")
                else:
                    print("   ❌ pg_id关联不正确")
        except Exception as e:
            print(f"   ❌ Elasticsearch查询失败: {e}")
        finally:
            await es_client.close()
        
        # 测试重复上传
        print("\n5. 测试重复上传处理...")
        duplicate_result = await article_processing_service.process_and_index(
            bucket_name=bucket_name,
            object_name=object_name,
            file_content=test_content,
            content_type="text/markdown",
            author="测试作者"
        )
        
        if duplicate_result['success'] and duplicate_result.get('is_duplicate'):
            print("   ✅ 重复检测正常工作")
            print(f"   - 返回已存在的PG ID: {duplicate_result.get('pg_id')}")
        else:
            print("   ⚠️  重复检测可能有问题")
            
    else:
        print(f"   ❌ 处理失败: {result.get('error')}")
    
    # 关闭连接池
    await postgresql_service.close_pool()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


async def test_postgresql_connection():
    """测试PostgreSQL连接"""
    print("\n测试PostgreSQL连接...")
    
    try:
        pool = await postgresql_service.get_pool()
        async with pool.acquire() as conn:
            # 测试查询
            result = await conn.fetchval("SELECT version()")
            print(f"✅ PostgreSQL连接成功!")
            print(f"   版本: {result}")
            
            # 检查表是否存在
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'newsletters'
                )
                """
            )
            
            if table_exists:
                print("✅ newsletters表存在")
                
                # 获取表的行数
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM public.newsletters"
                )
                print(f"   当前记录数: {count}")
            else:
                print("❌ newsletters表不存在，请先创建表")
                
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        print("   请检查:")
        print("   1. PostgreSQL服务是否运行")
        print("   2. 数据库配置是否正确")
        print("   3. newsletters表是否已创建")
    
    await postgresql_service.close_pool()


if __name__ == "__main__":
    print("开始测试PostgreSQL集成...")
    
    # 先测试数据库连接
    asyncio.run(test_postgresql_connection())
    
    # 询问是否继续
    response = input("\n是否继续测试完整工作流? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(test_complete_workflow())
    else:
        print("测试结束")