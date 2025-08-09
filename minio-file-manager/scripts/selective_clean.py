#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择性清理数据工具
可以单独清理Elasticsearch、MinIO或PostgreSQL
"""

import asyncio
from elasticsearch import AsyncElasticsearch
from minio import Minio
from app.core.config import get_settings
import sys
import argparse

async def clear_elasticsearch_index(index_name=None):
    """清空指定的Elasticsearch索引"""
    settings = get_settings()
    
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
        if index_name:
            # 清理指定索引
            indices_to_delete = [index_name]
        else:
            # 清理所有相关索引
            indices_to_delete = [
                'minio_files',
                'minio_documents', 
                'minio_articles',
                'newsletter_articles'
            ]
        
        print("\n清理Elasticsearch索引:")
        for index in indices_to_delete:
            try:
                exists = await client.indices.exists(index=index)
                if exists:
                    count_result = await client.count(index=index)
                    doc_count = count_result['count']
                    print(f"  {index}: {doc_count} 个文档", end="")
                    
                    # 方式1：删除索引（完全删除）
                    # await client.indices.delete(index=index)
                    
                    # 方式2：只删除文档（保留索引结构）
                    await client.delete_by_query(
                        index=index,
                        body={"query": {"match_all": {}}}
                    )
                    
                    print(" -> ✅ 已清空")
                else:
                    print(f"  {index}: 不存在")
            except Exception as e:
                print(f"  {index}: ❌ 失败 - {str(e)}")
                
    except Exception as e:
        print(f"Elasticsearch错误: {str(e)}")
    finally:
        await client.close()

def clear_minio_bucket(bucket_name=None):
    """清空指定的MinIO存储桶"""
    settings = get_settings()
    
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl
    )
    
    try:
        if bucket_name:
            # 清理指定存储桶
            buckets_to_clear = [bucket_name]
        else:
            # 清理所有存储桶
            buckets_to_clear = [b.name for b in client.list_buckets()]
        
        print("\n清理MinIO存储桶:")
        for bucket in buckets_to_clear:
            try:
                # 检查存储桶是否存在
                if not client.bucket_exists(bucket):
                    print(f"  {bucket}: 不存在")
                    continue
                
                # 列出所有对象
                objects = list(client.list_objects(bucket, recursive=True))
                object_count = len(objects)
                
                if object_count > 0:
                    print(f"  {bucket}: {object_count} 个对象", end="")
                    
                    # 批量删除对象
                    delete_objects = [obj.object_name for obj in objects]
                    for obj_name in delete_objects:
                        client.remove_object(bucket, obj_name)
                    
                    print(" -> ✅ 已清空")
                else:
                    print(f"  {bucket}: 已为空")
                    
            except Exception as e:
                print(f"  {bucket}: ❌ 失败 - {str(e)}")
                
    except Exception as e:
        print(f"MinIO错误: {str(e)}")

async def clear_postgresql_table():
    """清空PostgreSQL articles表"""
    from app.services.postgresql_service import postgresql_service
    
    try:
        pool = await postgresql_service.get_pool()
        
        async with pool.acquire() as conn:
            count_result = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM public.articles"
            )
            record_count = count_result['count']
            
            print("\n清理PostgreSQL:")
            print(f"  articles表: {record_count} 条记录", end="")
            
            if record_count > 0:
                await conn.execute("DELETE FROM public.articles")
                print(" -> ✅ 已清空")
            else:
                print(" -> 已为空")
        
        await postgresql_service.close_pool()
        
    except Exception as e:
        print(f"\nPostgreSQL错误: {str(e)}")

async def show_statistics():
    """显示当前数据统计"""
    settings = get_settings()
    
    print("\n" + "="*80)
    print("当前数据统计")
    print("="*80)
    
    # Elasticsearch统计
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
    
    print("\nElasticsearch索引:")
    indices = ['minio_files', 'minio_documents', 'minio_articles', 'newsletter_articles']
    for index in indices:
        try:
            if await es_client.indices.exists(index=index):
                count = await es_client.count(index=index)
                print(f"  {index}: {count['count']} 个文档")
            else:
                print(f"  {index}: 不存在")
        except:
            print(f"  {index}: 无法访问")
    
    await es_client.close()
    
    # MinIO统计
    print("\nMinIO存储桶:")
    minio_client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl
    )
    
    try:
        for bucket in minio_client.list_buckets():
            objects = list(minio_client.list_objects(bucket.name, recursive=True))
            total_size = sum(obj.size for obj in objects)
            print(f"  {bucket.name}: {len(objects)} 个对象, {format_size(total_size)}")
    except:
        print("  无法访问MinIO")
    
    # PostgreSQL统计
    print("\nPostgreSQL表:")
    try:
        from app.services.postgresql_service import postgresql_service
        pool = await postgresql_service.get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchrow("SELECT COUNT(*) as count FROM public.articles")
            print(f"  articles: {count['count']} 条记录")
        await postgresql_service.close_pool()
    except:
        print("  无法访问PostgreSQL")
    
    print("="*80)

def format_size(bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

async def main():
    parser = argparse.ArgumentParser(description='选择性清理数据工具')
    parser.add_argument('--es', action='store_true', help='清空Elasticsearch索引')
    parser.add_argument('--es-index', type=str, help='指定要清空的ES索引名')
    parser.add_argument('--minio', action='store_true', help='清空MinIO存储桶')
    parser.add_argument('--minio-bucket', type=str, help='指定要清空的MinIO存储桶')
    parser.add_argument('--pg', action='store_true', help='清空PostgreSQL表')
    parser.add_argument('--all', action='store_true', help='清空所有数据')
    parser.add_argument('--stats', action='store_true', help='只显示统计信息')
    parser.add_argument('-y', '--yes', action='store_true', help='跳过确认提示')
    
    args = parser.parse_args()
    
    # 如果只是查看统计
    if args.stats:
        await show_statistics()
        return
    
    # 如果没有指定任何选项，显示帮助
    if not any([args.es, args.minio, args.pg, args.all]):
        parser.print_help()
        print("\n示例:")
        print("  python selective_clean.py --stats          # 查看当前数据统计")
        print("  python selective_clean.py --es             # 清空所有ES索引")
        print("  python selective_clean.py --es-index minio_files  # 清空指定ES索引")
        print("  python selective_clean.py --minio          # 清空所有MinIO存储桶")
        print("  python selective_clean.py --minio-bucket test  # 清空指定存储桶")
        print("  python selective_clean.py --pg             # 清空PostgreSQL表")
        print("  python selective_clean.py --all            # 清空所有数据")
        print("  python selective_clean.py --all -y         # 清空所有数据(无需确认)")
        return
    
    # 显示将要执行的操作
    print("\n将执行以下清理操作:")
    if args.all or args.es:
        if args.es_index:
            print(f"  - 清空Elasticsearch索引: {args.es_index}")
        else:
            print("  - 清空所有Elasticsearch索引")
    if args.all or args.minio:
        if args.minio_bucket:
            print(f"  - 清空MinIO存储桶: {args.minio_bucket}")
        else:
            print("  - 清空所有MinIO存储桶")
    if args.all or args.pg:
        print("  - 清空PostgreSQL articles表")
    
    # 确认操作
    if not args.yes:
        response = input("\n⚠️  确认要继续吗？(yes/no): ")
        if response.lower() != 'yes':
            print("操作已取消")
            return
    
    # 执行清理
    if args.all or args.es:
        await clear_elasticsearch_index(args.es_index)
    
    if args.all or args.minio:
        clear_minio_bucket(args.minio_bucket)
    
    if args.all or args.pg:
        await clear_postgresql_table()
    
    print("\n✅ 清理完成！")
    
    # 显示清理后的统计
    print("\n清理后的数据统计:")
    await show_statistics()

if __name__ == "__main__":
    asyncio.run(main())