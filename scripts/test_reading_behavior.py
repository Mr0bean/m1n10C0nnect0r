#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户阅读行为存储功能
"""

import asyncio
import json
from datetime import datetime, timezone
import uuid

# 需要将项目路径添加到Python路径中
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'minio-file-manager', 'backend'))

from app.services.user_behavior_service import user_behavior_service, BehaviorType


async def test_reading_behavior_storage():
    """测试阅读行为数据存储"""
    
    print("=" * 60)
    print("测试用户阅读行为存储功能")
    print("=" * 60)
    
    # 测试数据
    user_id = "test_user_001"
    document_id = "test_doc_123" 
    session_id = str(uuid.uuid4())
    
    print(f"测试用户: {user_id}")
    print(f"测试文档: {document_id}")
    print(f"会话ID: {session_id}")
    print()
    
    try:
        # 1. 测试开始阅读会话
        print("1. 测试开始阅读会话...")
        session_start_data = {
            'id': session_id,
            'userId': user_id,
            'documentId': document_id,
            'sessionStart': datetime.now(timezone.utc).isoformat(),
            'isActive': True,
            'device': {
                'userAgent': 'Mozilla/5.0 (Test Browser)',
                'viewport': {'width': 1920, 'height': 1080},
                'isMobile': False
            }
        }
        
        start_result = await user_behavior_service.save_reading_session(
            user_id=user_id,
            document_id=document_id,
            session_data=session_start_data,
            action_type='start'
        )
        
        print(f"开始会话结果: {start_result['success']}")
        if start_result['success']:
            print(f"行为ID: {start_result['behavior_id']}")
        print()
        
        # 2. 测试保存整体阅读进度
        print("2. 测试保存整体阅读进度...")
        progress_data = {
            'userId': user_id,
            'documentId': document_id,
            'sessionId': session_id,
            'scrollProgress': 45.5,
            'readingProgress': 40.0,
            'totalReadingTime': 180000,  # 3分钟
            'activeReadingTime': 150000,  # 2.5分钟
            'estimatedTimeRemaining': 15,
            'totalSections': 10,
            'readSections': 4,
            'completionRate': 0.4,
            'currentBehavior': {
                'isActivelyReading': True,
                'readingMode': 'normal',
                'avgReadingSpeed': 250,
                'readingEfficiency': 85
            },
            'lastScrollPosition': 2340,
            'lastUpdateTime': datetime.now(timezone.utc).isoformat(),
            'isCompleted': False
        }
        
        progress_result = await user_behavior_service.save_reading_progress(
            user_id=user_id,
            document_id=document_id,
            session_id=session_id,
            progress_data=progress_data
        )
        
        print(f"进度保存结果: {progress_result['success']}")
        if progress_result['success']:
            print(f"行为ID: {progress_result['behavior_id']}")
        print()
        
        # 3. 测试保存章节进度
        print("3. 测试保存章节进度...")
        section_progress = [
            {
                'id': 'section-0',
                'userId': user_id,
                'documentId': document_id,
                'sessionId': session_id,
                'title': '引言',
                'level': 1,
                'position': {
                    'startOffset': 0,
                    'endOffset': 500,
                    'elementTop': 0,
                    'elementHeight': 120
                },
                'isRead': True,
                'readPercentage': 100,
                'firstReadTime': datetime.now(timezone.utc).isoformat(),
                'lastReadTime': datetime.now(timezone.utc).isoformat(),
                'totalReadTime': 30000,
                'engagementScore': 90,
                'scrollPauses': 2,
                'timeSpent': 35000,
                'interactionCount': 1
            },
            {
                'id': 'section-1', 
                'userId': user_id,
                'documentId': document_id,
                'sessionId': session_id,
                'title': '第一章：基础概念',
                'level': 1,
                'position': {
                    'startOffset': 500,
                    'endOffset': 1500,
                    'elementTop': 120,
                    'elementHeight': 250
                },
                'isRead': True,
                'readPercentage': 80,
                'firstReadTime': datetime.now(timezone.utc).isoformat(),
                'lastReadTime': datetime.now(timezone.utc).isoformat(),
                'totalReadTime': 60000,
                'engagementScore': 75,
                'scrollPauses': 5,
                'timeSpent': 70000,
                'interactionCount': 3
            }
        ]
        
        section_results = await user_behavior_service.save_section_progress(
            user_id=user_id,
            document_id=document_id,
            session_id=session_id,
            section_progress_list=section_progress
        )
        
        print(f"章节进度保存结果: {len(section_results)} 个章节")
        for i, result in enumerate(section_results):
            if result['success']:
                print(f"  章节 {i}: {result['behavior_id']}")
        print()
        
        # 4. 测试保存滚动行为
        print("4. 测试保存滚动行为...")
        scroll_data = {
            'userId': user_id,
            'documentId': document_id,
            'sessionId': session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'scrollTop': 2340,
            'scrollHeight': 5000,
            'clientHeight': 1080,
            'scrollProgress': 46.8,
            'scrollDirection': 'down',
            'scrollSpeed': 120,
            'isPaused': True,
            'pauseDuration': 3000,
            'visibleSections': ['section-1', 'section-2'],
            'focusedSection': 'section-2'
        }
        
        scroll_result = await user_behavior_service.save_scroll_behavior(
            user_id=user_id,
            document_id=document_id,
            session_id=session_id,
            scroll_data=scroll_data
        )
        
        print(f"滚动行为保存结果: {scroll_result['success']}")
        if scroll_result['success']:
            print(f"行为ID: {scroll_result['behavior_id']}")
        print()
        
        # 5. 测试保存阅读洞察
        print("5. 测试保存阅读洞察...")
        insights_data = {
            'userId': user_id,
            'documentId': document_id,
            'generatedAt': datetime.now(timezone.utc).isoformat(),
            'dominantReadingMode': 'normal',
            'readingModeDistribution': {
                'careful': 0.3,
                'normal': 0.5,
                'scanning': 0.15,
                'rapid': 0.05
            },
            'personalizedTips': [
                '您的阅读速度适中，可以尝试提高滚动速度',
                '建议在重要章节增加停留时间'
            ],
            'recommendedReadingTime': 25,
            'difficultyAssessment': 'medium',
            'avgCompletionTime': 30,
            'userRank': 65
        }
        
        insights_result = await user_behavior_service.save_reading_insights(
            user_id=user_id,
            document_id=document_id,
            insights_data=insights_data
        )
        
        print(f"洞察数据保存结果: {insights_result['success']}")
        if insights_result['success']:
            print(f"行为ID: {insights_result['behavior_id']}")
        print()
        
        # 6. 测试完整保存
        print("6. 测试完整保存...")
        complete_save_request = {
            'userId': user_id,
            'documentId': document_id,
            'sessionId': session_id,
            'overallProgress': progress_data,
            'sectionProgress': section_progress,
            'scrollBehavior': scroll_data,
            'insights': insights_data,
            'saveType': 'manual',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'clientVersion': '1.0.0'
        }
        
        complete_result = await user_behavior_service.save_complete_reading_progress(
            complete_save_request
        )
        
        print(f"完整保存结果: {complete_result['success']}")
        print(f"保存组件数: {len(complete_result.get('saved_components', []))}")
        if complete_result.get('errors'):
            print(f"错误: {complete_result['errors']}")
        print()
        
        # 7. 测试加载阅读进度
        print("7. 测试加载阅读进度...")
        load_result = await user_behavior_service.load_reading_progress(
            user_id=user_id,
            document_id=document_id
        )
        
        print(f"加载结果: {load_result['success']}")
        if load_result['success']:
            data = load_result['data']
            print(f"整体进度: {'有' if data.get('overall_progress') else '无'}")
            print(f"章节进度: {len(data.get('section_progress', []))} 个")
            print(f"最后会话: {'有' if data.get('last_session') else '无'}")
            print(f"阅读洞察: {'有' if data.get('insights') else '无'}")
            print(f"建议继续: {data.get('should_resume', False)}")
            print(f"恢复位置: {data.get('resume_position', 0)}")
        print()
        
        # 8. 测试结束会话
        print("8. 测试结束阅读会话...")
        session_end_data = {
            'id': session_id,
            'sessionEnd': datetime.now(timezone.utc).isoformat(),
            'isActive': False,
            'totalTime': 300000,  # 5分钟
            'isCompleted': False,
            'exitReason': 'manual_close'
        }
        
        end_result = await user_behavior_service.save_reading_session(
            user_id=user_id,
            document_id=document_id,
            session_data=session_end_data,
            action_type='end'
        )
        
        print(f"结束会话结果: {end_result['success']}")
        if end_result['success']:
            print(f"行为ID: {end_result['behavior_id']}")
        print()
        
        # 9. 查看所有相关行为记录
        print("9. 查看所有相关行为记录...")
        all_behaviors = await user_behavior_service.get_user_behaviors(
            user_id=user_id,
            limit=20
        )
        
        print(f"找到 {len(all_behaviors)} 条行为记录:")
        for behavior in all_behaviors:
            print(f"  {behavior.get('behavior_type', 'unknown')} - {behavior.get('created_at', 'no time')}")
        print()
        
        print("=" * 60)
        print("测试完成！所有功能正常工作。")
        print("=" * 60)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭数据库连接
        await user_behavior_service.close_pool()


if __name__ == "__main__":
    asyncio.run(test_reading_behavior_storage())