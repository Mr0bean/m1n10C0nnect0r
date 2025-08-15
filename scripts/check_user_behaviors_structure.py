#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查user_behaviors表的实际结构
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


async def check_table_structure():
    """检查user_behaviors表结构"""
    
    print(f"连接到数据库: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}")
    print(f"用户: {POSTGRES_USER}")
    
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
        
        # 检查表是否存在
        table_exists_sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'user_behaviors'
        );
        """
        
        exists = await conn.fetchval(table_exists_sql)
        print(f"user_behaviors表存在: {exists}")
        
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
            AND table_name = 'user_behaviors'
            ORDER BY ordinal_position;
            """
            
            columns = await conn.fetch(structure_sql)
            print("\n表结构:")
            print("-" * 80)
            print(f"{'列名':<20} {'数据类型':<20} {'允许空值':<10} {'默认值':<20}")
            print("-" * 80)
            for col in columns:
                nullable = "YES" if col['is_nullable'] == 'YES' else "NO"
                default = col['column_default'] or ""
                print(f"{col['column_name']:<20} {col['data_type']:<20} {nullable:<10} {default:<20}")
            print("-" * 80)
            
            # 检查外键约束
            fk_sql = """
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name='user_behaviors';
            """
            
            foreign_keys = await conn.fetch(fk_sql)
            if foreign_keys:
                print("\n外键约束:")
                print("-" * 80)
                for fk in foreign_keys:
                    print(f"列: {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
                    print(f"约束名: {fk['constraint_name']}")
                print("-" * 80)
            else:
                print("\n没有外键约束")
            
            # 查看当前数据
            count_sql = "SELECT COUNT(*) FROM public.user_behaviors;"
            count = await conn.fetchval(count_sql)
            print(f"\n当前表中记录数: {count}")
            
            if count > 0:
                sample_sql = "SELECT * FROM public.user_behaviors LIMIT 3;"
                samples = await conn.fetch(sample_sql)
                print("\n示例数据:")
                for sample in samples:
                    print(dict(sample))
        
        # 关闭连接
        await conn.close()
        print("\n检查完成!")
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_table_structure())