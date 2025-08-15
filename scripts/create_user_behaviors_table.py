#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建user_behaviors表
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


async def create_table():
    """创建user_behaviors表"""
    
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
        
        # 创建表的SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.user_behaviors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255),
            session_id VARCHAR(255),
            behavior_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(255),
            action_details JSONB,
            metadata JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            referer TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 创建索引的SQL
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_user_behaviors_user_id ON public.user_behaviors(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_behaviors_session_id ON public.user_behaviors(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_behaviors_behavior_type ON public.user_behaviors(behavior_type);",
            "CREATE INDEX IF NOT EXISTS idx_user_behaviors_created_at ON public.user_behaviors(created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_user_behaviors_target ON public.user_behaviors(target_type, target_id);"
        ]
        
        # 执行创建表
        print("创建表 user_behaviors...")
        await conn.execute(create_table_sql)
        print("表创建成功")
        
        # 创建索引
        print("创建索引...")
        for index_sql in create_indexes_sql:
            await conn.execute(index_sql)
        print("索引创建成功")
        
        # 验证表是否存在
        check_sql = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable 
        FROM 
            information_schema.columns 
        WHERE 
            table_schema = 'public' 
            AND table_name = 'user_behaviors'
        ORDER BY 
            ordinal_position;
        """
        
        rows = await conn.fetch(check_sql)
        
        if rows:
            print("\n表结构:")
            print("-" * 60)
            for row in rows:
                nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  {row['column_name']:20} {row['data_type']:15} {nullable}")
            print("-" * 60)
        
        # 插入测试数据
        print("\n插入测试数据...")
        test_sql = """
        INSERT INTO public.user_behaviors (
            user_id, session_id, behavior_type, target_type, target_id,
            action_details, metadata, ip_address, user_agent, referer
        ) VALUES (
            $1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10
        ) RETURNING id, created_at;
        """
        
        result = await conn.fetchrow(
            test_sql,
            'test_user_001',
            'test_session_001',
            'page_view',
            'page',
            '/home',
            '{"test": true}',
            '{"source": "test_script"}',
            '127.0.0.1',
            'Test Script',
            'http://localhost'
        )
        
        if result:
            print(f"测试数据插入成功: ID={result['id']}, 时间={result['created_at']}")
        
        # 查询测试
        print("\n查询测试数据...")
        test_query = "SELECT COUNT(*) as count FROM public.user_behaviors;"
        count_result = await conn.fetchrow(test_query)
        print(f"表中共有 {count_result['count']} 条记录")
        
        # 关闭连接
        await conn.close()
        print("\n表创建和测试完成!")
        
    except asyncpg.exceptions.UndefinedTableError:
        print("错误: 表不存在")
    except asyncpg.exceptions.PostgresError as e:
        print(f"PostgreSQL错误: {e}")
    except Exception as e:
        print(f"连接数据库失败: {e}")
        print("\n请检查:")
        print("1. PostgreSQL服务是否正在运行")
        print("2. 数据库配置是否正确")
        print("3. 用户权限是否足够")


if __name__ == "__main__":
    asyncio.run(create_table())