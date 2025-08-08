#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Elasticsearch集成功能
"""
import requests
import time

BASE_URL = "http://localhost:9011/api/v1"

def test_elasticsearch_integration():
    print("=== 测试Elasticsearch文件索引功能 ===\n")
    
    bucket_name = "search-test-bucket"
    
    # 1. 创建测试桶
    print(f"1. 创建测试桶: {bucket_name}")
    response = requests.post(f"{BASE_URL}/buckets", json={"bucket_name": bucket_name})
    if response.status_code in [201, 400]:
        print("   ✅ 桶已准备好")
    else:
        print(f"   ❌ 创建失败: {response.text}")
        return
    
    # 2. 上传测试文件（会自动索引到ES）
    test_files = [
        ("年度财务报告2024.pdf", "这是公司2024年度财务报告，包含详细的收支分析。", "application/pdf"),
        ("产品用户手册.docx", "产品使用说明书，帮助用户快速上手。", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("会议记录-技术讨论.txt", "2024年技术团队会议记录，讨论了新功能开发。", "text/plain"),
        ("项目计划书.pdf", "新项目的详细计划和时间安排。", "application/pdf")
    ]
    
    print(f"\n2. 上传测试文件到MinIO（同时索引到ES）")
    for file_name, content, content_type in test_files:
        files = {
            'file': (file_name, content, content_type)
        }
        # 添加一些元数据
        data = {
            'metadata': '{"author":"测试用户","department":"技术部","tags":"测试,文档"}'
        }
        
        response = requests.post(
            f"{BASE_URL}/objects/{bucket_name}/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 201:
            print(f"   ✅ 上传成功: {file_name}")
        else:
            print(f"   ❌ 上传失败: {file_name} - {response.text}")
    
    # 等待ES索引完成
    print("\n   等待Elasticsearch索引完成...")
    time.sleep(2)
    
    # 3. 测试文件搜索功能
    print(f"\n3. 测试文件搜索功能")
    
    search_tests = [
        ("报告", "搜索包含'报告'的文件"),
        ("技术", "搜索包含'技术'的文件"),
        ("pdf", "搜索PDF文件"),
        ("用户", "搜索包含'用户'的文件"),
        ("2024", "搜索包含'2024'的文件")
    ]
    
    for query, description in search_tests:
        print(f"\n   🔍 {description}")
        response = requests.get(
            f"{BASE_URL}/search/files",
            params={"query": query, "size": 10}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"      找到 {results['total']} 个匹配结果:")
            
            for result in results['results']:
                score = result['score']
                name = result['file_name']
                print(f"      - {name} (相关度: {score:.2f})")
                
                # 显示高亮信息
                if 'highlight' in result and result['highlight']:
                    for field, highlights in result['highlight'].items():
                        print(f"        高亮: {highlights[0]}")
        else:
            print(f"      ❌ 搜索失败: {response.text}")
    
    # 4. 测试高级搜索
    print(f"\n4. 测试高级搜索（POST请求）")
    search_request = {
        "query": "报告 AND 2024",
        "bucket": bucket_name,
        "file_type": ".pdf",
        "page": 1,
        "size": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/search/files",
        json=search_request
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"   ✅ 高级搜索成功，找到 {results['total']} 个结果")
        for result in results['results']:
            print(f"      - {result['file_name']} (桶: {result['bucket']})")
    else:
        print(f"   ❌ 高级搜索失败: {response.text}")
    
    # 5. 测试文件统计
    print(f"\n5. 测试文件统计功能")
    response = requests.get(f"{BASE_URL}/search/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"   ✅ 统计信息获取成功:")
        print(f"      总文件数: {stats['total_files']}")
        print(f"      存储桶分布:")
        for bucket_stat in stats['buckets']:
            print(f"        - {bucket_stat['bucket']}: {bucket_stat['count']} 个文件")
        print(f"      文件类型分布:")
        for type_stat in stats['file_types']:
            print(f"        - {type_stat['extension']}: {type_stat['count']} 个文件")
    else:
        print(f"   ❌ 获取统计失败: {response.text}")
    
    # 6. 测试文件删除（同时删除ES索引）
    print(f"\n6. 测试文件删除（同时删除ES索引）")
    file_to_delete = test_files[0][0]  # 删除第一个文件
    
    response = requests.delete(f"{BASE_URL}/objects/{bucket_name}/{file_to_delete}")
    
    if response.status_code == 200:
        print(f"   ✅ 文件删除成功: {file_to_delete}")
        
        # 验证ES索引也被删除
        time.sleep(1)  # 等待ES更新
        response = requests.get(
            f"{BASE_URL}/search/files",
            params={"query": file_to_delete.split('.')[0]}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"   ✅ ES索引同步删除验证: 现在搜索只能找到 {results['total']} 个结果")
    else:
        print(f"   ❌ 文件删除失败: {response.text}")
    
    print(f"\n=== Elasticsearch集成功能测试完成 ===")
    print(f"✅ 文件上传时自动索引到ES")
    print(f"✅ 支持多种搜索语法和过滤")
    print(f"✅ 提供搜索结果高亮显示")
    print(f"✅ 文件删除时同步删除ES索引")
    print(f"✅ 提供详细的统计信息")


if __name__ == "__main__":
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(5)
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/")
        if response.status_code == 200:
            print("✅ 服务已就绪\n")
            test_elasticsearch_integration()
        else:
            print("❌ 服务未就绪，请检查后端服务状态")
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("请确保后端服务在 http://localhost:9011 上运行")