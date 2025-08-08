#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings

async def delete_minio_indices():
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
        # Delete the actual index (this will also remove any aliases pointing to it)
        indices_to_delete = ['minio_documents_v2', 'minio_files', 'newsletter_articles']
        
        for index in indices_to_delete:
            try:
                if await client.indices.exists(index=index):
                    await client.indices.delete(index=index)
                    print(f"✅ Deleted index: {index}")
                else:
                    print(f"⏭️  Index not found: {index}")
            except Exception as e:
                print(f"❌ Error deleting {index}: {e}")
        
        print("\n✅ Cleanup complete!")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(delete_minio_indices())