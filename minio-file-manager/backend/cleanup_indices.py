#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理所有 Elasticsearch 索引
谨慎使用！这将删除所有数据！
"""

import asyncio
from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings
import sys


async def cleanup_all_indices():
    """清理所有非系统索引"""
    settings = get_settings()
    
    # 构建连接
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
        # 获取所有索引
        indices = await client.cat.indices(format='json')
        
        # 需要删除的索引（排除系统索引）
        indices_to_delete = []
        system_indices = []
        
        for index in indices:
            index_name = index['index']
            if index_name.startswith('.'):
                system_indices.append(index_name)
            else:
                indices_to_delete.append(index_name)
        
        print("=" * 60)
        print("Elasticsearch 索引清理工具")
        print("=" * 60)
        
        if system_indices:
            print(f"\n系统索引（不会删除）: {len(system_indices)} 个")
            for idx in system_indices[:5]:  # 只显示前5个
                print(f"  - {idx}")
            if len(system_indices) > 5:
                print(f"  ... 还有 {len(system_indices) - 5} 个")
        
        if indices_to_delete:
            print(f"\n将要删除的索引: {len(indices_to_delete)} 个")
            for idx in indices_to_delete:
                # 获取索引信息
                doc_count = 0
                for index_info in indices:
                    if index_info['index'] == idx:
                        doc_count = index_info.get('docs.count', 0)
                        break
                print(f"  - {idx} ({doc_count} 个文档)")
            
            print("\n⚠️  警告：这将永久删除所有数据！")
            confirm = input("确认删除？输入 'YES' 继续: ")
            
            if confirm == 'YES':
                print("\n开始删除索引...")
                for idx in indices_to_delete:
                    try:
                        await client.indices.delete(index=idx)
                        print(f"✅ 已删除: {idx}")
                    except Exception as e:
                        print(f"❌ 删除失败 {idx}: {e}")
                
                print("\n✅ 清理完成！")
            else:
                print("\n❌ 操作已取消")
        else:
            print("\n没有需要删除的用户索引")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        await client.close()


async def cleanup_specific_indices():
    """只清理 MinIO 相关的索引"""
    settings = get_settings()
    
    # 构建连接
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
    
    # 指定要删除的索引
    target_indices = [
        'minio_files',
        'minio_documents', 
        'minio_articles',
        'newsletter_articles'
    ]
    
    try:
        print("=" * 60)
        print("清理 MinIO 相关索引")
        print("=" * 60)
        
        for idx in target_indices:
            try:
                if await client.indices.exists(index=idx):
                    # 获取文档数量
                    stats = await client.count(index=idx)
                    doc_count = stats['count']
                    
                    await client.indices.delete(index=idx)
                    print(f"✅ 已删除: {idx} ({doc_count} 个文档)")
                else:
                    print(f"⏭️  跳过: {idx} (不存在)")
            except Exception as e:
                print(f"❌ 删除失败 {idx}: {e}")
        
        print("\n✅ 清理完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    print("选择清理模式:")
    print("1. 清理所有用户索引（危险！）")
    print("2. 只清理 MinIO 相关索引")
    print("3. 退出")
    
    choice = input("\n请选择 (1/2/3): ")
    
    if choice == '1':
        asyncio.run(cleanup_all_indices())
    elif choice == '2':
        asyncio.run(cleanup_specific_indices())
    else:
        print("退出")