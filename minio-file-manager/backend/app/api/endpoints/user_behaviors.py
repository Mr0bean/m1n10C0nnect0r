#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户行为追踪API端点
提供记录和查询用户行为的接口
"""

from fastapi import APIRouter, HTTPException, Query, Header, Request
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid

from app.services.user_behavior_service import user_behavior_service, BehaviorType

router = APIRouter(prefix="/user-behaviors", tags=["User Behaviors"])


class RecordBehaviorRequest(BaseModel):
    """记录用户行为请求模型"""
    behavior_type: BehaviorType = Field(..., description="行为类型")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    target_type: Optional[str] = Field(None, description="目标类型")
    target_id: Optional[str] = Field(None, description="目标ID")
    action_details: Optional[Dict[str, Any]] = Field(None, description="行为详细信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class BehaviorResponse(BaseModel):
    """行为记录响应模型"""
    success: bool
    behavior_id: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


class BehaviorQueryResponse(BaseModel):
    """行为查询响应模型"""
    behaviors: List[Dict[str, Any]]
    total: int
    page: int
    size: int


class BehaviorStatisticsResponse(BaseModel):
    """行为统计响应模型"""
    total_behaviors: int
    unique_users: int
    unique_sessions: int
    behavior_counts: Dict[str, int]
    period: Dict[str, str]


class PopularTargetsResponse(BaseModel):
    """热门目标响应模型"""
    target_type: str
    targets: List[Dict[str, Any]]
    period: Dict[str, str]


@router.post("/record", response_model=BehaviorResponse)
async def record_behavior(
    request: RecordBehaviorRequest,
    http_request: Request,
    user_agent: Optional[str] = Header(None),
    referer: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    记录用户行为
    
    - **behavior_type**: 行为类型（必填）
    - **user_id**: 用户ID（可选）
    - **session_id**: 会话ID（可选，可从Header获取）
    - **target_type**: 目标类型（如：newsletter, document等）
    - **target_id**: 目标ID
    - **action_details**: 行为详细信息
    - **metadata**: 额外元数据
    """
    try:
        # 获取客户端IP
        client_ip = http_request.client.host if http_request.client else None
        
        # 如果没有提供session_id，使用header中的或生成一个
        session_id = request.session_id or x_session_id or str(uuid.uuid4())
        
        # 记录行为
        result = await user_behavior_service.record_behavior(
            behavior_type=request.behavior_type.value,
            user_id=request.user_id,
            session_id=session_id,
            target_type=request.target_type,
            target_id=request.target_id,
            action_details=request.action_details,
            metadata=request.metadata,
            ip_address=client_ip,
            user_agent=user_agent,
            referer=referer
        )
        
        if result['success']:
            return BehaviorResponse(
                success=True,
                behavior_id=result['behavior_id'],
                created_at=result['created_at']
            )
        else:
            return BehaviorResponse(
                success=False,
                error=result.get('error', 'Unknown error')
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query", response_model=BehaviorQueryResponse)
async def query_behaviors(
    user_id: Optional[str] = Query(None, description="用户ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    behavior_type: Optional[BehaviorType] = Query(None, description="行为类型"),
    target_type: Optional[str] = Query(None, description="目标类型"),
    target_id: Optional[str] = Query(None, description="目标ID"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    查询用户行为记录
    
    支持多种过滤条件：
    - 用户ID
    - 会话ID
    - 行为类型
    - 目标类型和ID
    - 时间范围
    """
    try:
        # 解析时间参数
        start_time = None
        end_time = None
        
        if start_date:
            start_time = datetime.strptime(start_date, "%Y-%m-%d")
        
        if end_date:
            end_time = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        # 计算分页
        offset = (page - 1) * size
        
        # 查询行为记录
        behaviors = await user_behavior_service.get_user_behaviors(
            user_id=user_id,
            session_id=session_id,
            behavior_type=behavior_type.value if behavior_type else None,
            target_type=target_type,
            target_id=target_id,
            start_time=start_time,
            end_time=end_time,
            limit=size,
            offset=offset
        )
        
        return BehaviorQueryResponse(
            behaviors=behaviors,
            total=len(behaviors),  # 实际应该从数据库获取总数
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=BehaviorStatisticsResponse)
async def get_behavior_statistics(
    user_id: Optional[str] = Query(None, description="用户ID"),
    behavior_type: Optional[BehaviorType] = Query(None, description="行为类型"),
    days: int = Query(7, ge=1, le=365, description="统计天数")
):
    """
    获取用户行为统计信息
    
    - **user_id**: 指定用户的统计（可选）
    - **behavior_type**: 指定行为类型的统计（可选）
    - **days**: 统计最近N天的数据
    """
    try:
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取统计信息
        stats = await user_behavior_service.get_behavior_statistics(
            user_id=user_id,
            behavior_type=behavior_type.value if behavior_type else None,
            start_time=start_time,
            end_time=end_time
        )
        
        return BehaviorStatisticsResponse(
            total_behaviors=stats['total_behaviors'],
            unique_users=stats['unique_users'],
            unique_sessions=stats['unique_sessions'],
            behavior_counts=stats['behavior_counts'],
            period={
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular/{target_type}", response_model=PopularTargetsResponse)
async def get_popular_targets(
    target_type: str,
    behavior_type: Optional[BehaviorType] = Query(None, description="行为类型"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    days: int = Query(7, ge=1, le=365, description="统计天数")
):
    """
    获取热门目标
    
    例如：
    - 最常被查看的newsletter
    - 最常被下载的文档
    - 最常被搜索的关键词
    
    - **target_type**: 目标类型（newsletter, document, search_query等）
    - **behavior_type**: 行为类型（可选）
    - **limit**: 返回数量限制
    - **days**: 统计最近N天的数据
    """
    try:
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取热门目标
        popular = await user_behavior_service.get_popular_targets(
            target_type=target_type,
            behavior_type=behavior_type.value if behavior_type else None,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        
        return PopularTargetsResponse(
            target_type=target_type,
            targets=popular,
            period={
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-record")
async def batch_record_behaviors(
    behaviors: List[RecordBehaviorRequest],
    http_request: Request,
    user_agent: Optional[str] = Header(None),
    referer: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    批量记录用户行为
    
    用于一次性记录多个用户行为，提高性能
    """
    try:
        # 获取客户端IP
        client_ip = http_request.client.host if http_request.client else None
        
        results = []
        for behavior in behaviors:
            # 如果没有提供session_id，使用header中的或生成一个
            session_id = behavior.session_id or x_session_id or str(uuid.uuid4())
            
            # 记录行为
            result = await user_behavior_service.record_behavior(
                behavior_type=behavior.behavior_type.value,
                user_id=behavior.user_id,
                session_id=session_id,
                target_type=behavior.target_type,
                target_id=behavior.target_id,
                action_details=behavior.action_details,
                metadata=behavior.metadata,
                ip_address=client_ip,
                user_agent=user_agent,
                referer=referer
            )
            results.append(result)
        
        # 统计成功和失败的数量
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count
        
        return {
            'total': len(results),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/timeline")
async def get_user_timeline(
    user_id: str,
    days: int = Query(7, ge=1, le=365, description="查看最近N天的行为"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页数量")
):
    """
    获取指定用户的行为时间线
    
    返回用户最近的所有行为记录，按时间倒序排列
    """
    try:
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 计算分页
        offset = (page - 1) * size
        
        # 查询用户行为
        behaviors = await user_behavior_service.get_user_behaviors(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=size,
            offset=offset
        )
        
        # 获取用户统计信息
        stats = await user_behavior_service.get_behavior_statistics(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            'user_id': user_id,
            'timeline': behaviors,
            'statistics': stats,
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            },
            'pagination': {
                'page': page,
                'size': size,
                'total': len(behaviors)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 阅读进度相关API - 基于前端TypeScript接口 ===

class SaveProgressRequest(BaseModel):
    """保存阅读进度请求模型 - 对应前端SaveProgressRequest接口"""
    userId: str = Field(..., description="用户ID")
    documentId: str = Field(..., description="文档ID")
    sessionId: str = Field(..., description="会话ID")
    overallProgress: Optional[Dict[str, Any]] = Field(None, description="整体阅读进度")
    sectionProgress: Optional[List[Dict[str, Any]]] = Field(None, description="章节进度列表")
    scrollBehavior: Optional[Dict[str, Any]] = Field(None, description="滚动行为数据")
    insights: Optional[Dict[str, Any]] = Field(None, description="阅读洞察数据")
    saveType: str = Field("auto", description="保存类型: auto/manual/exit")
    timestamp: str = Field(..., description="保存时间戳")
    clientVersion: Optional[str] = Field(None, description="客户端版本")


class LoadProgressResponse(BaseModel):
    """加载阅读进度响应模型 - 对应前端LoadProgressResponse接口"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/reading-progress/save", response_model=Dict[str, Any])
async def save_reading_progress(request: SaveProgressRequest):
    """
    保存完整的用户阅读进度数据
    
    支持保存：
    - 整体阅读进度 (OverallReadingProgress)
    - 章节级别进度 (SectionProgress[])
    - 滚动行为 (ScrollBehavior)
    - 阅读洞察 (ReadingInsights)
    """
    try:
        # 转换为内部格式
        save_request = {
            'userId': request.userId,
            'documentId': request.documentId,
            'sessionId': request.sessionId,
            'overallProgress': request.overallProgress,
            'sectionProgress': request.sectionProgress,
            'scrollBehavior': request.scrollBehavior,
            'insights': request.insights,
            'saveType': request.saveType,
            'timestamp': request.timestamp,
            'clientVersion': request.clientVersion
        }
        
        # 保存数据
        result = await user_behavior_service.save_complete_reading_progress(save_request)
        
        return {
            'success': result['success'],
            'message': '阅读进度保存成功' if result['success'] else '阅读进度保存失败',
            'saved_components': result.get('saved_components', []),
            'errors': result.get('errors', [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存阅读进度失败: {str(e)}")


@router.get("/reading-progress/load/{user_id}/{document_id}", response_model=LoadProgressResponse)
async def load_reading_progress(user_id: str, document_id: str):
    """
    加载用户的阅读进度数据
    
    返回：
    - 整体阅读进度
    - 章节进度列表
    - 最后会话信息
    - 阅读历史统计
    - 阅读洞察
    - 是否建议继续阅读
    - 建议恢复的位置
    """
    try:
        result = await user_behavior_service.load_reading_progress(user_id, document_id)
        
        return LoadProgressResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载阅读进度失败: {str(e)}")


class ReadingSessionRequest(BaseModel):
    """阅读会话请求模型"""
    user_id: str = Field(..., description="用户ID")
    document_id: str = Field(..., description="文档ID")
    session_data: Dict[str, Any] = Field(..., description="会话数据")
    action: str = Field(..., description="操作类型: start/end/update", pattern="^(start|end|update)$")


@router.post("/reading-session", response_model=Dict[str, Any])
async def manage_reading_session(request: ReadingSessionRequest):
    """
    管理阅读会话 - 统一的开始、更新、结束接口
    
    支持的操作：
    - start: 开始新的阅读会话
    - end: 结束当前阅读会话
    - update: 更新会话信息（如设备变化等）
    
    请求格式：
    {
        "user_id": "user123",
        "document_id": "doc456", 
        "action": "start",
        "session_data": {
            "id": "session789",
            "sessionStart": "2024-01-01T10:00:00Z",
            "sessionEnd": "2024-01-01T11:00:00Z",  // 仅end时需要
            "isActive": true,
            "device": {
                "userAgent": "Chrome/120.0",
                "viewport": {"width": 1920, "height": 1080},
                "isMobile": false
            },
            // end时的额外字段
            "totalTime": 3600000,     // 总时长（毫秒）
            "isCompleted": true,      // 是否完成阅读
            "exitReason": "finished"  // 退出原因: finished/closed/switched
        }
    }
    """
    try:
        action_messages = {
            'start': '阅读会话已开始',
            'end': '阅读会话已结束', 
            'update': '阅读会话已更新'
        }
        
        # 调用统一的会话保存方法
        result = await user_behavior_service.save_reading_session(
            user_id=request.user_id,
            document_id=request.document_id,
            session_data=request.session_data,
            action_type=request.action
        )
        
        # 如果是开始会话，还需要检查是否有未结束的会话
        if request.action == 'start':
            # 可以在这里添加自动结束旧会话的逻辑
            pass
        
        return {
            'success': result['success'],
            'action': request.action,
            'session_id': request.session_data.get('id'),
            'message': action_messages.get(request.action, '会话操作完成'),
            'behavior_id': result.get('behavior_id'),
            'created_at': result.get('created_at')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"管理阅读会话失败: {str(e)}")


@router.get("/reading-session/active/{user_id}")
async def get_active_reading_sessions(user_id: str):
    """
    获取用户当前活跃的阅读会话
    
    用于检查用户是否有正在进行的阅读会话
    """
    try:
        # 查询最近的会话开始记录
        recent_behaviors = await user_behavior_service.get_user_behaviors(
            user_id=user_id,
            behavior_type=BehaviorType.READING_SESSION_START.value,
            limit=10
        )
        
        active_sessions = []
        for behavior in recent_behaviors:
            session_id = behavior.get('session_id')
            if not session_id:
                continue
                
            # 检查是否有对应的结束记录
            end_behaviors = await user_behavior_service.get_user_behaviors(
                user_id=user_id,
                session_id=session_id,
                behavior_type=BehaviorType.READING_SESSION_END.value,
                limit=1
            )
            
            # 如果没有结束记录，认为是活跃会话
            if not end_behaviors:
                session_data = behavior.get('action_details', {})
                session_data['behavior_id'] = behavior.get('id')
                session_data['started_at'] = behavior.get('created_at')
                active_sessions.append(session_data)
        
        return {
            'user_id': user_id,
            'active_sessions': active_sessions,
            'count': len(active_sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃会话失败: {str(e)}")


@router.post("/reading-session/cleanup/{user_id}")
async def cleanup_stale_sessions(
    user_id: str,
    max_session_duration_hours: int = Query(24, description="最大会话持续时间（小时）")
):
    """
    清理过期的活跃会话
    
    自动结束超过指定时间的未结束会话
    """
    try:
        # 获取活跃会话
        active_response = await get_active_reading_sessions(user_id)
        active_sessions = active_response['active_sessions']
        
        cleaned_count = 0
        max_duration = timedelta(hours=max_session_duration_hours)
        current_time = datetime.now()
        
        for session in active_sessions:
            started_at = datetime.fromisoformat(session['started_at'].replace('Z', '+00:00'))
            
            # 检查会话是否超时
            if current_time - started_at > max_duration:
                # 自动结束超时会话
                cleanup_data = {
                    'id': session.get('id'),
                    'sessionEnd': current_time.isoformat(),
                    'isActive': False,
                    'totalTime': int((current_time - started_at).total_seconds() * 1000),
                    'isCompleted': False,
                    'exitReason': 'timeout_cleanup'
                }
                
                await user_behavior_service.save_reading_session(
                    user_id=user_id,
                    document_id=session.get('documentId', ''),
                    session_data=cleanup_data,
                    action_type='end'
                )
                cleaned_count += 1
        
        return {
            'user_id': user_id,
            'cleaned_sessions': cleaned_count,
            'remaining_active': len(active_sessions) - cleaned_count,
            'max_duration_hours': max_session_duration_hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理过期会话失败: {str(e)}")


@router.get("/reading-analytics/user/{user_id}")
async def get_user_reading_analytics(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="分析最近N天的数据")
):
    """
    获取用户阅读分析数据
    
    包括：
    - 阅读习惯分析
    - 阅读进度统计
    - 设备使用情况
    - 阅读模式分布
    """
    try:
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取阅读相关行为
        reading_behaviors = await user_behavior_service.get_user_behaviors(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # 过滤阅读相关行为
        reading_sessions = [b for b in reading_behaviors if b['behavior_type'] in [
            'reading_session_start', 'reading_session_end', 'reading_progress_update'
        ]]
        
        # 统计分析
        total_sessions = len([b for b in reading_sessions if b['behavior_type'] == 'reading_session_start'])
        total_documents = len(set(b['target_id'] for b in reading_sessions if b['target_id']))
        
        # 设备统计
        device_stats = {}
        for behavior in reading_sessions:
            device_info = behavior.get('metadata', {}).get('device', {})
            is_mobile = device_info.get('is_mobile', False)
            device_type = 'mobile' if is_mobile else 'desktop'
            device_stats[device_type] = device_stats.get(device_type, 0) + 1
        
        # 阅读模式统计
        reading_modes = {}
        for behavior in reading_sessions:
            current_behavior = behavior.get('metadata', {}).get('current_behavior', {})
            mode = current_behavior.get('reading_mode', 'normal')
            reading_modes[mode] = reading_modes.get(mode, 0) + 1
        
        return {
            'user_id': user_id,
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'days': days
            },
            'statistics': {
                'total_sessions': total_sessions,
                'total_documents_read': total_documents,
                'avg_sessions_per_day': round(total_sessions / days, 2),
                'device_distribution': device_stats,
                'reading_mode_distribution': reading_modes
            },
            'raw_data_count': len(reading_behaviors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取阅读分析失败: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_behaviors(
    days: int = Query(90, ge=1, description="删除N天前的行为记录"),
    dry_run: bool = Query(True, description="是否为演练模式（不实际删除）")
):
    """
    清理旧的行为记录
    
    用于定期清理过期的行为记录，保持数据库性能
    
    - **days**: 删除N天前的记录
    - **dry_run**: 如果为true，只返回将要删除的数量，不实际删除
    """
    # 这里只是示例，实际实现需要在service中添加相应方法
    return {
        'message': f"{'将要' if dry_run else '已'}删除{days}天前的行为记录",
        'dry_run': dry_run
    }