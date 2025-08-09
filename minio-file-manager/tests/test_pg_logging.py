#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PostgreSQL日志记录功能
"""

import asyncio
import logging
from datetime import datetime
from app.services.document_pipeline_service import document_pipeline_service

# 配置日志级别为DEBUG以查看所有日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('pg_storage_log.txt', encoding='utf-8')  # 输出到文件
    ]
)

async def test_document_upload():
    """测试文档上传并查看日志输出"""
    
    # 准备测试数据
    test_markdown = """# 测试文档标题

这是一个测试文档的摘要部分，用于验证PostgreSQL存储日志功能。

## 主要内容

这里是文档的主要内容，包含一些技术关键词如Python、Docker、Kubernetes等。

### 代码示例

```python
def hello_world():
    print("Hello, World!")
```

## 总结

这是一个用于测试日志记录的示例文档。
"""
    
    # 文件信息
    bucket_name = "test-bucket"
    file_name = f"test_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    file_content = test_markdown.encode('utf-8')
    content_type = "text/markdown"
    
    print("="*80)
    print("开始测试文档上传流程")
    print(f"Bucket: {bucket_name}")
    print(f"文件名: {file_name}")
    print(f"内容类型: {content_type}")
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
        print("处理结果:")
        print(f"MinIO上传: {result.get('minio_upload', False)}")
        print(f"ES索引: {result.get('es_indexed', False)}")
        print(f"PostgreSQL ID: {result.get('pg_id', 'None')}")
        print(f"ES文档ID: {result.get('es_document_id', 'None')}")
        print(f"公开URL: {result.get('public_url', 'None')}")
        print(f"是否重复: {result.get('is_duplicate', False)}")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        
        print("="*80)
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("PostgreSQL存储日志测试程序")
    print("日志将同时输出到控制台和pg_storage_log.txt文件")
    print("="*80 + "\n")
    
    await test_document_upload()
    
    print("\n测试完成！请查看控制台输出和pg_storage_log.txt文件中的详细日志。")

if __name__ == "__main__":
    asyncio.run(main())