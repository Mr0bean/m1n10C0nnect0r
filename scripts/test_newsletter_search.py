#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Newsletter搜索功能脚本
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'minio-file-manager', 'backend')
sys.path.insert(0, backend_path)

from app.services.newsletter_search_service import newsletter_search_service


async def test_basic_search():
    """测试基本搜索功能"""
    print("\n" + "="*60)
    print("📝 测试基本搜索功能")
    print("="*60)
    
    # 测试关键词列表
    test_queries = [
        "AI",
        "agent",
        "GPT",
        "机器学习",
        "深度学习",
        "LLM",
        "transformer",
        "neural network"
    ]
    
    for query in test_queries:
        print(f"\n🔍 搜索关键词: '{query}'")
        print("-" * 40)
        
        result = await newsletter_search_service.search_articles(
            query=query,
            from_=0,
            size=5,
            sort_by="_score",
            highlight=True
        )
        
        if result.get("success"):
            total = result.get("total", 0)
            print(f"✅ 找到 {total} 个结果")
            
            for i, article in enumerate(result.get("results", []), 1):
                print(f"\n  {i}. 标题: {article.get('title', 'N/A')}")
                print(f"     副标题: {article.get('subtitle', 'N/A')[:50]}...")
                print(f"     相关度评分: {article.get('score', 0):.2f}")
                print(f"     发布日期: {article.get('post_date', 'N/A')}")
                print(f"     类型: {article.get('type', 'N/A')}")
                print(f"     字数: {article.get('wordcount', 0)}")
                
                # 显示高亮内容
                highlight = article.get('highlight', {})
                if highlight:
                    print("     高亮内容:")
                    for field, fragments in highlight.items():
                        for fragment in fragments[:1]:  # 只显示第一个片段
                            print(f"       - {field}: {fragment[:100]}...")
        else:
            print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
    
    print("\n" + "="*60)


async def test_advanced_search():
    """测试高级搜索功能"""
    print("\n" + "="*60)
    print("🔬 测试高级搜索功能")
    print("="*60)
    
    # 测试不同的过滤条件
    test_cases = [
        {
            "name": "按类型过滤",
            "params": {
                "article_type": "newsletter",
                "size": 5
            }
        },
        {
            "name": "按日期范围过滤",
            "params": {
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
                "size": 5
            }
        },
        {
            "name": "按字数范围过滤",
            "params": {
                "min_wordcount": 1000,
                "max_wordcount": 5000,
                "size": 5
            }
        },
        {
            "name": "组合条件搜索",
            "params": {
                "query": "AI",
                "article_type": "newsletter",
                "min_wordcount": 500,
                "size": 5,
                "sort_by": "popularity_score"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 测试场景: {test_case['name']}")
        print("-" * 40)
        
        result = await newsletter_search_service.search_with_filters(
            **test_case['params']
        )
        
        if result.get("success"):
            total = result.get("total", 0)
            print(f"✅ 找到 {total} 个结果")
            
            # 显示过滤条件
            filters = result.get("filters", {})
            print("\n应用的过滤条件:")
            for key, value in filters.items():
                if value is not None:
                    print(f"  - {key}: {value}")
            
            # 显示前3个结果
            for i, article in enumerate(result.get("results", [])[:3], 1):
                print(f"\n  {i}. {article.get('title', 'N/A')}")
                print(f"     类型: {article.get('type', 'N/A')}")
                print(f"     日期: {article.get('post_date', 'N/A')}")
                print(f"     字数: {article.get('wordcount', 0)}")
                
                scores = article.get('scores', {})
                print(f"     评分: 流行度={scores.get('popularity', 0):.1f}, "
                      f"新鲜度={scores.get('freshness', 0):.1f}, "
                      f"质量={scores.get('quality', 0):.1f}")
        else:
            print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
    
    print("\n" + "="*60)


async def test_sorting():
    """测试不同排序方式"""
    print("\n" + "="*60)
    print("📈 测试排序功能")
    print("="*60)
    
    query = "AI"
    sort_options = [
        ("_score", "相关度"),
        ("post_date", "发布日期"),
        ("popularity_score", "流行度"),
        ("combined_score", "综合评分")
    ]
    
    for sort_by, sort_name in sort_options:
        print(f"\n🔀 按{sort_name}排序 (sort_by={sort_by})")
        print("-" * 40)
        
        result = await newsletter_search_service.search_articles(
            query=query,
            from_=0,
            size=3,
            sort_by=sort_by,
            highlight=False
        )
        
        if result.get("success"):
            for i, article in enumerate(result.get("results", []), 1):
                print(f"  {i}. {article.get('title', 'N/A')[:60]}...")
                
                if sort_by == "_score":
                    print(f"     相关度: {article.get('score', 0):.2f}")
                elif sort_by == "post_date":
                    print(f"     日期: {article.get('post_date', 'N/A')}")
                elif sort_by == "popularity_score":
                    print(f"     流行度: {article.get('popularity_score', 0):.1f}")
                elif sort_by == "combined_score":
                    print(f"     综合评分: {article.get('combined_score', 0):.1f}")
        else:
            print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
    
    print("\n" + "="*60)


async def test_pagination():
    """测试分页功能"""
    print("\n" + "="*60)
    print("📄 测试分页功能")
    print("="*60)
    
    query = "AI"
    page_size = 5
    
    # 获取前3页
    for page in range(3):
        from_ = page * page_size
        
        print(f"\n📖 第 {page + 1} 页 (from={from_}, size={page_size})")
        print("-" * 40)
        
        result = await newsletter_search_service.search_articles(
            query=query,
            from_=from_,
            size=page_size,
            sort_by="_score",
            highlight=False
        )
        
        if result.get("success"):
            total = result.get("total", 0)
            total_pages = (total + page_size - 1) // page_size
            
            print(f"总共 {total} 条记录，共 {total_pages} 页")
            
            for i, article in enumerate(result.get("results", []), 1):
                global_index = from_ + i
                print(f"  {global_index}. {article.get('title', 'N/A')[:50]}...")
        else:
            print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
            break
    
    print("\n" + "="*60)


async def test_empty_search():
    """测试空搜索和错误处理"""
    print("\n" + "="*60)
    print("🔧 测试空搜索和错误处理")
    print("="*60)
    
    # 测试空关键词
    print("\n测试1: 空关键词搜索")
    result = await newsletter_search_service.search_articles(
        query="",
        from_=0,
        size=5
    )
    
    if result.get("success"):
        print(f"✅ 空搜索成功，返回 {result.get('total', 0)} 个结果")
    else:
        print(f"❌ 空搜索失败: {result.get('error', '未知错误')}")
    
    # 测试不存在的关键词
    print("\n测试2: 不存在的关键词")
    result = await newsletter_search_service.search_articles(
        query="xyzabc123456789",
        from_=0,
        size=5
    )
    
    if result.get("success"):
        total = result.get("total", 0)
        if total == 0:
            print("✅ 正确返回0个结果")
        else:
            print(f"⚠️  意外找到 {total} 个结果")
    else:
        print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
    
    # 测试无效的排序字段
    print("\n测试3: 无效的排序字段")
    result = await newsletter_search_service.search_articles(
        query="AI",
        from_=0,
        size=5,
        sort_by="invalid_field"
    )
    
    if result.get("success"):
        print("⚠️  使用无效排序字段但仍返回结果")
    else:
        print(f"✅ 正确处理错误: {result.get('error', '未知错误')}")
    
    print("\n" + "="*60)


async def main():
    """主函数"""
    print("="*80)
    print("🚀 Newsletter搜索功能测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # 运行各项测试
        await test_basic_search()
        await test_advanced_search()
        await test_sorting()
        await test_pagination()
        await test_empty_search()
        
        print("\n" + "="*80)
        print("✅ 所有测试完成!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        await newsletter_search_service.close()


if __name__ == "__main__":
    asyncio.run(main())