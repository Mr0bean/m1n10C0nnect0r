#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PostgreSQL连接
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_connection():
    """测试PostgreSQL连接"""
    
    # 从环境变量获取配置
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = int(os.getenv('POSTGRES_PORT', '5432'))
    database = os.getenv('POSTGRES_DATABASE', 'newsletters')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', '')
    
    print("="*80)
    print("PostgreSQL连接测试")
    print("="*80)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else '(empty)'}")
    print("="*80)
    
    # 测试1: 直接连接测试
    print("\n1. 测试直接连接...")
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print("✅ 连接成功!")
        
        # 测试查询
        version = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL版本: {version}")
        
        await conn.close()
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        print("\n可能的原因:")
        print("1. PostgreSQL服务未启动")
        print("2. 数据库不存在")
        print("3. 用户名/密码错误")
        print("4. 网络/防火墙问题")
        return False
    
    # 测试2: 连接池测试
    print("\n2. 测试连接池...")
    try:
        pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            min_size=1,
            max_size=5
        )
        print("✅ 连接池创建成功!")
        
        async with pool.acquire() as conn:
            # 测试表是否存在
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'newsletters'
                )
            """)
            
            if exists:
                print("✅ newsletters表存在")
                
                # 获取表信息
                count = await conn.fetchval("SELECT COUNT(*) FROM public.newsletters")
                print(f"   当前记录数: {count}")
                
                # 获取表结构
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = 'newsletters'
                    ORDER BY ordinal_position
                """)
                
                print("\n   表结构:")
                for col in columns[:5]:  # 只显示前5列
                    print(f"   - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
                if len(columns) > 5:
                    print(f"   ... 还有 {len(columns)-5} 列")
            else:
                print("⚠️ newsletters表不存在")
                print("\n需要创建表吗？运行以下SQL:")
                print("""
CREATE TABLE IF NOT EXISTS public.newsletters (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL UNIQUE,
    summary TEXT,
    content TEXT,
    category VARCHAR(50),
    tags JSONB,
    author VARCHAR(100),
    "sourceUrl" TEXT,
    "readTime" INTEGER,
    "viewCount" INTEGER DEFAULT 0,
    "likeCount" INTEGER DEFAULT 0,
    "shareCount" INTEGER DEFAULT 0,
    "commentCount" INTEGER DEFAULT 0,
    featured BOOLEAN DEFAULT FALSE,
    "memberOnly" BOOLEAN DEFAULT FALSE,
    status VARCHAR(50),
    "publishedAt" TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    "contentFileKey" TEXT,
    "contentStorageType" VARCHAR(50)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_newsletters_title ON public.newsletters(title);
CREATE INDEX IF NOT EXISTS idx_newsletters_category ON public.newsletters(category);
CREATE INDEX IF NOT EXISTS idx_newsletters_published ON public.newsletters("publishedAt");
                """)
        
        await pool.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接池创建失败: {str(e)}")
        return False

async def test_service():
    """测试PostgreSQL服务类"""
    print("\n3. 测试PostgreSQL服务类...")
    
    try:
        from app.services.postgresql_service import postgresql_service
        
        # 测试获取连接池
        pool = await postgresql_service.get_pool()
        print("✅ 服务类连接池获取成功!")
        
        # 测试基本查询
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"✅ 测试查询成功: 1 = {result}")
        
        # 关闭连接池
        await postgresql_service.close_pool()
        print("✅ 连接池关闭成功")
        
    except Exception as e:
        print(f"❌ 服务类测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    success = await test_connection()
    
    if success:
        await test_service()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())