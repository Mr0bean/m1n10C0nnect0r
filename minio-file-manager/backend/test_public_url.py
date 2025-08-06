#!/usr/bin/env python3
"""
测试获取文件公开访问URL功能
"""
import requests

BASE_URL = "http://localhost:9011/api/v1"

def test_public_url_feature():
    bucket_name = "url-test-bucket"
    file_name = "sample.txt"
    
    print("=== 测试文件公开URL功能 ===\n")
    
    # 1. 创建桶
    print(f"1. 创建测试桶: {bucket_name}")
    response = requests.post(f"{BASE_URL}/buckets", json={"bucket_name": bucket_name})
    if response.status_code in [201, 400]:
        print("   ✅ 桶已准备好")
    else:
        print(f"   ❌ 创建失败: {response.text}")
        return
    
    # 2. 上传测试文件
    print(f"\n2. 上传测试文件: {file_name}")
    files = {'file': (file_name, '这是一个测试文件，用于演示公开URL功能。', 'text/plain')}
    response = requests.post(f"{BASE_URL}/objects/{bucket_name}/upload", files=files)
    if response.status_code == 201:
        print("   ✅ 文件上传成功")
    else:
        print(f"   ❌ 上传失败: {response.text}")
        return
    
    # 3. 获取文件的公开URL（桶还是私有的）
    print(f"\n3. 获取私有桶中文件的公开URL")
    response = requests.get(f"{BASE_URL}/objects/{bucket_name}/{file_name}/public-url")
    if response.status_code == 200:
        url_info = response.json()
        print(f"   URL: {url_info['public_url']}")
        print(f"   是否公开: {url_info['is_public']}")
        print(f"   说明: {url_info['note']}")
    else:
        print(f"   ❌ 获取失败: {response.text}")
        return
    
    # 4. 设置桶为公开
    print(f"\n4. 设置桶为公开访问")
    response = requests.put(f"{BASE_URL}/buckets/{bucket_name}/make-public")
    if response.status_code == 200:
        print(f"   ✅ {response.json()['message']}")
    else:
        print(f"   ❌ 设置失败: {response.text}")
        return
    
    # 5. 再次获取公开URL（现在桶是公开的）
    print(f"\n5. 获取公开桶中文件的URL")
    response = requests.get(f"{BASE_URL}/objects/{bucket_name}/{file_name}/public-url")
    if response.status_code == 200:
        url_info = response.json()
        print(f"   URL: {url_info['public_url']}")
        print(f"   是否公开: {url_info['is_public']}")
        print(f"   说明: {url_info['note']}")
        
        print(f"\n   🎉 现在你可以直接在浏览器中访问这个URL:")
        print(f"   {url_info['public_url']}")
    else:
        print(f"   ❌ 获取失败: {response.text}")
    
    # 6. 演示批量获取URL
    print(f"\n6. 演示批量获取文件URL")
    
    # 上传更多文件
    for i in range(2, 4):
        test_file = f"file-{i}.txt"
        files = {'file': (test_file, f'测试文件 {i}', 'text/plain')}
        requests.post(f"{BASE_URL}/objects/{bucket_name}/upload", files=files)
    
    # 获取桶中所有文件
    response = requests.get(f"{BASE_URL}/objects/{bucket_name}")
    if response.status_code == 200:
        objects = response.json()
        print(f"   桶中有 {len(objects)} 个文件:")
        
        for obj in objects:
            if not obj['is_dir']:
                # 获取每个文件的公开URL
                url_response = requests.get(f"{BASE_URL}/objects/{bucket_name}/{obj['name']}/public-url")
                if url_response.status_code == 200:
                    url_info = url_response.json()
                    print(f"   - {obj['name']}: {url_info['public_url']}")
    
    print(f"\n=== 功能特点总结 ===")
    print(f"✅ 自动检测桶是否公开")
    print(f"✅ 返回完整的访问URL")
    print(f"✅ 提供URL有效性说明")
    print(f"✅ 支持任意文件路径")
    print(f"✅ 适合批量URL获取")

if __name__ == "__main__":
    test_public_url_feature()