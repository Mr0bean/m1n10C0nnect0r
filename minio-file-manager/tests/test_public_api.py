#!/usr/bin/env python3
"""
测试桶公开访问API的简单示例
"""
import requests

BASE_URL = "http://localhost:9011/api/v1"

# 创建测试桶
bucket_name = "demo-public-bucket"
print(f"创建桶: {bucket_name}")
response = requests.post(f"{BASE_URL}/buckets", json={"bucket_name": bucket_name})
print(f"状态: {response.status_code}")

# 设置为公开访问
print(f"\n设置桶为公开访问...")
response = requests.put(f"{BASE_URL}/buckets/{bucket_name}/make-public")
print(f"响应: {response.json()}")

# 上传文件
print(f"\n上传测试文件...")
files = {'file': ('hello.txt', '欢迎访问公开文件!', 'text/plain')}
response = requests.post(f"{BASE_URL}/objects/{bucket_name}/upload", files=files)
upload_info = response.json()
print(f"文件已上传: {upload_info['object_name']}")

# 显示公开访问URL
public_url = f"http://60.205.160.74:9000/{bucket_name}/{upload_info['object_name']}"
print(f"\n✅ 公开访问URL: {public_url}")
print("你可以在浏览器中直接访问这个URL，无需任何认证！")

# 设置回私有（可选）
# response = requests.put(f"{BASE_URL}/buckets/{bucket_name}/make-private")
# print(f"\n设置回私有: {response.json()}")