#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找最近上传的数据
"""

import asyncio
from datetime import datetime, timedelta
import asyncpg
from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings
from tabulate import tabulate

async def find_recent_data():
    """查找最近24小时内的数据"""
    settings = get_settings()
    
    # 设置时间范围
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    print("\n" + "="*80)
    print(f"🔍 查找最近24小时内的数据")
    print(f"时间范围: {yesterday.strftime('%Y-%m-%d %H:%M')} 到 {now.strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    # 1. PostgreSQL查询
    print("\n📊 PostgreSQL (articles表):")
    print("-" * 40)
    
    try:
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_database,
            user=settings.postgres_user,
            password=settings.postgres_password
        )
        
        # 查询最近的记录
        recent_records = await conn.fetch("""
            SELECT id, title, category, author, created_at, subtitle
            FROM articles 
            WHERE created_at >= $1
            ORDER BY created_at DESC
        """, yesterday)
        
        if recent_records:
            print(f"找到 {len(recent_records)} 条记录:")
            for record in recent_records:
                print(f"\n  📄 ID: {record['id']}")
                print(f"     标题: {record['title']}")
                print(f"     分类: {record['category']}")
                print(f"     作者: {record['author']}")
                print(f"     时间: {record['created_at']}")
                if record['subtitle']:
                    print(f"     摘要: {record['subtitle'][:100]}...")
        else:
            print("没有找到最近24小时的记录")
        
        # 查询今天的记录
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_records = await conn.fetch("""
            SELECT COUNT(*) as count, category
            FROM articles 
            WHERE created_at >= $1
            GROUP BY category
        """, today_start)
        
        if today_records:
            print(f"\n今天的记录统计:")
            for record in today_records:
                print(f"  - {record['category']}: {record['count']} 条")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL错误: {str(e)}")
    
    # 2. Elasticsearch查询
    print("\n🔍 Elasticsearch索引:")
    print("-" * 40)
    
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
        # 查询各个索引
        indices = ['minio_files', 'minio_documents', 'minio_articles']
        
        for index_name in indices:
            try:
                if await es_client.indices.exists(index=index_name):
                    # 搜索最近的文档
                    search_result = await es_client.search(
                        index=index_name,
                        body={
                            "size": 5,
                            "query": {
                                "range": {
                                    "upload_time": {
                                        "gte": yesterday.isoformat()
                                    }
                                }
                            },
                            "sort": [
                                {"upload_time": {"order": "desc"}}
                            ]
                        }
                    )
                    
                    hits = search_result.get('hits', {}).get('hits', [])
                    if hits:
                        print(f"\n📁 {index_name}: 找到 {len(hits)} 个最近文档")
                        for hit in hits:
                            source = hit['_source']
                            print(f"  - {source.get('object_name', source.get('title', 'N/A'))}")
                            if 'upload_time' in source:
                                print(f"    上传时间: {source['upload_time']}")
                    else:
                        # 尝试其他时间字段
                        search_result = await es_client.search(
                            index=index_name,
                            body={
                                "size": 3,
                                "sort": [{"_doc": {"order": "desc"}}]
                            }
                        )
                        
                        hits = search_result.get('hits', {}).get('hits', [])
                        if hits:
                            print(f"\n📁 {index_name}: 最新的 {len(hits)} 个文档")
                            for hit in hits:
                                source = hit['_source']
                                title = source.get('title', source.get('object_name', 'N/A'))
                                if len(title) > 60:
                                    title = title[:60] + "..."
                                print(f"  - {title}")
                
            except Exception as e:
                print(f"📁 {index_name}: 查询错误 - {str(e)[:50]}")
        
    except Exception as e:
        print(f"❌ Elasticsearch错误: {str(e)}")
    finally:
        await es_client.close()

async def check_api_endpoints():
    """测试API端点"""
    print("\n🌐 API端点测试:")
    print("-" * 40)
    
    import aiohttp
    
    endpoints = [
        ("GET", "http://localhost:9011/api/v1/buckets/", "获取存储桶列表"),
        ("GET", "http://localhost:9011/api/v1/search/?query=test", "搜索测试"),
        ("GET", "http://localhost:9011/docs", "API文档"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, url, desc in endpoints:
            try:
                async with session.request(method, url, timeout=5) as response:
                    status = response.status
                    if status == 200:
                        print(f"✅ {desc}: {url} - 状态 {status}")
                    else:
                        print(f"⚠️ {desc}: {url} - 状态 {status}")
            except Exception as e:
                print(f"❌ {desc}: {url} - 错误: {str(e)[:30]}")

async def main():
    """主函数"""
    await find_recent_data()
    await check_api_endpoints()
    
    print("\n" + "="*80)
    print("💡 数据位置总结:")
    print("-" * 40)
    print("1. PostgreSQL本地数据库 - localhost:5432/ai_newsletters/articles")
    print("2. Elasticsearch远程索引 - 60.205.160.74:9200")
    print("3. MinIO远程存储 - 60.205.160.74:9000")
    print("4. API服务 - localhost:9011/api/v1")
    print("\n如果前端看不到数据，请检查:")
    print("- 前端是否正确连接到API (localhost:9011)")
    print("- API是否正常运行")
    print("- 前端查询的索引/表是否正确")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())