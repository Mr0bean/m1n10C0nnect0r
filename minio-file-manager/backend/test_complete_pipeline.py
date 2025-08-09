#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试文档上传管道并验证PostgreSQL日志
"""

import asyncio
import logging
from datetime import datetime
from app.services.document_pipeline_service import document_pipeline_service
from app.services.minio_service import MinioService
from minio import Minio
from app.core.config import get_settings

# 配置日志级别为DEBUG以查看所有日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('complete_pipeline_log.txt', encoding='utf-8')  # 输出到文件
    ]
)

async def create_test_bucket():
    """创建测试用的存储桶"""
    settings = get_settings()
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl
    )
    
    bucket_name = "test-bucket"
    
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"✅ 创建存储桶: {bucket_name}")
        else:
            print(f"ℹ️ 存储桶已存在: {bucket_name}")
        return True
    except Exception as e:
        print(f"❌ 创建存储桶失败: {str(e)}")
        return False

async def test_document_upload():
    """测试文档上传并查看日志输出"""
    
    # 准备测试数据
    test_markdown = """# AI Newsletter测试文档

这是一个关于AI Agent和LLM的测试文档，用于验证PostgreSQL存储日志功能。

## 主要内容

这里讨论最新的AI技术趋势，包括：
- Large Language Models (LLM)
- AI Agents
- Machine Learning
- Neural Networks

### 代码示例

```python
import openai

def chat_with_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

## 工具推荐

1. **LangChain** - 用于构建LLM应用的框架
2. **AutoGPT** - 自主AI Agent
3. **Vector Database** - 用于语义搜索

## 总结

这是一个用于测试日志记录的AI相关示例文档。
"""
    
    # 文件信息
    bucket_name = "test-bucket"
    file_name = f"ai_newsletter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    file_content = test_markdown.encode('utf-8')
    content_type = "text/markdown"
    
    print("="*80)
    print("开始测试文档上传流程")
    print(f"Bucket: {bucket_name}")
    print(f"文件名: {file_name}")
    print(f"内容类型: {content_type}")
    print(f"文件大小: {len(file_content)} bytes")
    print("="*80)
    
    try:
        # 调用文档处理管道
        result = await document_pipeline_service.process_upload(
            bucket_name=bucket_name,
            file_name=file_name,
            file_content=file_content,
            content_type=content_type
        )
        
        print("\n" + "="*80)
        print("处理结果摘要:")
        print(f"✅ MinIO上传: {result.get('minio_upload', False)}")
        print(f"✅ ES索引: {result.get('es_indexed', False)}")
        print(f"✅ PostgreSQL ID: {result.get('pg_id', 'None')}")
        print(f"✅ ES文档ID: {result.get('es_document_id', 'None')}")
        print(f"✅ 公开URL: {result.get('public_url', 'None')[:50]}..." if result.get('public_url') else "❌ 公开URL: None")
        print(f"ℹ️ 是否重复: {result.get('is_duplicate', False)}")
        
        if result.get('error'):
            print(f"❌ 错误: {result['error']}")
        
        print("="*80)
        
        # 如果成功，验证PostgreSQL数据
        if result.get('pg_id'):
            from app.services.postgresql_service import postgresql_service
            pg_record = await postgresql_service.get_newsletter_by_id(result['pg_id'])
            if pg_record:
                print("\n" + "="*80)
                print("PostgreSQL记录验证:")
                print(f"ID: {pg_record['id']}")
                print(f"标题: {pg_record['title']}")
                print(f"分类: {pg_record['category']}")
                print(f"作者: {pg_record.get('author', 'None')}")
                print(f"创建时间: {pg_record['created_at']}")
                print("="*80)
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("完整管道测试程序")
    print("包含: MinIO上传 + Elasticsearch索引 + PostgreSQL存储")
    print("日志将同时输出到控制台和complete_pipeline_log.txt文件")
    print("="*80 + "\n")
    
    # 1. 创建测试bucket
    if await create_test_bucket():
        # 2. 测试文档上传
        await test_document_upload()
    
    print("\n✅ 测试完成！")
    print("请查看以下内容:")
    print("1. 控制台输出 - 查看实时日志")
    print("2. complete_pipeline_log.txt - 查看完整日志文件")
    print("3. PostgreSQL数据库 - 验证数据是否正确存储")

if __name__ == "__main__":
    asyncio.run(main())