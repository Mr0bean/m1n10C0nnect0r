from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from pydantic import BaseModel, Field
from app.services.newsletter_search_service import newsletter_search_service

router = APIRouter(
    prefix="/newsletter/search",
    tags=["Newsletter搜索"],
    responses={
        500: {"description": "搜索服务错误"}
    }
)


class NewsletterSearchRequest(BaseModel):
    """Newsletter搜索请求"""
    query: str = Field(..., description="搜索关键词", example="AI agent")
    categories: Optional[List[str]] = Field(None, description="分类列表，内容将拼接到query中")
    tags: Optional[List[str]] = Field(None, description="标签列表，用于精确过滤")
    from_: int = Field(0, ge=0, description="起始位置", alias="from")
    size: int = Field(20, ge=1, le=100, description="返回数量")
    sort_by: str = Field("_score", description="排序字段: _score, post_date, popularity_score")
    highlight: bool = Field(True, description="是否高亮显示匹配内容")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "query": "AI agent",
                "categories": ["AI", "机器学习"],
                "tags": ["GPT-5", "LLM"],
                "from": 0,
                "size": 20,
                "sort_by": "_score",
                "highlight": True
            }
        }


class AdvancedSearchRequest(BaseModel):
    """高级搜索请求"""
    query: Optional[str] = Field(None, description="搜索关键词")
    categories: Optional[List[str]] = Field(None, description="分类列表，内容将拼接到query中")
    article_type: Optional[str] = Field(None, description="文章类型: newsletter, tutorial, paper")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    date_from: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    min_wordcount: Optional[int] = Field(None, ge=0, description="最小字数")
    max_wordcount: Optional[int] = Field(None, ge=0, description="最大字数")
    from_: int = Field(0, ge=0, description="起始位置", alias="from")
    size: int = Field(20, ge=1, le=100, description="返回数量")
    sort_by: str = Field("_score", description="排序字段")
    
    class Config:
        populate_by_name = True


@router.get(
    "/",
    summary="搜索Newsletter文章",
    description="""
    对Newsletter文章进行全文搜索。
    
    ### 功能特性
    - **全文搜索**: 搜索标题、副标题、内容、标签等所有文本字段
    - **智能权重**: 标题权重最高(3x)，副标题次之(2x)，标签(1.5x)，内容(1x)
    - **模糊匹配**: 自动纠正拼写错误，支持近似匹配
    - **短语匹配**: 支持短语前缀匹配，提高搜索准确度
    - **高亮显示**: 在搜索结果中高亮显示匹配的关键词
    - **多种排序**: 支持按相关度、发布日期、流行度排序
    
    ### 搜索示例
    - `AI agent` - 搜索包含AI和agent的文章
    - `"machine learning"` - 精确匹配短语
    - `GPT*` - 匹配以GPT开头的词
    
    ### 返回信息
    - 文章基本信息（标题、副标题、摘要）
    - 评分信息（相关度、流行度、新鲜度、质量）
    - 高亮片段（匹配内容的上下文）
    - 标签和反应统计
    """,
    response_description="搜索结果列表"
)
async def search_newsletter(
    query: str = Query(..., description="搜索关键词", example="AI agent"),
    categories: Optional[List[str]] = Query(None, description="分类列表，内容将拼接到query中"),
    tags: Optional[List[str]] = Query(None, description="标签列表，用于精确过滤"),
    from_: int = Query(0, ge=0, description="起始位置", alias="from"),
    size: int = Query(20, ge=1, le=100, description="返回数量"),
    sort_by: str = Query("_score", description="排序字段: _score(相关度), post_date(日期), popularity_score(流行度)"),
    highlight: bool = Query(True, description="是否高亮显示")
):
    try:
        result = await newsletter_search_service.search_articles(
            query=query,
            categories=categories,
            tags=tags,
            from_=from_,
            size=size,
            sort_by=sort_by,
            highlight=highlight
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"搜索失败: {result.get('error', '未知错误')}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.post(
    "/",
    summary="搜索Newsletter文章(POST)",
    description="""
    通过POST请求搜索Newsletter文章，支持更复杂的请求体。
    
    功能与GET接口相同，但更适合：
    - 传递复杂的搜索参数
    - 程序化调用
    - 避免URL长度限制
    """,
    response_description="搜索结果"
)
async def search_newsletter_post(request: NewsletterSearchRequest = Body(...)):
    try:
        result = await newsletter_search_service.search_articles(
            query=request.query,
            categories=request.categories,
            tags=request.tags,
            from_=request.from_,
            size=request.size,
            sort_by=request.sort_by,
            highlight=request.highlight
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"搜索失败: {result.get('error', '未知错误')}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.post(
    "/advanced",
    summary="高级搜索",
    description="""
    支持多条件过滤的高级搜索功能。
    
    ### 过滤条件
    - **query**: 关键词搜索（可选）
    - **article_type**: 文章类型过滤
    - **tags**: 标签过滤（支持多个）
    - **date_from/date_to**: 日期范围过滤
    - **min_wordcount/max_wordcount**: 字数范围过滤
    
    ### 使用场景
    - 精确查找特定类型的文章
    - 按时间段浏览文章
    - 根据标签发现相关内容
    - 筛选特定长度的文章
    
    ### 请求示例
    ```json
    {
      "query": "GPT",
      "article_type": "newsletter",
      "tags": ["AI", "LLM"],
      "date_from": "2024-01-01",
      "date_to": "2024-12-31",
      "min_wordcount": 500,
      "from": 0,
      "size": 20,
      "sort_by": "post_date"
    }
    ```
    """,
    response_description="高级搜索结果"
)
async def advanced_search(request: AdvancedSearchRequest = Body(...)):
    try:
        result = await newsletter_search_service.search_with_filters(
            query=request.query,
            categories=request.categories,
            article_type=request.article_type,
            tags=request.tags,
            date_from=request.date_from,
            date_to=request.date_to,
            min_wordcount=request.min_wordcount,
            max_wordcount=request.max_wordcount,
            from_=request.from_,
            size=request.size,
            sort_by=request.sort_by
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"搜索失败: {result.get('error', '未知错误')}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.get(
    "/quick",
    summary="快速搜索(简化版)",
    description="""
    简化版搜索接口，适合快速测试和简单搜索需求。
    
    - 只需要输入关键词
    - 自动返回最相关的10条结果
    - 包含高亮显示
    - 按相关度排序
    """,
    response_description="快速搜索结果"
)
async def quick_search(
    q: str = Query(..., description="搜索关键词", example="AI"),
    categories: Optional[List[str]] = Query(None, description="分类列表，内容将拼接到query中"),
    tags: Optional[List[str]] = Query(None, description="标签列表，用于精确过滤")
):
    try:
        result = await newsletter_search_service.search_articles(
            query=q,
            categories=categories,
            tags=tags,
            from_=0,
            size=10,
            sort_by="_score",
            highlight=True
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"搜索失败: {result.get('error', '未知错误')}"
            )
        
        # 简化返回结果
        simplified_results = []
        for item in result.get("results", []):
            simplified_results.append({
                "title": item.get("title"),
                "subtitle": item.get("subtitle"),
                "score": item.get("score"),
                "date": item.get("post_date"),
                "type": item.get("type"),
                "highlight": item.get("highlight", {})
            })
        
        return {
            "query": result.get("query", q),
            "original_query": q,
            "categories": categories,
            "tags": tags,
            "total": result.get("total"),
            "results": simplified_results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.get(
    "/{article_id}",
    summary="根据ID获取文章详情",
    description="""
    根据文章ID获取完整的文章详情信息。
    
    ### 功能特性
    - **完整内容**: 返回文章的所有字段，包括完整内容
    - **元数据信息**: 包含文件大小、类型、MinIO URL等
    - **统计信息**: 如果有的话，包含文章的统计数据
    
    ### 返回格式
    包含文章的所有信息：标题、内容、元数据、统计等
    """,
    response_description="文章详情"
)
async def get_article_by_id(
    article_id: str
):
    try:
        result = await newsletter_search_service.get_article_by_id(article_id)
        
        if not result.get("success"):
            if result.get("error") == "Article not found":
                raise HTTPException(
                    status_code=404,
                    detail=f"文章不存在: {article_id}"
                )
            raise HTTPException(
                status_code=500,
                detail=f"获取文章失败: {result.get('error', '未知错误')}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文章服务错误: {str(e)}")


@router.get(
    "/tags/aggregate",
    summary="聚合Tags统计",
    description="""
    获取所有Newsletter文章的tags聚合统计信息。
    
    ### 功能特性
    - **按数量排序**: 按每个tag出现的文章数量倒序排列
    - **可配置阈值**: 可以设置最小文档数量阈值，过滤掉低频tags
    - **数量限制**: 可以限制返回的tag数量，避免结果过多
    - **统计信息**: 返回总tag数量、总文档数量等统计信息
    
    ### 使用场景
    - 生成标签云
    - 分析热门话题趋势
    - 内容分类统计
    - 用户兴趣分析
    
    ### 返回格式
    ```json
    {
      "success": true,
      "total_tags": 25,
      "tags": [
        {"tag": "AI", "count": 45},
        {"tag": "机器学习", "count": 32},
        {"tag": "GPT", "count": 28}
      ],
      "total_documents": 150
    }
    ```
    """,
    response_description="Tags聚合统计结果"
)
async def aggregate_tags(
    size: int = Query(50, ge=1, le=200, description="返回的tag数量上限"),
    min_doc_count: int = Query(1, ge=1, description="最小文档数量阈值")
):
    try:
        result = await newsletter_search_service.aggregate_tags(
            size=size,
            min_doc_count=min_doc_count
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Tags聚合失败: {result.get('error', '未知错误')}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tags聚合服务错误: {str(e)}")