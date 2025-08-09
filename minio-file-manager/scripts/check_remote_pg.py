#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查远程PostgreSQL数据库
"""

import asyncio
import asyncpg
from datetime import datetime
from tabulate import tabulate

async def check_remote_database():
    """检查远程数据库"""
    
    # 远程数据库配置
    host = "60.205.160.74"
    port = 5432
    database = "thinkinai"
    user = "postgres"
    password = "uro@#wet8332@"
    
    print("\n" + "="*80)
    print("🔍 连接到远程PostgreSQL数据库")
    print(f"Host: {host}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print("="*80)
    
    try:
        # 连接到远程数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        print("✅ 连接成功！")
        
        # 1. 列出所有表
        print("\n📊 数据库中的表：")
        print("-" * 40)
        
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        if tables:
            for table in tables:
                table_name = table['tablename']
                
                # 获取表的行数
                count_query = f"SELECT COUNT(*) as count FROM public.{table_name}"
                try:
                    count_result = await conn.fetchrow(count_query)
                    count = count_result['count']
                    print(f"  📁 {table_name}: {count} 条记录")
                    
                    # 如果是articles或newsletters表，显示更多信息
                    if table_name in ['articles', 'newsletters']:
                        # 获取最新记录
                        latest_query = f"""
                            SELECT * FROM public.{table_name} 
                            ORDER BY created_at DESC LIMIT 3
                        """
                        latest_records = await conn.fetch(latest_query)
                        
                        if latest_records:
                            print(f"\n    最新记录：")
                            for record in latest_records:
                                title = record.get('title', 'N/A')
                                if len(title) > 50:
                                    title = title[:50] + "..."
                                created_at = record.get('created_at', 'N/A')
                                print(f"      - {title}")
                                print(f"        创建时间: {created_at}")
                        
                        # 获取今天的记录数
                        today_query = f"""
                            SELECT COUNT(*) as count 
                            FROM public.{table_name} 
                            WHERE created_at >= CURRENT_DATE
                        """
                        today_result = await conn.fetchrow(today_query)
                        today_count = today_result['count']
                        print(f"    今天新增: {today_count} 条")
                        
                except Exception as e:
                    print(f"  📁 {table_name}: 查询错误 - {str(e)[:50]}")
        else:
            print("  没有找到任何表")
        
        # 2. 检查是否有newsletters表
        print("\n🔍 查找newsletter相关表：")
        print("-" * 40)
        
        newsletter_tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND (tablename LIKE '%newsletter%' OR tablename LIKE '%article%')
        """)
        
        if newsletter_tables:
            for table in newsletter_tables:
                table_name = table['tablename']
                print(f"  ✅ 找到: {table_name}")
                
                # 获取表结构
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                    LIMIT 10
                """)
                
                print(f"    主要字段：")
                for col in columns[:5]:
                    print(f"      - {col['column_name']}: {col['data_type']}")
                if len(columns) > 5:
                    print(f"      ... 还有 {len(columns)-5} 个字段")
        else:
            print("  没有找到newsletter或article相关的表")
        
        # 3. 检查最近插入的数据
        print("\n📈 数据统计：")
        print("-" * 40)
        
        # 尝试查询articles表
        try:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    MAX(created_at) as latest,
                    MIN(created_at) as earliest
                FROM public.articles
            """)
            
            if stats and stats['total'] > 0:
                print(f"  Articles表统计：")
                print(f"    总记录数: {stats['total']}")
                print(f"    最早记录: {stats['earliest']}")
                print(f"    最新记录: {stats['latest']}")
                
                # 按分类统计
                categories = await conn.fetch("""
                    SELECT category, COUNT(*) as count
                    FROM public.articles
                    GROUP BY category
                    ORDER BY count DESC
                """)
                
                if categories:
                    print(f"    按分类：")
                    for cat in categories:
                        print(f"      - {cat['category']}: {cat['count']} 条")
        except Exception as e:
            if "does not exist" not in str(e):
                print(f"  查询articles表失败: {str(e)[:50]}")
        
        await conn.close()
        print("\n✅ 数据库检查完成")
        
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        print("\n可能的原因：")
        print("1. 网络连接问题")
        print("2. 防火墙阻止了5432端口")
        print("3. PostgreSQL未配置远程访问")
        print("4. 用户名或密码错误")
        print("5. 数据库名称错误")

async def test_insert():
    """测试插入数据"""
    
    # 远程数据库配置
    host = "60.205.160.74"
    port = 5432
    database = "thinkinai"
    user = "postgres"
    password = "uro@#wet8332@"
    
    print("\n" + "="*80)
    print("🧪 测试数据插入")
    print("="*80)
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # 检查articles表是否存在
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'articles'
            )
        """)
        
        if not table_exists:
            print("⚠️ articles表不存在，需要创建表")
            
            # 创建表的SQL
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS public.articles (
                id VARCHAR(50) PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                subtitle TEXT,
                content TEXT,
                category VARCHAR(50),
                tags JSON,
                author VARCHAR(200),
                source_url VARCHAR(1000),
                publish_date TIMESTAMP,
                read_time INTEGER,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                featured BOOLEAN DEFAULT FALSE,
                member_only BOOLEAN DEFAULT FALSE,
                status VARCHAR(20),
                cover_image VARCHAR(1000),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                metadata JSON
            );
            
            CREATE INDEX IF NOT EXISTS idx_articles_created ON public.articles(created_at);
            CREATE INDEX IF NOT EXISTS idx_articles_category ON public.articles(category);
            """
            
            print("是否要创建articles表？(yes/no): ", end="")
            # 这里需要用户确认
            
        else:
            print("✅ articles表存在")
            
            # 显示最新的数据
            latest = await conn.fetch("""
                SELECT id, title, created_at 
                FROM public.articles 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            if latest:
                print("\n最新5条记录：")
                for record in latest:
                    print(f"  - {record['title'][:50]}...")
                    print(f"    ID: {record['id']}")
                    print(f"    时间: {record['created_at']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

async def main():
    """主函数"""
    await check_remote_database()
    # await test_insert()  # 如果需要测试插入，取消注释

if __name__ == "__main__":
    asyncio.run(main())