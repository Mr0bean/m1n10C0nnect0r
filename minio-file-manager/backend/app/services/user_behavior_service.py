#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户行为追踪服务
记录和分析用户在系统中的各种操作行为
"""

import asyncpg
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json
import logging
from enum import Enum
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BehaviorType(str, Enum):
    """用户行为类型枚举"""
    # 搜索相关
    SEARCH_QUERY = "search_query"
    SEARCH_RESULT_CLICK = "search_result_click"
    SEARCH_FILTER_APPLY = "search_filter_apply"
    
    # 文档操作
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_SHARE = "document_share"
    
    # Newsletter相关
    NEWSLETTER_VIEW = "newsletter_view"
    NEWSLETTER_LIKE = "newsletter_like"
    NEWSLETTER_SHARE = "newsletter_share"
    NEWSLETTER_COMMENT = "newsletter_comment"
    
    # 系统操作
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PAGE_VIEW = "page_view"
    FEATURE_USE = "feature_use"
    
    # MinIO操作
    BUCKET_CREATE = "bucket_create"
    BUCKET_DELETE = "bucket_delete"
    OBJECT_LIST = "object_list"
    
    # 阅读行为相关 - 基于前端TypeScript接口设计
    READING_SESSION_START = "reading_session_start"      # 阅读会话开始
    READING_SESSION_END = "reading_session_end"          # 阅读会话结束
    READING_PROGRESS_UPDATE = "reading_progress_update"  # 阅读进度更新
    SECTION_PROGRESS_UPDATE = "section_progress_update"  # 章节进度更新
    SCROLL_BEHAVIOR_TRACK = "scroll_behavior_track"      # 滚动行为追踪
    READING_INSIGHTS_GENERATED = "reading_insights_generated"  # 阅读洞察生成


class UserBehaviorService:
    """用户行为追踪服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pool = None
    
    def _safe_get_metadata_value(self, behavior_dict, key, default=None):
        """安全地从behavior的metadata中获取值"""
        if not behavior_dict:
            return default
        
        metadata = behavior_dict.get('metadata', {})
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
            except:
                return default
        
        if isinstance(metadata, dict):
            return metadata.get(key, default)
        
        return default
        
    async def get_pool(self) -> asyncpg.Pool:
        """获取数据库连接池"""
        if self.pool is None:
            logger.info("初始化用户行为服务PostgreSQL连接池")
            try:
                self.pool = await asyncpg.create_pool(
                    host=self.settings.postgres_host,
                    port=self.settings.postgres_port,
                    database=self.settings.postgres_database,
                    user=self.settings.postgres_user,
                    password=self.settings.postgres_password,
                    min_size=1,
                    max_size=10
                )
                # 表已经存在，不需要创建
            except Exception as e:
                logger.error(f"创建PostgreSQL连接池失败: {str(e)}")
                raise
        return self.pool
    
    async def ensure_table_exists(self):
        """确保user_behaviors表存在"""
        pool = await self.get_pool()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.user_behaviors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255),
            session_id VARCHAR(255),
            behavior_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(255),
            action_details JSONB,
            metadata JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            referer TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- 索引
            CONSTRAINT user_behaviors_behavior_type_check 
                CHECK (behavior_type IN (
                    'search_query', 'search_result_click', 'search_filter_apply',
                    'document_view', 'document_download', 'document_upload', 
                    'document_delete', 'document_share',
                    'newsletter_view', 'newsletter_like', 'newsletter_share', 
                    'newsletter_comment',
                    'user_login', 'user_logout', 'page_view', 'feature_use',
                    'bucket_create', 'bucket_delete', 'object_list'
                ))
        );
        
        -- 创建索引以提高查询性能
        CREATE INDEX IF NOT EXISTS idx_user_behaviors_user_id 
            ON public.user_behaviors(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_behaviors_session_id 
            ON public.user_behaviors(session_id);
        CREATE INDEX IF NOT EXISTS idx_user_behaviors_behavior_type 
            ON public.user_behaviors(behavior_type);
        CREATE INDEX IF NOT EXISTS idx_user_behaviors_created_at 
            ON public.user_behaviors(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_user_behaviors_target 
            ON public.user_behaviors(target_type, target_id);
        """
        
        try:
            async with pool.acquire() as conn:
                await conn.execute(create_table_query)
                logger.info("user_behaviors表已准备就绪")
        except Exception as e:
            logger.error(f"创建user_behaviors表失败: {str(e)}")
            raise
    
    async def close_pool(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def record_behavior(
        self,
        behavior_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        action_details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录用户行为
        
        Args:
            behavior_type: 行为类型（必须是BehaviorType枚举值）
            user_id: 用户ID（可选，未登录用户为空）
            session_id: 会话ID（用于追踪匿名用户）
            target_type: 目标类型（如：newsletter, document, bucket等）
            target_id: 目标ID
            action_details: 行为详细信息（如搜索关键词、过滤条件等）
            metadata: 额外元数据
            ip_address: 用户IP地址
            user_agent: 用户浏览器信息
            referer: 来源页面
        
        Returns:
            插入的记录信息
        """
        pool = await self.get_pool()
        
        # 准备JSON数据
        action_details_json = json.dumps(action_details) if action_details else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        # 使用现有表结构的列名，生成UUID作为ID
        query = """
            INSERT INTO public.user_behaviors (
                id, "userId", action, "targetType", "targetId", metadata, "createdAt"
            ) VALUES (
                gen_random_uuid()::text, $1, $2, $3, $4, $5::jsonb, $6
            )
            RETURNING id, "createdAt"
        """
        
        try:
            async with pool.acquire() as conn:
                # 合并所有信息到metadata中
                combined_metadata = metadata or {}
                combined_metadata.update({
                    'session_id': session_id,
                    'action_details': action_details,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'referer': referer
                })
                combined_metadata_json = json.dumps(combined_metadata)
                
                row = await conn.fetchrow(
                    query,
                    user_id or None,  # Use NULL for anonymous users
                    behavior_type,
                    target_type or '',
                    target_id or '',  # Use empty string instead of NULL
                    combined_metadata_json,
                    datetime.now()
                )
                
                logger.info(
                    f"记录用户行为: type={behavior_type}, "
                    f"user={user_id or 'anonymous'}, "
                    f"target={target_type}:{target_id}"
                )
                
                return {
                    'success': True,
                    'behavior_id': str(row['id']),
                    'created_at': row['createdAt'].isoformat()
                }
                
        except Exception as e:
            logger.error(f"记录用户行为失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_user_behaviors(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        behavior_type: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询用户行为记录
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            behavior_type: 行为类型
            target_type: 目标类型
            target_id: 目标ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            offset: 偏移量
        
        Returns:
            行为记录列表
        """
        pool = await self.get_pool()
        
        # 构建查询条件
        conditions = []
        params = []
        param_count = 0
        
        if user_id:
            param_count += 1
            conditions.append(f'"userId" = ${param_count}')
            params.append(user_id)
        
        if session_id:
            param_count += 1
            conditions.append(f"metadata->>'session_id' = ${param_count}")
            params.append(session_id)
        
        if behavior_type:
            param_count += 1
            conditions.append(f"action = ${param_count}")
            params.append(behavior_type)
        
        if target_type:
            param_count += 1
            conditions.append(f'"targetType" = ${param_count}')
            params.append(target_type)
        
        if target_id:
            param_count += 1
            conditions.append(f'"targetId" = ${param_count}')
            params.append(target_id)
        
        if start_time:
            param_count += 1
            conditions.append(f'"createdAt" >= ${param_count}')
            params.append(start_time)
        
        if end_time:
            param_count += 1
            conditions.append(f'"createdAt" <= ${param_count}')
            params.append(end_time)
        
        # 构建完整查询
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)
        
        param_count += 1
        offset_param = f"${param_count}"
        params.append(offset)
        
        query = f"""
            SELECT * FROM public.user_behaviors
            {where_clause}
            ORDER BY "createdAt" DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                behaviors = []
                for row in rows:
                    behavior = dict(row)
                    behavior['id'] = str(behavior['id'])
                    # Map column names to expected format
                    behavior['user_id'] = behavior.get('userId')
                    behavior['behavior_type'] = behavior.get('action')
                    behavior['target_type'] = behavior.get('targetType')
                    behavior['target_id'] = behavior.get('targetId')
                    behavior['created_at'] = behavior['createdAt'].isoformat() if behavior.get('createdAt') else None
                    # 从metadata中提取action_details，如果没有则用空字典
                    metadata = behavior.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            import json
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    
                    if isinstance(metadata, dict):
                        behavior['action_details'] = metadata.get('action_details', {})
                    else:
                        behavior['action_details'] = {}
                    behaviors.append(behavior)
                
                return behaviors
                
        except Exception as e:
            logger.error(f"查询用户行为失败: {str(e)}")
            return []
    
    async def get_behavior_statistics(
        self,
        user_id: Optional[str] = None,
        behavior_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取用户行为统计信息
        
        Args:
            user_id: 用户ID
            behavior_type: 行为类型
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            统计信息字典
        """
        pool = await self.get_pool()
        
        # 构建查询条件
        conditions = []
        params = []
        param_count = 0
        
        if user_id:
            param_count += 1
            conditions.append(f'"userId" = ${param_count}')
            params.append(user_id)
        
        if behavior_type:
            param_count += 1
            conditions.append(f"action = ${param_count}")
            params.append(behavior_type)
        
        if start_time:
            param_count += 1
            conditions.append(f'"createdAt" >= ${param_count}')
            params.append(start_time)
        
        if end_time:
            param_count += 1
            conditions.append(f'"createdAt" <= ${param_count}')
            params.append(end_time)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 统计查询
        stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT "userId") as unique_users,
                COUNT(DISTINCT metadata->>'session_id') as unique_sessions,
                action as behavior_type,
                COUNT(*) as count
            FROM public.user_behaviors
            {where_clause}
            GROUP BY action
            ORDER BY count DESC
        """
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(stats_query, *params)
                
                behavior_counts = {}
                total_count = 0
                unique_users = set()
                unique_sessions = set()
                
                for row in rows:
                    behavior_counts[row['behavior_type']] = row['count']
                    total_count = row['total_count']
                    if row['unique_users']:
                        unique_users.add(row['unique_users'])
                    if row['unique_sessions']:
                        unique_sessions.add(row['unique_sessions'])
                
                return {
                    'total_behaviors': total_count,
                    'unique_users': len(unique_users),
                    'unique_sessions': len(unique_sessions),
                    'behavior_counts': behavior_counts
                }
                
        except Exception as e:
            logger.error(f"获取行为统计失败: {str(e)}")
            return {
                'total_behaviors': 0,
                'unique_users': 0,
                'unique_sessions': 0,
                'behavior_counts': {}
            }
    
    async def get_popular_targets(
        self,
        target_type: str,
        behavior_type: Optional[str] = None,
        limit: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取热门目标（如最常被查看的文档、最常被搜索的关键词等）
        
        Args:
            target_type: 目标类型
            behavior_type: 行为类型
            limit: 返回数量限制
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            热门目标列表
        """
        pool = await self.get_pool()
        
        # 构建查询条件
        conditions = [f"target_type = $1"]
        params = [target_type]
        param_count = 1
        
        if behavior_type:
            param_count += 1
            conditions.append(f"action = ${param_count}")
            params.append(behavior_type)
        
        if start_time:
            param_count += 1
            conditions.append(f'"createdAt" >= ${param_count}')
            params.append(start_time)
        
        if end_time:
            param_count += 1
            conditions.append(f'"createdAt" <= ${param_count}')
            params.append(end_time)
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)
        
        query = f"""
            SELECT 
                "targetId" as target_id,
                COUNT(*) as access_count,
                COUNT(DISTINCT "userId") as unique_users,
                MAX("createdAt") as last_accessed
            FROM public.user_behaviors
            {where_clause}
            GROUP BY "targetId"
            ORDER BY access_count DESC
            LIMIT {limit_param}
        """
        
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                popular_targets = []
                for row in rows:
                    popular_targets.append({
                        'target_id': row['target_id'],
                        'access_count': row['access_count'],
                        'unique_users': row['unique_users'],
                        'last_accessed': row['last_accessed'].isoformat()
                    })
                
                return popular_targets
                
        except Exception as e:
            logger.error(f"获取热门目标失败: {str(e)}")
            return []
    
    # === 阅读行为专用方法 - 基于前端TypeScript接口 ===
    
    async def save_reading_session(
        self,
        user_id: str,
        document_id: str,
        session_data: Dict[str, Any],
        action_type: str = 'start'
    ) -> Dict[str, Any]:
        """
        保存用户阅读会话信息
        
        对应前端接口: ReadingSession
        支持开始和结束会话
        """
        behavior_type = (
            BehaviorType.READING_SESSION_START if action_type == 'start' 
            else BehaviorType.READING_SESSION_END
        )
        
        # 基础元数据
        metadata = {
            'session_start': session_data.get('sessionStart'),
            'session_end': session_data.get('sessionEnd'),
            'is_active': session_data.get('isActive', action_type == 'start'),
            'device': session_data.get('device', {}),
            'action_type': action_type
        }
        
        # 如果是结束会话，添加额外的统计信息
        if action_type == 'end':
            metadata.update({
                'total_session_time': session_data.get('totalTime', 0),
                'is_completed': session_data.get('isCompleted', False),
                'exit_reason': session_data.get('exitReason', 'normal')
            })
        
        return await self.record_behavior(
            behavior_type=behavior_type,
            user_id=user_id,
            session_id=session_data.get('id'),
            target_type='document',
            target_id=document_id,
            action_details=session_data,
            metadata=metadata
        )
    
    async def save_reading_progress(
        self,
        user_id: str,
        document_id: str,
        session_id: str,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存整体阅读进度
        
        对应前端接口: OverallReadingProgress
        """
        return await self.record_behavior(
            behavior_type=BehaviorType.READING_PROGRESS_UPDATE,
            user_id=user_id,
            session_id=session_id,
            target_type='document',
            target_id=document_id,
            action_details=progress_data,
            metadata={
                'scroll_progress': progress_data.get('scrollProgress', 0),
                'reading_progress': progress_data.get('readingProgress', 0),
                'total_reading_time': progress_data.get('totalReadingTime', 0),
                'active_reading_time': progress_data.get('activeReadingTime', 0),
                'estimated_time_remaining': progress_data.get('estimatedTimeRemaining', 0),
                'total_sections': progress_data.get('totalSections', 0),
                'read_sections': progress_data.get('readSections', 0),
                'completion_rate': progress_data.get('completionRate', 0),
                'current_behavior': progress_data.get('currentBehavior', {}),
                'last_scroll_position': progress_data.get('lastScrollPosition', 0),
                'last_update_time': progress_data.get('lastUpdateTime'),
                'is_completed': progress_data.get('isCompleted', False)
            }
        )
    
    async def save_section_progress(
        self,
        user_id: str,
        document_id: str,
        session_id: str,
        section_progress_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        保存章节级别进度
        
        对应前端接口: SectionProgress[]
        """
        results = []
        for section in section_progress_list:
            result = await self.record_behavior(
                behavior_type=BehaviorType.SECTION_PROGRESS_UPDATE,
                user_id=user_id,
                session_id=session_id,
                target_type='section',
                target_id=section.get('id'),
                action_details=section,
                metadata={
                    'title': section.get('title'),
                    'level': section.get('level', 1),
                    'position': section.get('position', {}),
                    'is_read': section.get('isRead', False),
                    'read_percentage': section.get('readPercentage', 0),
                    'first_read_time': section.get('firstReadTime'),
                    'last_read_time': section.get('lastReadTime'),
                    'total_read_time': section.get('totalReadTime', 0),
                    'engagement_score': section.get('engagementScore', 0),
                    'scroll_pauses': section.get('scrollPauses', 0),
                    'time_spent': section.get('timeSpent', 0),
                    'interaction_count': section.get('interactionCount', 0)
                }
            )
            results.append(result)
        return results
    
    async def save_scroll_behavior(
        self,
        user_id: str,
        document_id: str,
        session_id: str,
        scroll_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存滚动行为追踪数据
        
        对应前端接口: ScrollBehavior
        """
        return await self.record_behavior(
            behavior_type=BehaviorType.SCROLL_BEHAVIOR_TRACK,
            user_id=user_id,
            session_id=session_id,
            target_type='document',
            target_id=document_id,
            action_details=scroll_data,
            metadata={
                'scroll_top': scroll_data.get('scrollTop', 0),
                'scroll_height': scroll_data.get('scrollHeight', 0),
                'client_height': scroll_data.get('clientHeight', 0),
                'scroll_progress': scroll_data.get('scrollProgress', 0),
                'scroll_direction': scroll_data.get('scrollDirection', 'none'),
                'scroll_speed': scroll_data.get('scrollSpeed', 0),
                'is_paused': scroll_data.get('isPaused', False),
                'pause_duration': scroll_data.get('pauseDuration', 0),
                'visible_sections': scroll_data.get('visibleSections', []),
                'focused_section': scroll_data.get('focusedSection')
            }
        )
    
    async def save_reading_insights(
        self,
        user_id: str,
        document_id: str,
        insights_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存阅读洞察数据
        
        对应前端接口: ReadingInsights
        """
        return await self.record_behavior(
            behavior_type=BehaviorType.READING_INSIGHTS_GENERATED,
            user_id=user_id,
            target_type='document',
            target_id=document_id,
            action_details=insights_data,
            metadata={
                'dominant_reading_mode': insights_data.get('dominantReadingMode'),
                'reading_mode_distribution': insights_data.get('readingModeDistribution', {}),
                'personalized_tips': insights_data.get('personalizedTips', []),
                'recommended_reading_time': insights_data.get('recommendedReadingTime', 0),
                'difficulty_assessment': insights_data.get('difficultyAssessment'),
                'avg_completion_time': insights_data.get('avgCompletionTime'),
                'user_rank': insights_data.get('userRank'),
                'generated_at': insights_data.get('generatedAt')
            }
        )
    
    async def save_complete_reading_progress(
        self,
        save_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存完整的阅读进度数据
        
        对应前端接口: SaveProgressRequest
        """
        user_id = save_request.get('userId')
        document_id = save_request.get('documentId')
        session_id = save_request.get('sessionId')
        
        results = {
            'success': True,
            'saved_components': [],
            'errors': []
        }
        
        try:
            # 保存整体进度
            if 'overallProgress' in save_request:
                progress_result = await self.save_reading_progress(
                    user_id, document_id, session_id,
                    save_request['overallProgress']
                )
                results['saved_components'].append({
                    'type': 'overall_progress',
                    'result': progress_result
                })
            
            # 保存章节进度
            if 'sectionProgress' in save_request and save_request['sectionProgress']:
                section_results = await self.save_section_progress(
                    user_id, document_id, session_id,
                    save_request['sectionProgress']
                )
                results['saved_components'].append({
                    'type': 'section_progress',
                    'count': len(section_results) if section_results else 0,
                    'results': section_results or []
                })
            
            # 保存滚动行为
            if 'scrollBehavior' in save_request and save_request['scrollBehavior']:
                scroll_result = await self.save_scroll_behavior(
                    user_id, document_id, session_id,
                    save_request['scrollBehavior']
                )
                results['saved_components'].append({
                    'type': 'scroll_behavior',
                    'result': scroll_result
                })
            
            # 保存洞察数据
            if 'insights' in save_request and save_request['insights']:
                insights_result = await self.save_reading_insights(
                    user_id, document_id,
                    save_request['insights']
                )
                results['saved_components'].append({
                    'type': 'insights',
                    'result': insights_result
                })
            
            # 记录保存类型和元数据
            await self.record_behavior(
                behavior_type='reading_progress_save',
                user_id=user_id,
                session_id=session_id,
                target_type='document',
                target_id=document_id,
                metadata={
                    'save_type': save_request.get('saveType', 'auto'),
                    'timestamp': save_request.get('timestamp'),
                    'client_version': save_request.get('clientVersion'),
                    'components_saved': len(results['saved_components'])
                }
            )
            
        except Exception as e:
            logger.error(f"保存完整阅读进度失败: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    async def load_reading_progress(
        self,
        user_id: str,
        document_id: str
    ) -> Dict[str, Any]:
        """
        加载用户的阅读进度
        
        返回格式对应前端接口: LoadProgressResponse
        """
        try:
            # 获取最新的整体阅读进度
            overall_progress_behaviors = await self.get_user_behaviors(
                user_id=user_id,
                behavior_type=BehaviorType.READING_PROGRESS_UPDATE,
                target_type='document',
                target_id=document_id,
                limit=1
            )
            
            # 获取章节进度
            section_progress_behaviors = await self.get_user_behaviors(
                user_id=user_id,
                behavior_type=BehaviorType.SECTION_PROGRESS_UPDATE,
                target_type='section',
                limit=50
            )
            
            # 获取最后会话信息
            session_behaviors = await self.get_user_behaviors(
                user_id=user_id,
                behavior_type=BehaviorType.READING_SESSION_START,
                target_type='document',
                target_id=document_id,
                limit=1
            )
            
            # 获取阅读洞察
            insights_behaviors = await self.get_user_behaviors(
                user_id=user_id,
                behavior_type=BehaviorType.READING_INSIGHTS_GENERATED,
                target_type='document',
                target_id=document_id,
                limit=1
            )
            
            # 获取阅读历史统计
            all_reading_behaviors = await self.get_user_behaviors(
                user_id=user_id,
                behavior_type=BehaviorType.READING_PROGRESS_UPDATE,
                limit=100
            )
            
            # 构造返回数据
            response_data = {
                'overall_progress': overall_progress_behaviors[0].get('action_details', {}) if overall_progress_behaviors else None,
                'section_progress': [b.get('action_details', {}) for b in section_progress_behaviors],
                'last_session': session_behaviors[0].get('action_details', {}) if session_behaviors else None,
                'reading_history': {
                    'total_sessions': len(set(str(b.get('session_id', '')) for b in all_reading_behaviors if b.get('session_id'))),
                    'total_reading_time': sum(
                        self._safe_get_metadata_value(b, 'total_reading_time', 0)
                        for b in all_reading_behaviors
                    ),
                    'average_session_time': 0,  # 需要计算
                    'last_read_time': overall_progress_behaviors[0].get('created_at') if overall_progress_behaviors else None
                },
                'insights': insights_behaviors[0].get('action_details', {}) if insights_behaviors else None,
                'should_resume': bool(overall_progress_behaviors and not self._safe_get_metadata_value(overall_progress_behaviors[0], 'is_completed', False)),
                'resume_position': self._safe_get_metadata_value(overall_progress_behaviors[0], 'last_scroll_position', 0) if overall_progress_behaviors else 0
            }
            
            return {
                'success': True,
                'data': response_data
            }
            
        except Exception as e:
            logger.error(f"加载阅读进度失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# 创建全局实例
user_behavior_service = UserBehaviorService()