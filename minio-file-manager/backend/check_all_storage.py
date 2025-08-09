#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有存储位置的数据情况
"""

import asyncio
from elasticsearch import AsyncElasticsearch
from minio import Minio
import asyncpg
from app.core.config import get_settings
from datetime import datetime
from tabulate import tabulate

async def check_postgresql():
    """检查PostgreSQL数据"""
    settings = get_settings()
    
    print("\n" + "="*80)
    print("📊 PostgreSQL 数据库 (ai_newsletters)")
    print("="*80)
    
    try:
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_database,
            user=settings.postgres_user,
            password=settings.postgres_password
        )
        
        # 总体统计
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT category) as categories,
                MAX(created_at) as latest,
                MIN(created_at) as earliest
            FROM articles
        """)
        
        print(f"📌 总记录数: {stats['total']}")
        print(f"📌 分类数量: {stats['categories']}")
        print(f"📌 最早记录: {stats['earliest']}")
        print(f"📌 最新记录: {stats['latest']}")
        
        # 按分类统计
        categories = await conn.fetch("""
            SELECT category, COUNT(*) as count 
            FROM articles 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        print("\n按分类统计:")
        for cat in categories:
            print(f"  - {cat['category']}: {cat['count']} 条")
        
        # 最新5条记录
        latest = await conn.fetch("""
            SELECT id, title, category, created_at 
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        print("\n最新5条记录:")
        table_data = []
        for record in latest:
            table_data.append([
                record['id'][:8] + "...",
                record['title'][:40] + ("..." if len(record['title']) > 40 else ""),
                record['category'],
                record['created_at'].strftime('%Y-%m-%d %H:%M')
            ])
        
        print(tabulate(table_data, headers=['ID', '标题', '分类', '创建时间'], tablefmt='grid'))
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL 错误: {str(e)}")

async def check_elasticsearch():
    """检查Elasticsearch数据"""
    settings = get_settings()
    
    print("\n" + "="*80)
    print("🔍 Elasticsearch 索引")
    print("="*80)
    
    scheme = "https" if settings.elasticsearch_use_ssl else "http"
    host = f"{scheme}://{settings.elasticsearch_host}:{settings.elasticsearch_port}"
    
    if settings.elasticsearch_username and settings.elasticsearch_password:
        auth = (settings.elasticsearch_username, settings.elasticsearch_password)
    else:
        auth = None
    
    client = AsyncElasticsearch(
        [host],
        basic_auth=auth,
        verify_certs=settings.elasticsearch_use_ssl,
        ssl_show_warn=False
    )
    
    try:
        # 检查所有相关索引
        indices = ['minio_files', 'minio_documents', 'minio_articles', 'newsletter_articles']
        
        for index_name in indices:
            try:
                if await client.indices.exists(index=index_name):
                    # 获取文档数量
                    count = await client.count(index=index_name)
                    doc_count = count['count']
                    
                    # 获取索引统计
                    stats = await client.indices.stats(index=index_name)
                    size = stats['indices'][index_name]['total']['store']['size_in_bytes']
                    size_mb = size / (1024 * 1024)
                    
                    print(f"\n📁 索引: {index_name}")
                    print(f"  - 文档数: {doc_count}")
                    print(f"  - 大小: {size_mb:.2f} MB")
                    
                    # 获取最新文档
                    if doc_count > 0:
                        search_result = await client.search(
                            index=index_name,
                            body={
                                "size": 3,
                                "sort": [{"_doc": {"order": "desc"}}],
                                "_source": ["title", "object_name", "upload_time", "created_at"]
                            }
                        )
                        
                        if search_result['hits']['hits']:
                            print("  最新文档:")
                            for hit in search_result['hits']['hits']:
                                source = hit['_source']
                                title = source.get('title', source.get('object_name', 'N/A'))
                                if len(title) > 50:
                                    title = title[:50] + "..."
                                print(f"    - {title}")
                else:
                    print(f"\n📁 索引: {index_name} - 不存在")
                    
            except Exception as e:
                print(f"\n📁 索引: {index_name} - 访问错误: {str(e)[:50]}")
        
    except Exception as e:
        print(f"❌ Elasticsearch 错误: {str(e)}")
    finally:
        await client.close()

def check_minio():
    """检查MinIO存储"""
    settings = get_settings()
    
    print("\n" + "="*80)
    print("☁️ MinIO 对象存储")
    print("="*80)
    
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl
    )
    
    try:
        # 列出所有存储桶
        buckets = client.list_buckets()
        
        print(f"📌 存储桶总数: {len(buckets)}")
        
        total_objects = 0
        total_size = 0
        
        for bucket in buckets:
            try:
                # 统计每个桶的对象
                objects = list(client.list_objects(bucket.name, recursive=True))
                bucket_size = sum(obj.size for obj in objects)
                total_objects += len(objects)
                total_size += bucket_size
                
                print(f"\n📦 存储桶: {bucket.name}")
                print(f"  - 对象数: {len(objects)}")
                print(f"  - 总大小: {bucket_size / (1024*1024):.2f} MB")
                
                # 显示最新的3个对象
                if objects:
                    sorted_objects = sorted(objects, key=lambda x: x.last_modified, reverse=True)[:3]
                    print("  最新对象:")
                    for obj in sorted_objects:
                        name = obj.object_name
                        if len(name) > 50:
                            name = "..." + name[-47:]
                        print(f"    - {name} ({obj.size} bytes)")
                        
            except Exception as e:
                print(f"  ❌ 读取错误: {str(e)[:50]}")
        
        print(f"\n📊 总计:")
        print(f"  - 总对象数: {total_objects}")
        print(f"  - 总大小: {total_size / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"❌ MinIO 错误: {str(e)}")

async def check_data_flow():
    """检查数据流向"""
    print("\n" + "="*80)
    print("🔄 数据流向分析")
    print("="*80)
    
    print("""
    上传流程:
    1. 文件上传 → MinIO (对象存储)
    2. 文档处理 → 提取内容和元数据
    3. 数据存储:
       ├─ PostgreSQL (articles表) - 结构化数据
       ├─ Elasticsearch (minio_documents) - 全文搜索
       └─ Elasticsearch (minio_articles) - 文章索引
    
    数据位置:
    - MinIO: http://60.205.160.74:9000 (原始文件)
    - PostgreSQL: localhost:5432/ai_newsletters (结构化数据)
    - Elasticsearch: http://60.205.160.74:9200 (搜索索引)
    """)

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("🔍 数据存储位置全面检查")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)
    
    # 检查各个存储
    await check_postgresql()
    await check_elasticsearch()
    check_minio()
    await check_data_flow()
    
    print("\n" + "="*80)
    print("✅ 检查完成")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())