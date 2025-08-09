#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理所有数据：清空Elasticsearch索引和MinIO存储桶
"""

import asyncio
from elasticsearch import AsyncElasticsearch
from minio import Minio
from app.core.config import get_settings
import sys

async def clear_elasticsearch():
    """清空所有Elasticsearch索引"""
    settings = get_settings()
    
    # 创建ES客户端
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
        # 列出所有相关索引
        indices_to_delete = [
            'minio_files',
            'minio_documents', 
            'minio_articles',
            'newsletter_articles'
        ]
        
        print("\n" + "="*80)
        print("Elasticsearch索引清理")
        print("="*80)
        
        for index in indices_to_delete:
            try:
                # 检查索引是否存在
                exists = await client.indices.exists(index=index)
                if exists:
                    # 获取文档数量
                    count_result = await client.count(index=index)
                    doc_count = count_result['count']
                    
                    print(f"\n索引: {index}")
                    print(f"  当前文档数: {doc_count}")
                    
                    # 删除索引
                    response = await client.indices.delete(index=index)
                    print(f"  状态: ✅ 已删除")
                else:
                    print(f"\n索引: {index}")
                    print(f"  状态: ⚠️ 索引不存在")
                    
            except Exception as e:
                print(f"\n索引: {index}")
                print(f"  状态: ❌ 删除失败 - {str(e)}")
        
        print("\n" + "="*80)
        print("Elasticsearch清理完成")
        print("="*80)
        
    except Exception as e:
        print(f"Elasticsearch连接失败: {str(e)}")
    finally:
        await client.close()

def clear_minio():
    """清空所有MinIO存储桶"""
    settings = get_settings()
    
    # 创建MinIO客户端
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl
    )
    
    print("\n" + "="*80)
    print("MinIO存储桶清理")
    print("="*80)
    
    try:
        # 列出所有存储桶
        buckets = client.list_buckets()
        
        if not buckets:
            print("\n没有找到任何存储桶")
        else:
            for bucket in buckets:
                bucket_name = bucket.name
                print(f"\n存储桶: {bucket_name}")
                print(f"  创建时间: {bucket.creation_date}")
                
                try:
                    # 列出并统计对象
                    objects = list(client.list_objects(bucket_name, recursive=True))
                    object_count = len(objects)
                    total_size = sum(obj.size for obj in objects)
                    
                    print(f"  对象数量: {object_count}")
                    print(f"  总大小: {format_size(total_size)}")
                    
                    if object_count > 0:
                        # 删除所有对象
                        for obj in objects:
                            client.remove_object(bucket_name, obj.object_name)
                            print(f"    删除对象: {obj.object_name}")
                        
                        print(f"  状态: ✅ 已清空所有对象")
                    else:
                        print(f"  状态: ⚠️ 存储桶已为空")
                    
                    # 询问是否删除存储桶本身
                    # 注意：这里注释掉了删除桶的代码，避免误删
                    # client.remove_bucket(bucket_name)
                    # print(f"  存储桶删除: ✅")
                    
                except Exception as e:
                    print(f"  状态: ❌ 清理失败 - {str(e)}")
        
        print("\n" + "="*80)
        print("MinIO清理完成")
        print("="*80)
        
    except Exception as e:
        print(f"MinIO连接失败: {str(e)}")

def format_size(bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

async def clear_postgresql():
    """清空PostgreSQL articles表"""
    from app.services.postgresql_service import postgresql_service
    
    print("\n" + "="*80)
    print("PostgreSQL数据清理")
    print("="*80)
    
    try:
        pool = await postgresql_service.get_pool()
        
        async with pool.acquire() as conn:
            # 获取当前记录数
            count_result = await conn.fetchrow(
                "SELECT COUNT(*) as count FROM public.articles"
            )
            record_count = count_result['count']
            
            print(f"\nArticles表")
            print(f"  当前记录数: {record_count}")
            
            if record_count > 0:
                # 删除所有记录
                await conn.execute("DELETE FROM public.articles")
                print(f"  状态: ✅ 已删除所有记录")
            else:
                print(f"  状态: ⚠️ 表已为空")
        
        await postgresql_service.close_pool()
        
        print("\n" + "="*80)
        print("PostgreSQL清理完成")
        print("="*80)
        
    except Exception as e:
        print(f"PostgreSQL操作失败: {str(e)}")

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("数据清理工具")
    print("="*80)
    print("\n⚠️  警告：此操作将清空所有数据，无法恢复！")
    print("\n将清理以下内容：")
    print("1. Elasticsearch索引：minio_files, minio_documents, minio_articles, newsletter_articles")
    print("2. MinIO存储桶中的所有对象")
    print("3. PostgreSQL articles表中的所有记录")
    
    print("\n" + "="*80)
    response = input("\n确认要继续吗？(输入 'yes' 继续，其他任意键取消): ")
    
    if response.lower() != 'yes':
        print("\n操作已取消")
        sys.exit(0)
    
    print("\n开始清理数据...")
    
    # 清理Elasticsearch
    await clear_elasticsearch()
    
    # 清理MinIO
    clear_minio()
    
    # 清理PostgreSQL
    await clear_postgresql()
    
    print("\n" + "="*80)
    print("✅ 所有数据清理完成！")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())