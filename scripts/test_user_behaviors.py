#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户行为API端点
"""

import requests
import json
import uuid
from datetime import datetime
import time

# API基础URL
BASE_URL = "http://localhost:9011/api/v1"

# 测试会话ID
TEST_SESSION_ID = str(uuid.uuid4())
TEST_USER_ID = "test_user_001"


def test_record_single_behavior():
    """测试记录单个用户行为"""
    print("\n=== 测试记录单个用户行为 ===")
    
    # 测试搜索行为
    search_behavior = {
        "behavior_type": "search_query",
        "user_id": TEST_USER_ID,
        "session_id": TEST_SESSION_ID,
        "target_type": "search",
        "target_id": None,
        "action_details": {
            "query": "AI newsletter",
            "filters": {
                "category": "AI_NEWS",
                "date_range": "last_week"
            }
        },
        "metadata": {
            "source": "search_bar",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/user-behaviors/record",
        json=search_behavior,
        headers={
            "User-Agent": "Mozilla/5.0 Test Client",
            "Referer": "http://localhost:3000/search"
        }
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 测试文档查看行为
    doc_view_behavior = {
        "behavior_type": "document_view",
        "user_id": TEST_USER_ID,
        "session_id": TEST_SESSION_ID,
        "target_type": "newsletter",
        "target_id": "newsletter_123",
        "action_details": {
            "view_duration": 120,
            "scroll_depth": 0.75
        },
        "metadata": {
            "device": "desktop",
            "browser": "Chrome"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/user-behaviors/record",
        json=doc_view_behavior
    )
    
    print(f"\n文档查看行为记录状态: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_batch_record_behaviors():
    """测试批量记录用户行为"""
    print("\n=== 测试批量记录用户行为 ===")
    
    behaviors = [
        {
            "behavior_type": "newsletter_view",
            "user_id": TEST_USER_ID,
            "target_type": "newsletter",
            "target_id": "nl_001",
            "action_details": {"view_time": 30}
        },
        {
            "behavior_type": "newsletter_like",
            "user_id": TEST_USER_ID,
            "target_type": "newsletter",
            "target_id": "nl_001",
            "action_details": {"liked": True}
        },
        {
            "behavior_type": "newsletter_share",
            "user_id": TEST_USER_ID,
            "target_type": "newsletter",
            "target_id": "nl_001",
            "action_details": {"platform": "twitter"}
        }
    ]
    
    response = requests.post(
        f"{BASE_URL}/user-behaviors/batch-record",
        json=behaviors,
        headers={"X-Session-ID": TEST_SESSION_ID}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_query_behaviors():
    """测试查询用户行为"""
    print("\n=== 测试查询用户行为 ===")
    
    # 查询特定用户的所有行为
    params = {
        "user_id": TEST_USER_ID,
        "page": 1,
        "size": 10
    }
    
    response = requests.get(
        f"{BASE_URL}/user-behaviors/query",
        params=params
    )
    
    print(f"状态码: {response.status_code}")
    print(f"用户 {TEST_USER_ID} 的行为记录:")
    result = response.json()
    print(f"总数: {result.get('total', 0)}")
    
    for behavior in result.get('behaviors', []):
        print(f"  - {behavior.get('behavior_type')}: {behavior.get('target_type')}:{behavior.get('target_id')}")
    
    # 查询特定类型的行为
    params = {
        "behavior_type": "newsletter_view",
        "page": 1,
        "size": 5
    }
    
    response = requests.get(
        f"{BASE_URL}/user-behaviors/query",
        params=params
    )
    
    print(f"\nNewsletter查看行为记录:")
    result = response.json()
    for behavior in result.get('behaviors', []):
        print(f"  - User: {behavior.get('user_id')}, Target: {behavior.get('target_id')}")


def test_get_statistics():
    """测试获取行为统计"""
    print("\n=== 测试获取行为统计 ===")
    
    # 获取特定用户的统计
    params = {
        "user_id": TEST_USER_ID,
        "days": 7
    }
    
    response = requests.get(
        f"{BASE_URL}/user-behaviors/statistics",
        params=params
    )
    
    print(f"状态码: {response.status_code}")
    print(f"用户 {TEST_USER_ID} 的行为统计:")
    stats = response.json()
    print(f"  总行为数: {stats.get('total_behaviors', 0)}")
    print(f"  行为类型分布:")
    for behavior_type, count in stats.get('behavior_counts', {}).items():
        print(f"    - {behavior_type}: {count}")
    
    # 获取全局统计
    params = {
        "days": 1
    }
    
    response = requests.get(
        f"{BASE_URL}/user-behaviors/statistics",
        params=params
    )
    
    print(f"\n过去24小时的全局统计:")
    stats = response.json()
    print(f"  总行为数: {stats.get('total_behaviors', 0)}")
    print(f"  独立用户数: {stats.get('unique_users', 0)}")
    print(f"  独立会话数: {stats.get('unique_sessions', 0)}")


def test_get_popular_targets():
    """测试获取热门目标"""
    print("\n=== 测试获取热门目标 ===")
    
    # 先记录一些测试数据
    for i in range(5):
        for j in range(i + 1):
            behavior = {
                "behavior_type": "newsletter_view",
                "user_id": f"user_{j}",
                "target_type": "newsletter",
                "target_id": f"nl_{i:03d}",
                "action_details": {"test": True}
            }
            requests.post(f"{BASE_URL}/user-behaviors/record", json=behavior)
    
    # 获取热门newsletter
    params = {
        "behavior_type": "newsletter_view",
        "limit": 5,
        "days": 1
    }
    
    response = requests.get(
        f"{BASE_URL}/user-behaviors/popular/newsletter",
        params=params
    )
    
    print(f"状态码: {response.status_code}")
    print("热门Newsletter:")
    result = response.json()
    for target in result.get('targets', []):
        print(f"  - ID: {target.get('target_id')}, 访问次数: {target.get('access_count')}, 独立用户: {target.get('unique_users')}")


def test_user_timeline():
    """测试获取用户行为时间线"""
    print("\n=== 测试获取用户行为时间线 ===")
    
    response = requests.get(
        f"{BASE_URL}/user-behaviors/user/{TEST_USER_ID}/timeline",
        params={
            "days": 7,
            "page": 1,
            "size": 20
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"用户 {TEST_USER_ID} 的行为时间线:")
    print(f"统计信息: {json.dumps(result.get('statistics', {}), indent=2, ensure_ascii=False)}")
    print(f"最近行为:")
    for behavior in result.get('timeline', [])[:5]:
        print(f"  - {behavior.get('created_at')}: {behavior.get('behavior_type')} on {behavior.get('target_type')}:{behavior.get('target_id')}")


def test_anonymous_behavior():
    """测试匿名用户行为记录"""
    print("\n=== 测试匿名用户行为记录 ===")
    
    # 不提供user_id，只使用session_id
    behavior = {
        "behavior_type": "page_view",
        "target_type": "page",
        "target_id": "/home",
        "action_details": {
            "referrer": "google.com",
            "landing": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/user-behaviors/record",
        json=behavior
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def main():
    """运行所有测试"""
    print("开始测试用户行为API端点...")
    print(f"API地址: {BASE_URL}")
    print(f"测试会话ID: {TEST_SESSION_ID}")
    print(f"测试用户ID: {TEST_USER_ID}")
    
    try:
        # 测试服务是否可用
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("错误: API服务不可用")
            return
        
        # 运行测试
        test_record_single_behavior()
        time.sleep(0.5)
        
        test_batch_record_behaviors()
        time.sleep(0.5)
        
        test_query_behaviors()
        time.sleep(0.5)
        
        test_get_statistics()
        time.sleep(0.5)
        
        test_get_popular_targets()
        time.sleep(0.5)
        
        test_user_timeline()
        time.sleep(0.5)
        
        test_anonymous_behavior()
        
        print("\n=== 所有测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到API服务")
        print("请确保后端服务正在运行: cd minio-file-manager/backend && python -m uvicorn app.main:app --reload --port 9011")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()