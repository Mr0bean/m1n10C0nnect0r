#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Newsletter交互API
包括点赞、评论等功能
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'minio-file-manager', 'backend')
sys.path.insert(0, backend_path)

# API基础配置
API_BASE_URL = "http://localhost:9011/api/v1"
TEST_NEWSLETTER_ID = None  # 将在测试中动态获取
TEST_COMMENT_ID = None     # 将在测试中创建


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*80)
    print(f"📌 {title}")
    print("="*80)


def print_result(success: bool, message: str, details: Dict = None):
    """打印测试结果"""
    status = "✅" if success else "❌"
    print(f"{status} {message}")
    if details:
        print(f"   详情: {json.dumps(details, ensure_ascii=False, indent=2)}")


def get_first_newsletter() -> Optional[str]:
    """获取第一个可用的Newsletter ID"""
    try:
        # 搜索Newsletter获取一个可用的ID
        response = requests.get(
            f"{API_BASE_URL}/newsletter/search/quick",
            params={"q": "AI"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                # 从搜索结果中提取ID
                first_result = data['results'][0]
                # 需要从数据库获取实际的Newsletter ID
                # 这里暂时使用一个示例ID
                return "test_newsletter_001"
        
        return None
    except Exception as e:
        print(f"获取Newsletter ID失败: {str(e)}")
        return None


class NewsletterAPITester:
    """Newsletter API测试器"""
    
    def __init__(self):
        self.api_base = API_BASE_URL
        self.newsletter_id = None
        self.comment_id = None
        self.test_results = []
        
    def setup(self):
        """测试前准备"""
        print_section("测试准备")
        
        # 获取可用的Newsletter ID
        # 使用实际存在的Newsletter ID
        self.newsletter_id = "e8ffb4ac-e3ea-4e3a-835a-e6ec6ff6cf30"  # 使用实际存在的ID
        
        print(f"使用Newsletter ID: {self.newsletter_id}")
        print("标题: 🥇Top ML Papers of the Week")
        return True
    
    def test_newsletter_like(self):
        """测试文章点赞功能"""
        print_section("测试文章点赞/取消点赞")
        
        # 1. 第一次点赞
        print("\n1. 测试点赞文章...")
        response = requests.post(
            f"{self.api_base}/newsletters/{self.newsletter_id}/like",
            json={"action": "like"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result(True, f"点赞成功！当前点赞数: {data.get('likeCount')}, 是否已赞: {data.get('isLiked')}")
                self.test_results.append(("文章点赞", True))
            else:
                print_result(False, f"点赞失败: {data.get('error')}")
                self.test_results.append(("文章点赞", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}: {response.text[:200]}")
            self.test_results.append(("文章点赞", False))
        
        time.sleep(1)
        
        # 2. 再次点赞（应该取消点赞）
        print("\n2. 测试取消点赞...")
        response = requests.post(
            f"{self.api_base}/newsletters/{self.newsletter_id}/like",
            json={"action": "unlike"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result(True, f"取消点赞成功！当前点赞数: {data.get('likeCount')}, 是否已赞: {data.get('isLiked')}")
                self.test_results.append(("取消点赞", True))
            else:
                print_result(False, f"取消点赞失败: {data.get('error')}")
                self.test_results.append(("取消点赞", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}")
            self.test_results.append(("取消点赞", False))
    
    def test_get_comments(self):
        """测试获取评论列表"""
        print_section("测试获取评论列表")
        
        # 1. 获取最新评论
        print("\n1. 获取最新评论...")
        response = requests.get(
            f"{self.api_base}/newsletters/{self.newsletter_id}/comments",
            params={
                "page": 1,
                "pageSize": 10,
                "sortBy": "latest"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total = data.get('total', 0)
                comments = data.get('comments', [])
                print_result(True, f"获取评论成功！总数: {total}, 本页: {len(comments)}条")
                
                # 显示前3条评论
                for i, comment in enumerate(comments[:3], 1):
                    author = comment.get('author', {})
                    print(f"\n   评论{i}:")
                    print(f"     作者: {author.get('name', 'Anonymous')}")
                    print(f"     内容: {comment.get('content', '')[:100]}...")
                    print(f"     点赞: {comment.get('likeCount', 0)}, 回复: {comment.get('replyCount', 0)}")
                
                self.test_results.append(("获取评论列表", True))
            else:
                print_result(False, f"获取评论失败: {data.get('error')}")
                self.test_results.append(("获取评论列表", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}")
            self.test_results.append(("获取评论列表", False))
        
        # 2. 测试分页
        print("\n2. 测试分页（第2页）...")
        response = requests.get(
            f"{self.api_base}/newsletters/{self.newsletter_id}/comments",
            params={
                "page": 2,
                "pageSize": 5,
                "sortBy": "latest"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result(True, f"分页成功！第2页有 {len(data.get('comments', []))} 条评论")
                self.test_results.append(("评论分页", True))
            else:
                print_result(False, "分页失败")
                self.test_results.append(("评论分页", False))
    
    def test_create_comment(self):
        """测试发表评论"""
        print_section("测试发表评论")
        
        # 1. 发表主评论
        print("\n1. 发表主评论...")
        test_content = f"测试评论 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        response = requests.post(
            f"{self.api_base}/newsletters/{self.newsletter_id}/comments",
            json={
                "content": test_content,
                "parentId": None
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                comment_data = data.get('data', {})
                self.comment_id = comment_data.get('id')
                print_result(True, f"评论发表成功！评论ID: {self.comment_id}")
                print(f"   内容: {comment_data.get('content')}")
                print(f"   作者: {comment_data.get('author', {}).get('name', 'Anonymous')}")
                self.test_results.append(("发表主评论", True))
            else:
                print_result(False, f"发表评论失败: {data.get('error')}")
                self.test_results.append(("发表主评论", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}: {response.text[:200]}")
            self.test_results.append(("发表主评论", False))
        
        time.sleep(1)
        
        # 2. 发表回复
        if self.comment_id:
            print("\n2. 发表回复评论...")
            reply_content = f"回复测试 - {datetime.now().strftime('%H:%M:%S')}"
            
            response = requests.post(
                f"{self.api_base}/newsletters/{self.newsletter_id}/comments",
                json={
                    "content": reply_content,
                    "parentId": self.comment_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    reply_data = data.get('data', {})
                    print_result(True, f"回复发表成功！回复ID: {reply_data.get('id')}")
                    self.test_results.append(("发表回复", True))
                else:
                    print_result(False, f"发表回复失败: {data.get('error')}")
                    self.test_results.append(("发表回复", False))
            else:
                print_result(False, f"HTTP错误 {response.status_code}")
                self.test_results.append(("发表回复", False))
        
        # 3. 测试空内容
        print("\n3. 测试空内容（应该失败）...")
        response = requests.post(
            f"{self.api_base}/newsletters/{self.newsletter_id}/comments",
            json={
                "content": "",
                "parentId": None
            }
        )
        
        if response.status_code == 400:
            print_result(True, "正确拒绝了空内容")
            self.test_results.append(("拒绝空内容", True))
        else:
            print_result(False, "未能正确处理空内容")
            self.test_results.append(("拒绝空内容", False))
    
    def test_comment_like(self):
        """测试评论点赞"""
        print_section("测试评论点赞")
        
        if not self.comment_id:
            print_result(False, "没有可用的评论ID，跳过测试")
            return
        
        # 1. 点赞评论
        print("\n1. 点赞评论...")
        response = requests.post(
            f"{self.api_base}/newsletters/comments/{self.comment_id}/like",
            json={"action": "like"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result(True, f"评论点赞成功！点赞数: {data.get('likeCount')}")
                self.test_results.append(("评论点赞", True))
            else:
                print_result(False, f"评论点赞失败: {data.get('error')}")
                self.test_results.append(("评论点赞", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}")
            self.test_results.append(("评论点赞", False))
        
        time.sleep(1)
        
        # 2. 取消点赞
        print("\n2. 取消评论点赞...")
        response = requests.post(
            f"{self.api_base}/newsletters/comments/{self.comment_id}/like",
            json={"action": "unlike"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result(True, f"取消点赞成功！点赞数: {data.get('likeCount')}")
                self.test_results.append(("取消评论点赞", True))
            else:
                print_result(False, f"取消点赞失败: {data.get('error')}")
                self.test_results.append(("取消评论点赞", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}")
            self.test_results.append(("取消评论点赞", False))
    
    def test_comment_replies(self):
        """测试获取评论回复"""
        print_section("测试获取评论回复")
        
        if not self.comment_id:
            print_result(False, "没有可用的评论ID，跳过测试")
            return
        
        print("\n获取评论的回复...")
        response = requests.get(
            f"{self.api_base}/newsletters/comments/{self.comment_id}/replies",
            params={
                "page": 1,
                "pageSize": 10
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total = data.get('total', 0)
                replies = data.get('replies', [])
                print_result(True, f"获取回复成功！总数: {total}, 本页: {len(replies)}条")
                
                for i, reply in enumerate(replies[:3], 1):
                    author = reply.get('author', {})
                    print(f"\n   回复{i}:")
                    print(f"     作者: {author.get('name', 'Anonymous')}")
                    print(f"     内容: {reply.get('content', '')[:100]}...")
                
                self.test_results.append(("获取评论回复", True))
            else:
                print_result(False, f"获取回复失败: {data.get('error')}")
                self.test_results.append(("获取评论回复", False))
        else:
            print_result(False, f"HTTP错误 {response.status_code}")
            self.test_results.append(("获取评论回复", False))
    
    def print_summary(self):
        """打印测试总结"""
        print_section("测试总结")
        
        total = len(self.test_results)
        passed = sum(1 for _, success in self.test_results if success)
        failed = total - passed
        
        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for name, success in self.test_results:
                if not success:
                    print(f"  - {name}")
        
        print("\n详细结果:")
        for name, success in self.test_results:
            status = "✅" if success else "❌"
            print(f"  {status} {name}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("🚀 Newsletter交互API测试")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 API地址: {self.api_base}")
        print("="*80)
        
        # 检查服务器
        try:
            response = requests.get("http://localhost:9011/health")
            if response.status_code != 200:
                print("❌ 服务器未运行！")
                return False
        except:
            print("❌ 无法连接到服务器！")
            print("请先启动后端服务:")
            print("  cd minio-file-manager/backend")
            print("  python3 -m uvicorn app.main:app --reload --port 9011")
            return False
        
        print("✅ 服务器运行正常\n")
        
        # 准备测试
        if not self.setup():
            print("❌ 测试准备失败")
            return False
        
        # 运行测试
        try:
            self.test_newsletter_like()
            time.sleep(1)
            
            self.test_get_comments()
            time.sleep(1)
            
            self.test_create_comment()
            time.sleep(1)
            
            self.test_comment_like()
            time.sleep(1)
            
            self.test_comment_replies()
            
        except Exception as e:
            print(f"\n❌ 测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 打印总结
        self.print_summary()
        
        return True


def main():
    """主函数"""
    tester = NewsletterAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n" + "="*80)
        print("✅ Newsletter交互API测试完成！")
        print("="*80)
        
        print("\n📚 API文档地址:")
        print("  - Swagger UI: http://localhost:9011/docs")
        print("  - ReDoc: http://localhost:9011/redoc")
        
        print("\n🔍 可用的API端点:")
        print("  - POST /api/v1/newsletters/{id}/like - 文章点赞")
        print("  - GET  /api/v1/newsletters/{id}/comments - 获取评论")
        print("  - POST /api/v1/newsletters/{id}/comments - 发表评论")
        print("  - POST /api/v1/newsletters/comments/{id}/like - 评论点赞")
        print("  - GET  /api/v1/newsletters/comments/{id}/replies - 获取回复")


if __name__ == "__main__":
    main()