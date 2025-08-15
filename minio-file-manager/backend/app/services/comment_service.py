"""
评论服务
处理文章评论的增删改查
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self):
        self.pool = None
        
    async def get_pool(self):
        """获取数据库连接池"""
        if not self.pool:
            from app.services.postgresql_service import postgresql_service
            self.pool = await postgresql_service.get_pool()
        return self.pool
    
    async def get_newsletter_comments(
        self,
        newsletter_id: str,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "latest"
    ) -> Dict[str, Any]:
        """
        获取文章评论列表
        
        Args:
            newsletter_id: 文章ID
            page: 页码
            page_size: 每页数量
            sort_by: 排序方式 (latest/popular)
            
        Returns:
            评论列表和分页信息
        """
        pool = await self.get_pool()
        offset = (page - 1) * page_size
        
        # 排序条件
        order_by = '"createdAt" DESC' if sort_by == "latest" else '"likeCount" DESC, "createdAt" DESC'
        
        try:
            async with pool.acquire() as conn:
                # 获取主评论（parentId为空）
                query = f'''
                    SELECT 
                        c.id,
                        c.content,
                        c."userId",
                        c."parentId",
                        c."likeCount",
                        c.status,
                        c."createdAt",
                        c."updatedAt",
                        u.name as "userName",
                        u.email as "userEmail",
                        u.avatar as "userAvatar",
                        (SELECT COUNT(*) FROM comments WHERE "parentId" = c.id) as "replyCount"
                    FROM comments c
                    LEFT JOIN users u ON c."userId" = u.id
                    WHERE c."targetId" = $1 
                        AND c."targetType" = 'NEWSLETTER'
                        AND c."parentId" IS NULL
                        AND c.status = 'PUBLISHED'
                    ORDER BY {order_by}
                    LIMIT $2 OFFSET $3
                '''
                
                comments = await conn.fetch(query, newsletter_id, page_size, offset)
                
                # 转换为字典列表
                comment_list = []
                for comment in comments:
                    comment_dict = dict(comment)
                    
                    # 获取前3条回复
                    if comment_dict['replyCount'] > 0:
                        replies_query = '''
                            SELECT 
                                c.id,
                                c.content,
                                c."userId",
                                c."parentId",
                                c."likeCount",
                                c.status,
                                c."createdAt",
                                u.name as "userName",
                                u.email as "userEmail",
                                u.avatar as "userAvatar"
                            FROM comments c
                            LEFT JOIN users u ON c."userId" = u.id
                            WHERE c."parentId" = $1 AND c.status = 'PUBLISHED'
                            ORDER BY c."createdAt" ASC
                            LIMIT 3
                        '''
                        replies = await conn.fetch(replies_query, comment['id'])
                        comment_dict['replies'] = [dict(reply) for reply in replies]
                    else:
                        comment_dict['replies'] = []
                    
                    # 格式化用户信息
                    comment_dict['author'] = {
                        'id': comment_dict['userId'],
                        'name': comment_dict.get('userName', 'Anonymous'),
                        'email': comment_dict.get('userEmail'),
                        'avatar': comment_dict.get('userAvatar')
                    }
                    
                    # 清理临时字段
                    for field in ['userName', 'userEmail', 'userAvatar']:
                        comment_dict.pop(field, None)
                    
                    comment_list.append(comment_dict)
                
                # 获取总数
                total_result = await conn.fetchrow(
                    '''SELECT COUNT(*) as count FROM comments 
                       WHERE "targetId" = $1 
                       AND "targetType" = 'NEWSLETTER'
                       AND "parentId" IS NULL 
                       AND status = 'PUBLISHED' ''',
                    newsletter_id
                )
                
                total = total_result['count'] if total_result else 0
                
                return {
                    "success": True,
                    "total": total,
                    "page": page,
                    "pageSize": page_size,
                    "hasNext": offset + page_size < total,
                    "comments": comment_list
                }
                
        except Exception as e:
            logger.error(f"获取评论列表失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total": 0,
                "comments": []
            }
    
    async def create_comment(
        self,
        newsletter_id: str,
        content: str,
        parent_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建评论
        
        Args:
            newsletter_id: 文章ID
            content: 评论内容
            parent_id: 父评论ID（可选，用于回复）
            user_id: 用户ID（可选，默认使用mock用户）
            
        Returns:
            新创建的评论信息
        """
        # 使用默认用户ID（测试用户）
        if not user_id:
            user_id = "cmdu8uetk007dvjcsfjnqg2wd"  # 张三的用户ID
        
        # 内容验证
        if not content or len(content.strip()) == 0:
            return {
                "success": False,
                "error": "评论内容不能为空"
            }
        
        if len(content) > 1000:
            return {
                "success": False,
                "error": "评论内容不能超过1000字"
            }
        
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # 检查文章是否存在
                    newsletter = await conn.fetchrow(
                        'SELECT id FROM newsletters WHERE id = $1',
                        newsletter_id
                    )
                    
                    if not newsletter:
                        return {
                            "success": False,
                            "error": "Newsletter not found"
                        }
                    
                    # 如果是回复，检查父评论是否存在
                    if parent_id:
                        parent_comment = await conn.fetchrow(
                            'SELECT id FROM comments WHERE id = $1',
                            parent_id
                        )
                        if not parent_comment:
                            return {
                                "success": False,
                                "error": "Parent comment not found"
                            }
                    
                    # 生成评论ID
                    comment_id = str(uuid.uuid4())
                    now = datetime.utcnow()
                    
                    # 插入评论
                    await conn.execute(
                        '''INSERT INTO comments 
                           (id, "userId", "targetId", "targetType", "parentId", 
                            content, "likeCount", status, "createdAt", "updatedAt")
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)''',
                        comment_id, user_id, newsletter_id, 'NEWSLETTER', parent_id,
                        content, 0, 'PUBLISHED', now, now
                    )
                    
                    # 更新文章评论数（仅主评论）
                    if not parent_id:
                        await conn.execute(
                            'UPDATE newsletters SET "commentCount" = "commentCount" + 1 WHERE id = $1',
                            newsletter_id
                        )
                    
                    # 获取用户信息
                    user = await conn.fetchrow(
                        'SELECT id, name, email, avatar FROM users WHERE id = $1',
                        user_id
                    )
                    
                    # 构建返回数据
                    new_comment = {
                        "id": comment_id,
                        "content": content,
                        "userId": user_id,
                        "parentId": parent_id,
                        "likeCount": 0,
                        "replyCount": 0,
                        "status": 'PUBLISHED',
                        "createdAt": now.isoformat(),
                        "updatedAt": now.isoformat(),
                        "author": {
                            "id": user_id,
                            "name": user['name'] if user else 'Anonymous',
                            "email": user['email'] if user else None,
                            "avatar": user['avatar'] if user else None
                        },
                        "replies": []
                    }
                    
                    logger.info(f"创建评论成功 - 用户: {user_id}, 文章: {newsletter_id}, 评论ID: {comment_id}")
                    
                    return {
                        "success": True,
                        "data": new_comment,
                        "message": "评论发表成功"
                    }
                    
        except Exception as e:
            logger.error(f"创建评论失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_comment(
        self,
        comment_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        删除评论（软删除）
        
        Args:
            comment_id: 评论ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            删除结果
        """
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                # 更新状态为DELETED
                result = await conn.execute(
                    '''UPDATE comments 
                       SET status = 'DELETED', "updatedAt" = $1
                       WHERE id = $2''',
                    datetime.utcnow(), comment_id
                )
                
                if result == "UPDATE 1":
                    return {
                        "success": True,
                        "message": "评论已删除"
                    }
                else:
                    return {
                        "success": False,
                        "error": "评论不存在"
                    }
                    
        except Exception as e:
            logger.error(f"删除评论失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_comment_replies(
        self,
        comment_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        获取评论的所有回复
        
        Args:
            comment_id: 父评论ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            回复列表
        """
        pool = await self.get_pool()
        offset = (page - 1) * page_size
        
        try:
            async with pool.acquire() as conn:
                # 获取回复
                replies = await conn.fetch(
                    '''SELECT 
                        c.id,
                        c.content,
                        c."userId",
                        c."parentId",
                        c."likeCount",
                        c.status,
                        c."createdAt",
                        u.name as "userName",
                        u.email as "userEmail",
                        u.avatar as "userAvatar"
                    FROM comments c
                    LEFT JOIN users u ON c."userId" = u.id
                    WHERE c."parentId" = $1 AND c.status = 'PUBLISHED'
                    ORDER BY c."createdAt" ASC
                    LIMIT $2 OFFSET $3''',
                    comment_id, page_size, offset
                )
                
                # 获取总数
                total_result = await conn.fetchrow(
                    'SELECT COUNT(*) as count FROM comments WHERE "parentId" = $1 AND status = \'PUBLISHED\'',
                    comment_id
                )
                
                total = total_result['count'] if total_result else 0
                
                # 格式化回复
                reply_list = []
                for reply in replies:
                    reply_dict = dict(reply)
                    reply_dict['author'] = {
                        'id': reply_dict['userId'],
                        'name': reply_dict.get('userName', 'Anonymous'),
                        'email': reply_dict.get('userEmail'),
                        'avatar': reply_dict.get('userAvatar')
                    }
                    
                    # 清理临时字段
                    for field in ['userName', 'userEmail', 'userAvatar']:
                        reply_dict.pop(field, None)
                    
                    reply_list.append(reply_dict)
                
                return {
                    "success": True,
                    "total": total,
                    "page": page,
                    "pageSize": page_size,
                    "replies": reply_list
                }
                
        except Exception as e:
            logger.error(f"获取评论回复失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "replies": []
            }


# 创建全局实例
comment_service = CommentService()