#!/usr/bin/env python3
"""
测试将桶设置为公开访问的功能
"""
import requests
import json

BASE_URL = "http://localhost:9011/api/v1"

def test_bucket_public_access():
    # 1. 创建一个测试桶
    bucket_name = "test-public-bucket"
    
    print(f"1. 创建测试桶: {bucket_name}")
    response = requests.post(
        f"{BASE_URL}/buckets",
        json={"bucket_name": bucket_name}
    )
    
    if response.status_code == 201:
        print(f"   ✅ 桶创建成功")
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"   ℹ️  桶已存在")
    else:
        print(f"   ❌ 创建失败: {response.text}")
        return
    
    # 2. 设置桶为公开访问
    print(f"\n2. 设置桶为公开访问")
    response = requests.put(f"{BASE_URL}/buckets/{bucket_name}/make-public")
    
    if response.status_code == 200:
        print(f"   ✅ {response.json()['message']}")
    else:
        print(f"   ❌ 设置失败: {response.text}")
        return
    
    # 3. 获取桶策略验证
    print(f"\n3. 验证桶策略")
    response = requests.get(f"{BASE_URL}/buckets/{bucket_name}/policy")
    
    if response.status_code == 200:
        policy = response.json()
        print(f"   ✅ 当前策略:")
        print(json.dumps(policy, indent=4, ensure_ascii=False))
    else:
        print(f"   ❌ 获取策略失败: {response.text}")
    
    # 4. 上传测试文件
    print(f"\n4. 上传测试文件")
    test_content = "这是一个公开访问的测试文件"
    files = {
        'file': ('test.txt', test_content, 'text/plain')
    }
    
    response = requests.post(
        f"{BASE_URL}/objects/{bucket_name}/upload",
        files=files
    )
    
    if response.status_code == 201:
        upload_info = response.json()
        print(f"   ✅ 文件上传成功")
        print(f"   文件名: {upload_info['object_name']}")
        print(f"   ETag: {upload_info['etag']}")
        
        # 5. 测试公开访问
        print(f"\n5. 测试公开访问URL")
        public_url = f"http://60.205.160.74:9000/{bucket_name}/{upload_info['object_name']}"
        print(f"   公开访问URL: {public_url}")
        print(f"   提示: 你现在可以在浏览器中直接访问这个URL，无需认证")
        
    else:
        print(f"   ❌ 上传失败: {response.text}")
    
    # 6. 询问是否设置回私有
    print(f"\n6. 演示：将桶设置回私有")
    input("   按Enter键继续...")
    
    response = requests.put(f"{BASE_URL}/buckets/{bucket_name}/make-private")
    
    if response.status_code == 200:
        print(f"   ✅ {response.json()['message']}")
        print(f"   现在文件不能通过公开URL访问了")
    else:
        print(f"   ❌ 设置失败: {response.text}")


def test_custom_policy():
    """演示如何使用自定义策略"""
    bucket_name = "custom-policy-bucket"
    
    print(f"\n\n=== 自定义策略示例 ===")
    print(f"1. 创建桶: {bucket_name}")
    
    response = requests.post(
        f"{BASE_URL}/buckets",
        json={"bucket_name": bucket_name}
    )
    
    if response.status_code not in [201, 400]:
        print(f"   ❌ 创建失败: {response.text}")
        return
    
    # 2. 设置自定义策略（只允许读取特定前缀的文件）
    print(f"\n2. 设置自定义策略（只允许公开访问 'public/' 前缀的文件）")
    
    custom_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/public/*"]
            }
        ]
    }
    
    response = requests.put(
        f"{BASE_URL}/buckets/{bucket_name}/policy",
        json={"policy": custom_policy}
    )
    
    if response.status_code == 200:
        print(f"   ✅ 自定义策略设置成功")
        print(f"   现在只有 'public/' 目录下的文件可以公开访问")
    else:
        print(f"   ❌ 设置失败: {response.text}")


if __name__ == "__main__":
    print("=== MinIO 桶公开访问测试 ===\n")
    
    # 测试基本的公开/私有设置
    test_bucket_public_access()
    
    # 测试自定义策略
    test_custom_policy()
    
    print("\n\n测试完成！")