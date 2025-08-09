#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from datetime import datetime

# 创建测试文档
content = """# Test Document

This is a test document for the new article index.

## Content

Testing the IK analyzer with Chinese text: 这是一个测试文档，用于测试中文分词器。

Keywords: test, elasticsearch, minio, 中文分词
"""

# 准备文件上传
files = {
    'file': (f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md', content.encode('utf-8'), 'text/markdown')
}

# 上传文件
response = requests.post(
    'http://localhost:9011/api/v1/objects/test-articles/upload',
    files=files
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")