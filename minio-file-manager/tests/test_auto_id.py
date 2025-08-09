#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动生成ID功能
"""

import asyncio
from datetime import datetime
from app.services.postgresql_service import postgresql_service

async def test_auto_id():
    """测试自动生成ID"""
    
    print("\n" + "="*80)
    print("🧪 测试数据库自动生成ID")
    print("="*80)
    
    # 测试数据
    test_data = {
        "title": f"测试文档_自动ID_{datetime.now().strftime('%H%M%S')}",
        "summary": "这是一个测试数据库自动生成ID的文档",
        "content": "测试内容...",
        "category": "AI_NEWS",
        "tags": [{"name": "test", "slug": "test"}],
        "author": "测试用户",
        "source_url": "https://example.com",
        "read_time": 5,
        "content_file_key": f"test/auto_id_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        "metadata": {"test": True, "timestamp": datetime.now().isoformat()}
    }
    
    # 测试1：使用数据库自动生成ID（默认）
    print("\n1️⃣ 测试数据库自动生成ID (use_auto_id=True):")
    print("-" * 40)
    
    try:
        result = await postgresql_service.insert_newsletter(
            title=test_data["title"],
            summary=test_data["summary"],
            content=test_data["content"],
            category=test_data["category"],
            tags=test_data["tags"],
            author=test_data["author"],
            source_url=test_data["source_url"],
            read_time=test_data["read_time"],
            content_file_key=test_data["content_file_key"],
            metadata=test_data["metadata"],
            use_auto_id=True  # 使用数据库自动生成ID
        )
        
        if result['success']:
            print(f"✅ 插入成功!")
            print(f"   生成的ID: {result['id']}")
            print(f"   标题: {result['title']}")
            print(f"   创建时间: {result.get('created_at', 'N/A')}")
        else:
            print(f"❌ 插入失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    # 测试2：使用手动生成ID
    print("\n2️⃣ 测试手动生成ID (use_auto_id=False):")
    print("-" * 40)
    
    test_data["title"] = f"测试文档_手动ID_{datetime.now().strftime('%H%M%S')}"
    
    try:
        result = await postgresql_service.insert_newsletter(
            title=test_data["title"],
            summary=test_data["summary"],
            content=test_data["content"],
            category=test_data["category"],
            tags=test_data["tags"],
            author=test_data["author"],
            source_url=test_data["source_url"],
            read_time=test_data["read_time"],
            content_file_key=test_data["content_file_key"],
            metadata=test_data["metadata"],
            use_auto_id=False  # 使用手动生成ID
        )
        
        if result['success']:
            print(f"✅ 插入成功!")
            print(f"   生成的ID: {result['id']}")
            print(f"   标题: {result['title']}")
            print(f"   创建时间: {result.get('created_at', 'N/A')}")
        else:
            print(f"❌ 插入失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    # 关闭连接池
    await postgresql_service.close_pool()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)

async def main():
    await test_auto_id()

if __name__ == "__main__":
    asyncio.run(main())