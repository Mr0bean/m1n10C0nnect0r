#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings

async def check_indices():
    settings = get_settings()
    
    scheme = "https" if settings.elasticsearch_use_ssl else "http"
    host = f"{scheme}://{settings.elasticsearch_host}:{settings.elasticsearch_port}"
    
    client = AsyncElasticsearch([host])
    
    try:
        # Get all indices
        indices = await client.cat.indices(format='json')
        print("Current indices:")
        for idx in indices:
            print(f"  - {idx['index']} ({idx.get('docs.count', 0)} docs)")
        
        # Check aliases
        aliases = await client.cat.aliases(format='json')
        if aliases:
            print("\nAliases:")
            for alias in aliases:
                print(f"  - {alias['alias']} -> {alias['index']}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_indices())