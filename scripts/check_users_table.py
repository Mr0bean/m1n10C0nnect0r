#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查users表的结构和数据
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
POSTGRES_HOST = os.getenv('POSTGRES_HOST', '60.205.160.74')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'thinkinai')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'uro@#wet8332@')


async def check_users_table():
    """检查users表"""
    
    print(f"连接到数据库: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}")
    
    try:
        # 创建连接
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        
        print("成功连接到数据库")
        
        # 检查users表是否存在
        table_exists_sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
        """
        
        exists = await conn.fetchval(table_exists_sql)
        print(f"users表存在: {exists}")
        
        if exists:
            # 查看表结构
            structure_sql = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'users'
            ORDER BY ordinal_position;
            """
            
            columns = await conn.fetch(structure_sql)
            print("\nusers表结构:")
            print("-" * 80)
            print(f"{'列名':<20} {'数据类型':<20} {'允许空值':<10} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                nullable = "YES" if col['is_nullable'] == 'YES' else "NO"
                default = col['column_default'] or ""
                print(f"{col['column_name']:<20} {col['data_type']:<20} {nullable:<10} {default:<20}")
            print("-" * 80)
            
            # 查看用户数据
            count_sql = "SELECT COUNT(*) FROM public.users;"
            count = await conn.fetchval(count_sql)
            print(f"\n当前users表中记录数: {count}")
            
            if count > 0:
                sample_sql = "SELECT id, email, name FROM public.users LIMIT 5;"
                samples = await conn.fetch(sample_sql)
                print("\n示例用户数据:")
                for sample in samples:
                    print(f"ID: {sample['id']}, Email: {sample.get('email', 'N/A')}, Name: {sample.get('name', 'N/A')}")
        else:
            print("users表不存在")
        
        # 关闭连接
        await conn.close()
        print("\n检查完成!")
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_users_table())