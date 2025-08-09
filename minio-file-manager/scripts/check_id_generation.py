#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查ID生成方式
"""

import asyncio
import asyncpg

async def check_id_generation():
    """检查newsletters表的ID生成方式"""
    
    # 远程数据库配置
    host = "60.205.160.74"
    port = 5432
    database = "thinkinai"
    user = "postgres"
    password = "uro@#wet8332@"
    
    print("\n" + "="*80)
    print("🔍 检查newsletters表的ID配置")
    print("="*80)
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # 1. 检查ID列的默认值
        column_info = await conn.fetchrow("""
            SELECT 
                column_name,
                data_type,
                column_default,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'newsletters'
            AND column_name = 'id'
        """)
        
        print(f"\n📋 ID列信息：")
        print(f"  数据类型: {column_info['data_type']}")
        print(f"  默认值: {column_info['column_default']}")
        print(f"  可空: {column_info['is_nullable']}")
        
        # 2. 检查是否有UUID扩展
        uuid_ext = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_extension WHERE extname = 'uuid-ossp'
        """)
        
        if uuid_ext > 0:
            print("\n✅ UUID扩展已安装")
            
            # 测试UUID生成
            test_uuid = await conn.fetchval("SELECT uuid_generate_v4()")
            print(f"  测试生成UUID: {test_uuid}")
        else:
            print("\n⚠️ UUID扩展未安装")
        
        # 3. 尝试不提供ID插入
        print("\n🧪 测试自动生成ID...")
        
        try:
            # 方法1：使用DEFAULT
            result = await conn.fetchrow("""
                INSERT INTO public.newsletters (
                    id, title, summary, category, "contentFileKey"
                ) VALUES (
                    DEFAULT, $1, $2, $3, $4
                ) RETURNING id
            """, 
                "测试自动ID生成",
                "测试摘要",
                "AI_NEWS",
                "test/file.md"
            )
            
            if result:
                print(f"✅ 使用DEFAULT成功生成ID: {result['id']}")
                # 清理测试数据
                await conn.execute("DELETE FROM newsletters WHERE id = $1", result['id'])
                
        except Exception as e1:
            print(f"❌ DEFAULT方式失败: {str(e1)[:100]}")
            
            try:
                # 方法2：生成UUID
                result = await conn.fetchrow("""
                    INSERT INTO public.newsletters (
                        id, title, summary, category, "contentFileKey"
                    ) VALUES (
                        uuid_generate_v4()::text, $1, $2, $3, $4
                    ) RETURNING id
                """, 
                    "测试UUID生成",
                    "测试摘要",
                    "AI_NEWS",
                    "test/file.md"
                )
                
                if result:
                    print(f"✅ 使用uuid_generate_v4()成功生成ID: {result['id']}")
                    # 清理测试数据
                    await conn.execute("DELETE FROM newsletters WHERE id = $1", result['id'])
                    
            except Exception as e2:
                print(f"❌ UUID函数方式失败: {str(e2)[:100]}")
                
                # 方法3：不提供ID（如果有默认值）
                try:
                    result = await conn.fetchrow("""
                        INSERT INTO public.newsletters (
                            title, summary, category, "contentFileKey"
                        ) VALUES (
                            $1, $2, $3, $4
                        ) RETURNING id
                    """, 
                        "测试省略ID",
                        "测试摘要",
                        "AI_NEWS",
                        "test/file.md"
                    )
                    
                    if result:
                        print(f"✅ 省略ID成功生成: {result['id']}")
                        # 清理测试数据
                        await conn.execute("DELETE FROM newsletters WHERE id = $1", result['id'])
                        
                except Exception as e3:
                    print(f"❌ 省略ID方式失败: {str(e3)[:100]}")
                    print("\n需要手动生成ID")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

async def main():
    await check_id_generation()

if __name__ == "__main__":
    asyncio.run(main())