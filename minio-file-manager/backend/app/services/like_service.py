"""
点赞服务
处理文章和评论的点赞功能
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class LikeService:
    def __init__(self):
        self.pool = None
        
    async def get_pool(self):
        """获取数据库连接池"""
        if not self.pool:
            from app.services.postgresql_service import postgresql_service
            self.pool = await postgresql_service.get_pool()
        return self.pool
    
    async def toggle_newsletter_like(
        self, 
        newsletter_id: str, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        切换文章点赞状态
        
        Args:
            newsletter_id: 文章ID
            user_id: 用户ID（可选，默认使用mock用户）
            
        Returns:
            点赞状态和数量
        """
        # 使用默认用户ID（测试用户）
        if not user_id:
            user_id = "cmdu8uetk007dvjcsfjnqg2wd"  # 张三的用户ID
            
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                # 开启事务
                async with conn.transaction():
                    # 检查文章是否存在
                    newsletter = await conn.fetchrow(
                        'SELECT id, "likeCount" FROM newsletters WHERE id = $1',
                        newsletter_id
                    )
                    
                    if not newsletter:
                        return {
                            "success": False,
                            "error": "Newsletter not found"
                        }
                    
                    # 查询现有点赞记录
                    existing_like = await conn.fetchrow(
                        '''SELECT id FROM likes 
                           WHERE "userId" = $1 AND "targetId" = $2 AND "targetType" = $3''',
                        user_id, newsletter_id, 'NEWSLETTER'
                    )
                    
                    if existing_like:
                        # 取消点赞
                        await conn.execute(
                            'DELETE FROM likes WHERE id = $1',
                            existing_like['id']
                        )
                        
                        # 更新点赞数
                        await conn.execute(
                            'UPDATE newsletters SET "likeCount" = GREATEST("likeCount" - 1, 0) WHERE id = $1',
                            newsletter_id
                        )
                        
                        is_liked = False
                        new_count = max(newsletter['likeCount'] - 1, 0)
                        
                        logger.info(f"取消点赞 - 用户: {user_id}, 文章: {newsletter_id}")
                        
                    else:
                        # 添加点赞
                        like_id = str(uuid.uuid4())
                        await conn.execute(
                            '''INSERT INTO likes (id, "userId", "targetId", "targetType", "createdAt")
                               VALUES ($1, $2, $3, $4, $5)''',
                            like_id, user_id, newsletter_id, 'NEWSLETTER', datetime.utcnow()
                        )
                        
                        # 更新点赞数
                        await conn.execute(
                            'UPDATE newsletters SET "likeCount" = "likeCount" + 1 WHERE id = $1',
                            newsletter_id
                        )
                        
                        is_liked = True
                        new_count = newsletter['likeCount'] + 1
                        
                        logger.info(f"添加点赞 - 用户: {user_id}, 文章: {newsletter_id}")
                    
                    return {
                        "success": True,
                        "newsletterId": newsletter_id,
                        "isLiked": is_liked,
                        "likeCount": new_count,
                        "userId": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"点赞操作失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def toggle_comment_like(
        self,
        comment_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        切换评论点赞状态
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID（可选，默认使用mock用户）
            
        Returns:
            点赞状态和数量
        """
        # 使用默认用户ID（测试用户）
        if not user_id:
            user_id = "cmdu8uetk007dvjcsfjnqg2wd"  # 张三的用户ID
            
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # 检查评论是否存在
                    comment = await conn.fetchrow(
                        'SELECT id, "likeCount" FROM comments WHERE id = $1',
                        comment_id
                    )
                    
                    if not comment:
                        return {
                            "success": False,
                            "error": "Comment not found"
                        }
                    
                    # 查询现有点赞记录
                    existing_like = await conn.fetchrow(
                        '''SELECT id FROM likes 
                           WHERE "userId" = $1 AND "targetId" = $2 AND "targetType" = $3''',
                        user_id, comment_id, 'COMMENT'
                    )
                    
                    if existing_like:
                        # 取消点赞
                        await conn.execute(
                            'DELETE FROM likes WHERE id = $1',
                            existing_like['id']
                        )
                        
                        # 更新点赞数
                        await conn.execute(
                            'UPDATE comments SET "likeCount" = GREATEST("likeCount" - 1, 0) WHERE id = $1',
                            comment_id
                        )
                        
                        is_liked = False
                        new_count = max(comment['likeCount'] - 1, 0)
                        
                        logger.info(f"取消评论点赞 - 用户: {user_id}, 评论: {comment_id}")
                        
                    else:
                        # 添加点赞
                        like_id = str(uuid.uuid4())
                        await conn.execute(
                            '''INSERT INTO likes (id, "userId", "targetId", "targetType", "createdAt")
                               VALUES ($1, $2, $3, $4, $5)''',
                            like_id, user_id, comment_id, 'COMMENT', datetime.utcnow()
                        )
                        
                        # 更新点赞数
                        await conn.execute(
                            'UPDATE comments SET "likeCount" = "likeCount" + 1 WHERE id = $1',
                            comment_id
                        )
                        
                        is_liked = True
                        new_count = comment['likeCount'] + 1
                        
                        logger.info(f"添加评论点赞 - 用户: {user_id}, 评论: {comment_id}")
                    
                    return {
                        "success": True,
                        "commentId": comment_id,
                        "isLiked": is_liked,
                        "likeCount": new_count,
                        "userId": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"评论点赞操作失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_likes(
        self,
        user_id: str,
        target_type: str = 'NEWSLETTER'
    ) -> list:
        """
        获取用户的点赞列表
        
        Args:
            user_id: 用户ID
            target_type: 目标类型（NEWSLETTER或COMMENT）
            
        Returns:
            点赞记录列表
        """
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                likes = await conn.fetch(
                    '''SELECT "targetId" FROM likes 
                       WHERE "userId" = $1 AND "targetType" = $2
                       ORDER BY "createdAt" DESC''',
                    user_id, target_type
                )
                
                return [like['targetId'] for like in likes]
                
        except Exception as e:
            logger.error(f"获取用户点赞列表失败: {str(e)}")
            return []


# 创建全局实例
like_service = LikeService()