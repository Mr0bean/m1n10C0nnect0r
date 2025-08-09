#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查远程newsletters表结构
"""

import asyncio
import asyncpg
from datetime import datetime

async def check_newsletters_structure():
    """检查newsletters表结构"""
    
    # 远程数据库配置
    host = "60.205.160.74"
    port = 5432
    database = "thinkinai"
    user = "postgres"
    password = "uro@#wet8332@"
    
    print("\n" + "="*80)
    print("🔍 检查远程newsletters表结构")
    print("="*80)
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # 获取newsletters表的完整结构
        columns = await conn.fetch("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'newsletters'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 newsletters表结构：")
        print("-" * 60)
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
            
            print(f"  {col['column_name']}: {col['data_type']}{max_len} {nullable} {default}")
        
        # 检查索引
        indexes = await conn.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'newsletters'
        """)
        
        if indexes:
            print("\n📑 索引：")
            for idx in indexes:
                print(f"  - {idx['indexname']}")
        
        # 检查枚举类型
        print("\n🔤 枚举类型：")
        enums = await conn.fetch("""
            SELECT 
                t.typname as enum_name,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname IN ('NewsletterCategory', 'ContentStatus', 'categoryenum')
            GROUP BY t.typname
        """)
        
        for enum in enums:
            print(f"  {enum['enum_name']}: {', '.join(enum['enum_values'])}")
        
        # 测试插入一条数据
        print("\n🧪 测试插入数据...")
        
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 尝试插入
            await conn.execute("""
                INSERT INTO public.newsletters (
                    id, title, summary, content, category
                ) VALUES (
                    $1, $2, $3, $4, $5
                )
            """, 
                test_id,
                "测试Newsletter文档",
                "这是一个测试摘要",
                "测试内容",
                "NEWS"
            )
            
            print("✅ 插入成功！")
            
            # 查询刚插入的数据
            result = await conn.fetchrow("""
                SELECT * FROM public.newsletters WHERE id = $1
            """, test_id)
            
            if result:
                print(f"  ID: {result['id']}")
                print(f"  标题: {result['title']}")
                print(f"  分类: {result.get('category', 'N/A')}")
            
            # 删除测试数据
            await conn.execute("DELETE FROM public.newsletters WHERE id = $1", test_id)
            print("✅ 测试数据已清理")
            
        except Exception as e:
            print(f"❌ 插入失败: {str(e)}")
            print("\n可能需要调整字段或数据类型")
        
        # 显示当前数据
        count = await conn.fetchval("SELECT COUNT(*) FROM public.newsletters")
        print(f"\n📊 当前newsletters表有 {count} 条记录")
        
        if count > 0:
            latest = await conn.fetch("""
                SELECT id, title FROM public.newsletters LIMIT 5
            """)
            print("最新记录：")
            for record in latest:
                print(f"  - {record['title']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

async def main():
    await check_newsletters_structure()

if __name__ == "__main__":
    asyncio.run(main())