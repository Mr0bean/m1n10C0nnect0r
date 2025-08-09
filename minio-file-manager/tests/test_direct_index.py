#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from app.services.article_processing_service import article_processing_service

async def test_direct_indexing():
    """直接测试文章索引功能"""
    
    content = """# Test Article
    
This is a test article for debugging.
中文测试内容。
    """.encode('utf-8')
    
    result = await article_processing_service.process_and_index(
        bucket_name="test-articles",
        object_name="test_direct.md",
        file_content=content,
        content_type="text/markdown"
    )
    
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_direct_indexing())