"""
Newsletter交互接口
包括点赞、评论等功能
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.services.like_service import like_service
from app.services.comment_service import comment_service

router = APIRouter(
    prefix="/newsletters",
    tags=["Newsletter交互"],
    responses={
        404: {"description": "资源不存在"},
        500: {"description": "服务器错误"}
    }
)


# ============= 请求/响应模型 =============

class LikeActionRequest(BaseModel):
    """点赞操作请求"""
    action: str = Field(..., description="操作类型: like/unlike")
    userId: Optional[str] = Field(None, description="用户ID（可选）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "like",
                "userId": "user_123"
            }
        }


class LikeResponse(BaseModel):
    """点赞响应"""
    success: bool
    newsletterId: Optional[str] = None
    commentId: Optional[str] = None
    isLiked: bool
    likeCount: int
    userId: str
    timestamp: str
    message: Optional[str] = None
    error: Optional[str] = None


class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    parentId: Optional[str] = Field(None, description="父评论ID（用于回复）")
    userId: Optional[str] = Field(None, description="用户ID（可选）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "这篇文章写得很好，对AI Agent的分析很深入！",
                "parentId": None,
                "userId": None
            }
        }


class CommentResponse(BaseModel):
    """评论响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class CommentListResponse(BaseModel):
    """评论列表响应"""
    success: bool
    total: int
    page: int
    pageSize: int
    hasNext: bool
    comments: list
    error: Optional[str] = None


# ============= API接口 =============

@router.post(
    "/{newsletter_id}/like",
    response_model=LikeResponse,
    summary="文章点赞/取消点赞",
    description="""
    对文章进行点赞或取消点赞操作。
    
    ### 功能说明
    - 自动检测当前点赞状态
    - 已点赞则取消，未点赞则添加
    - 实时更新点赞数量
    - 支持Mock用户（userId可选）
    
    ### 使用示例
    ```
    POST /api/v1/newsletters/article_123/like
    {
        "action": "like"
    }
    ```
    """
)
async def toggle_newsletter_like(
    newsletter_id: str = Path(..., description="文章ID"),
    request: LikeActionRequest = Body(...)
):
    """切换文章点赞状态"""
    try:
        # 调用服务层
        result = await like_service.toggle_newsletter_like(
            newsletter_id=newsletter_id,
            user_id=request.userId
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "操作失败")
            )
        
        return LikeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{newsletter_id}/comments",
    response_model=CommentListResponse,
    summary="获取文章评论列表",
    description="""
    获取指定文章的评论列表，支持分页和排序。
    
    ### 功能特性
    - 支持分页查询
    - 支持按最新/最热排序
    - 包含用户信息
    - 自动加载前3条回复
    - 显示回复总数
    
    ### 排序选项
    - `latest`: 按时间倒序（默认）
    - `popular`: 按点赞数排序
    """
)
async def get_newsletter_comments(
    newsletter_id: str = Path(..., description="文章ID"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    sortBy: str = Query("latest", regex="^(latest|popular)$", description="排序方式")
):
    """获取文章评论列表"""
    try:
        result = await comment_service.get_newsletter_comments(
            newsletter_id=newsletter_id,
            page=page,
            page_size=pageSize,
            sort_by=sortBy
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "获取评论失败")
            )
        
        return CommentListResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{newsletter_id}/comments",
    response_model=CommentResponse,
    summary="发表评论",
    description="""
    对文章发表评论或回复其他评论。
    
    ### 功能说明
    - 支持主评论和回复
    - 自动更新文章评论数
    - 内容长度限制1-1000字
    - 支持Mock用户（userId可选）
    
    ### 使用示例
    
    #### 发表主评论
    ```json
    {
        "content": "这篇文章很有启发性！",
        "parentId": null
    }
    ```
    
    #### 回复评论
    ```json
    {
        "content": "同意你的观点",
        "parentId": "comment_123"
    }
    ```
    """
)
async def create_comment(
    newsletter_id: str = Path(..., description="文章ID"),
    request: CommentCreateRequest = Body(...)
):
    """发表评论"""
    try:
        result = await comment_service.create_comment(
            newsletter_id=newsletter_id,
            content=request.content,
            parent_id=request.parentId,
            user_id=request.userId
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400 if "不能" in result.get("error", "") else 404,
                detail=result.get("error", "发表评论失败")
            )
        
        return CommentResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/comments/{comment_id}/like",
    response_model=LikeResponse,
    summary="评论点赞/取消点赞",
    description="""
    对评论进行点赞或取消点赞操作。
    
    ### 功能说明
    - 自动检测当前点赞状态
    - 已点赞则取消，未点赞则添加
    - 实时更新评论点赞数
    - 支持Mock用户（userId可选）
    """
)
async def toggle_comment_like(
    comment_id: str = Path(..., description="评论ID"),
    request: LikeActionRequest = Body(...)
):
    """切换评论点赞状态"""
    try:
        result = await like_service.toggle_comment_like(
            comment_id=comment_id,
            user_id=request.userId
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "操作失败")
            )
        
        return LikeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/comments/{comment_id}/replies",
    summary="获取评论的回复",
    description="""
    获取指定评论的所有回复，支持分页。
    
    ### 功能说明
    - 获取评论的完整回复列表
    - 支持分页查询
    - 按时间顺序排列
    """
)
async def get_comment_replies(
    comment_id: str = Path(..., description="父评论ID"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=50, description="每页数量")
):
    """获取评论回复"""
    try:
        result = await comment_service.get_comment_replies(
            comment_id=comment_id,
            page=page,
            page_size=pageSize
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "获取回复失败")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))