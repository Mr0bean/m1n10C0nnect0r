from elasticsearch import AsyncElasticsearch
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class NewsletterSearchService:
    """
    Newsletter 搜索服务

    职责：
    - 面向 Newsletter/文档集合（索引从配置读取）提供搜索能力
    - 支持关键词、多字段匹配、短语前缀与高亮
    - 提供带过滤条件与排序的增强搜索
    """
    def __init__(self):
        settings = get_settings()
        scheme = "https" if settings.elasticsearch_use_ssl else "http"
        self.es_host = f"{scheme}://{settings.elasticsearch_host}:{settings.elasticsearch_port}"
        self.es_user = settings.elasticsearch_username or None
        self.es_password = settings.elasticsearch_password or None
        self.index_name = settings.document_pipeline_index
        self.client = None
        
    async def get_client(self) -> AsyncElasticsearch:
        """
        获取 Elasticsearch 客户端（单例缓存）。

        Returns:
            AsyncElasticsearch: 复用的 ES 客户端实例。
        """
        if self.client is None:
            auth = (self.es_user, self.es_password) if self.es_user and self.es_password else None
            self.client = AsyncElasticsearch(
                [self.es_host],
                basic_auth=auth,
                verify_certs=bool(auth)  # 若配置使用 HTTPS 则会开启校验
            )
        return self.client
    
    async def search_articles(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        from_: int = 0,
        size: int = 20,
        sort_by: str = '_score',
        highlight: bool = True
    ) -> Dict[str, Any]:
        """
        搜索 Newsletter 文章（索引：配置的 document_pipeline_index）。

        - 采用 multi_match 与短语前缀策略，提升标题与内容匹配效果
        - 支持高亮与按大小排序

        Args:
            query: 搜索关键词
            from_: 起始位置
            size: 返回数量
            sort_by: 排序字段（_score/size/…）
            highlight: 是否高亮显示

        Returns:
            Dict[str, Any]: 结果总数与命中条目列表。
        """
        try:
            client = await self.get_client()
            
            # 构建搜索查询
            search_body = {
                "from": from_,
                "size": size,
                "_source": {
                    "excludes": ["embeddings"]  # 排除向量字段
                }
            }
            
            # 构建最终查询词
            final_query = query
            if categories:
                categories_str = " ".join(categories)
                final_query = f"{query or ''} {categories_str}".strip()
            
            # 将tags拼接到查询词中
            if tags:
                valid_tags = [tag for tag in tags if tag and tag.strip()]
                if valid_tags:
                    tags_str = " ".join(valid_tags)
                    final_query = f"{final_query or ''} {tags_str}".strip()
            
            # 构建查询
            must_clauses = []
            filter_clauses = []
            
            # 关键词搜索
            if final_query and final_query.strip():
                must_clauses.append({
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": final_query,
                                    "fields": [
                                        "title^3",        # 标题权重最高
                                        "content^2",      # 内容
                                        "content_full",   # 完整内容
                                        "html_content",   # HTML内容
                                        "object_name"     # 对象名
                                    ],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO",
                                    "prefix_length": 2
                                }
                            },
                            {
                                "match_phrase_prefix": {
                                    "title": {
                                        "query": final_query,
                                        "boost": 2
                                    }
                                }
                            },
                            {
                                "match_phrase_prefix": {
                                    "content": {
                                        "query": final_query,
                                        "boost": 0.5
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                })
            
            # 构建最终查询
            if not must_clauses and not filter_clauses:
                # 没有任何条件时使用match_all
                search_body["query"] = {
                    "match_all": {}
                }
            else:
                search_body["query"] = {
                    "bool": {}
                }
                if must_clauses:
                    search_body["query"]["bool"]["must"] = must_clauses
                if filter_clauses:
                    search_body["query"]["bool"]["filter"] = filter_clauses
            
            # 添加排序（默认 _score）
            if sort_by == '_score':
                # 默认按相关度排序
                pass
            elif sort_by == 'size':
                # size字段可能不存在，暂时不排序，保持默认顺序
                logger.warning("size字段不存在，使用默认排序")
                pass
            elif sort_by == 'post_date':
                # 按发布日期排序
                search_body["sort"] = [
                    {"publish_date": {"order": "desc", "missing": "_last"}},
                    "_score"
                ]
            
            # 添加高亮
            if highlight:
                search_body["highlight"] = {
                    "fields": {
                        "title": {
                            "fragment_size": 200,
                            "number_of_fragments": 1
                        },
                        "subtitle": {
                            "fragment_size": 150,
                            "number_of_fragments": 1
                        },
                        "content": {
                            "fragment_size": 300,
                            "number_of_fragments": 3
                        }
                    },
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            
            # 执行搜索
            response = await client.search(
                index=self.index_name,
                body=search_body
            )
            
            # 处理结果：裁剪大文本，拼接预览
            hits = response.get('hits', {})
            total = hits.get('total', {}).get('value', 0)
            results = []
            
            for hit in hits.get('hits', []):
                source = hit['_source']
                # 提取内容摘要
                content_preview = ''
                if source.get('content'):
                    content_preview = source['content'][:500] + '...'
                elif source.get('content_full'):
                    content_preview = source['content_full'][:500] + '...'
                
                result = {
                    "id": hit['_id'],
                    "score": hit.get('_score', 0),
                    "title": source.get('title', source.get('object_name', '')),
                    "content": content_preview,
                    "bucket_name": source.get('bucket_name', ''),
                    "object_name": source.get('object_name', ''),
                    "document_type": source.get('document_type', ''),
                    "size": source.get('size', 0),
                    "content_type": source.get('content_type', ''),
                    "minio_public_url": source.get('minio_public_url', ''),
                    "statistics": source.get('statistics', {})
                }
                
                # 添加高亮内容
                if 'highlight' in hit:
                    result['highlight'] = hit['highlight']
                
                results.append(result)
            
            return {
                "success": True,
                "total": total,
                "results": results,
                "query": final_query,
                "original_query": query,
                "categories": categories,
                "tags": tags,
                "from": from_,
                "size": size
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total": 0,
                "results": []
            }
    
    async def search_with_filters(
        self,
        query: str = None,
        categories: List[str] = None,
        article_type: str = None,
        tags: List[str] = None,
        date_from: str = None,
        date_to: str = None,
        min_wordcount: int = None,
        max_wordcount: int = None,
        from_: int = 0,
        size: int = 20,
        sort_by: str = '_score'
    ) -> Dict[str, Any]:
        """
        带过滤条件与排序的高级搜索。

        - 统一在配置的 `document_pipeline_index` 索引上查询
        - 使用 bool.must 与 bool.filter 组合关键词与结构化筛选

        Args 同上。

        Returns:
            Dict[str, Any]: 结果总数与命中列表，附带回显 filters。
        """
        try:
            client = await self.get_client()
            
            # 构建查询：must（全文），filter（结构化）
            must_clauses = []
            filter_clauses = []
            
            # 构建最终查询词
            final_query = query
            if categories:
                categories_str = " ".join(categories)
                final_query = f"{query or ''} {categories_str}".strip()
            
            # 将tags拼接到查询词中
            if tags:
                valid_tags = [tag for tag in tags if tag and tag.strip()]
                if valid_tags:
                    tags_str = " ".join(valid_tags)
                    final_query = f"{final_query or ''} {tags_str}".strip()
            
            # 关键词搜索
            if final_query:
                must_clauses.append({
                    "multi_match": {
                        "query": final_query,
                        "fields": [
                            "title^3",
                            "content^2",
                            "content_full",
                            "html_content",
                            "object_name"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
            
            # 类型过滤 (使用document_type字段)
            if article_type:
                filter_clauses.append({
                    "term": {"document_type": article_type}
                })
            
            # 文件大小范围过滤 (替代字数范围)
            if min_wordcount or max_wordcount:
                size_range = {}
                if min_wordcount:
                    size_range["gte"] = min_wordcount * 10  # 估算字节数
                if max_wordcount:
                    size_range["lte"] = max_wordcount * 10
                filter_clauses.append({
                    "range": {"size": size_range}
                })
            
            # 构建最终查询（空条件回退为 match_all）
            if not must_clauses and not filter_clauses:
                query_body = {"match_all": {}}
            else:
                query_body = {"bool": {}}
                if must_clauses:
                    query_body["bool"]["must"] = must_clauses
                if filter_clauses:
                    query_body["bool"]["filter"] = filter_clauses
            
            search_body = {
                "from": from_,
                "size": size,
                "_source": {
                    "excludes": ["embeddings", "content"]  # 排除大字段
                },
                "query": query_body,
                "highlight": {
                    "fields": {
                        "title": {},
                        "subtitle": {},
                        "content": {"fragment_size": 200, "number_of_fragments": 2}
                    }
                } if final_query else None
            }
            
            # 添加排序
            if sort_by == 'size':
                search_body["sort"] = [{"size": {"order": "desc"}}]
            elif sort_by != '_score':
                # 尝试使用指定的排序字段，如果失败则回退到默认
                pass
            
            # 移除None值
            search_body = {k: v for k, v in search_body.items() if v is not None}
            
            # 执行搜索
            response = await client.search(
                index=self.index_name,
                body=search_body
            )
            
            # 处理结果
            hits = response.get('hits', {})
            total = hits.get('total', {}).get('value', 0)
            results = []
            
            for hit in hits.get('hits', []):
                source = hit['_source']
                # 提取内容摘要
                content_preview = ''
                if source.get('content'):
                    content_preview = source['content'][:300] + '...'
                elif source.get('content_full'):
                    content_preview = source['content_full'][:300] + '...'
                
                result = {
                    "id": hit['_id'],
                    "score": hit.get('_score', 0),
                    "title": source.get('title', source.get('object_name', '')),
                    "content": content_preview,
                    "bucket_name": source.get('bucket_name', ''),
                    "object_name": source.get('object_name', ''),
                    "document_type": source.get('document_type', ''),
                    "size": source.get('size', 0),
                    "content_type": source.get('content_type', ''),
                    "minio_public_url": source.get('minio_public_url', ''),
                    "statistics": source.get('statistics', {})
                }
                
                if 'highlight' in hit:
                    result['highlight'] = hit['highlight']
                
                results.append(result)
            
            return {
                "success": True,
                "total": total,
                "results": results,
                "filters": {
                    "query": final_query,
                    "original_query": query,
                    "categories": categories,
                    "type": article_type,
                    "tags": tags,
                    "date_from": date_from,
                    "date_to": date_to,
                    "min_wordcount": min_wordcount,
                    "max_wordcount": max_wordcount
                },
                "from": from_,
                "size": size
            }
            
        except Exception as e:
            logger.error(f"高级搜索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total": 0,
                "results": []
            }
    
    async def get_article_by_id(
        self,
        article_id: str
    ) -> Dict[str, Any]:
        """
        根据文章ID获取完整的文章详情，同时拼接PostgreSQL中的数据。
        
        Args:
            article_id: 文章的Elasticsearch文档ID
            
        Returns:
            Dict[str, Any]: 包含文章完整信息的字典（ES数据 + PG数据）
        """
        try:
            client = await self.get_client()
            
            # 使用get API获取单个文档
            response = await client.get(
                index=self.index_name,
                id=article_id,
                ignore=[404]  # 忽略404错误，自行处理
            )
            
            # 检查文档是否存在
            if not response.get('found', False):
                return {
                    "success": False,
                    "error": "Article not found",
                    "article_id": article_id
                }
            
            # 提取文档内容
            source = response['_source']
            
            # 构建基础文章信息（来自ES）
            article = {
                "id": response['_id'],
                "title": source.get('title', source.get('object_name', '')),
                "subtitle": source.get('subtitle', ''),
                "content": source.get('content', ''),
                "content_full": source.get('content_full', ''),
                "html_content": source.get('html_content', ''),
                "bucket_name": source.get('bucket_name', ''),
                "object_name": source.get('object_name', ''),
                "document_type": source.get('document_type', ''),
                "size": source.get('size', 0),
                "content_type": source.get('content_type', ''),
                "minio_public_url": source.get('minio_public_url', ''),
                "statistics": source.get('statistics', {}),
                "tags": source.get('tags', []),
                "publish_date": source.get('publish_date'),
                "created_at": source.get('created_at'),
                "updated_at": source.get('updated_at'),
                "metadata": source.get('metadata', {})
            }
            
            # 移除空的embeddings字段（如果存在）
            if 'embeddings' in source:
                article['has_embeddings'] = True
            
            # 尝试从PostgreSQL获取额外的数据（点赞数、评论数等）
            try:
                from app.services.postgresql_service import postgresql_service
                
                # 通过ES文档ID查找对应的PG记录
                pg_data = await postgresql_service.get_newsletter_by_id(article_id)
                
                if pg_data:
                    # 只添加ES中没有的字段，不覆盖已有字段
                    pg_fields_mapping = {
                        "category": pg_data.get('category'),
                        "source_url": pg_data.get('sourceUrl'),
                        "read_time": pg_data.get('readTime'),
                        "view_count": pg_data.get('viewCount', 0),
                        "like_count": pg_data.get('likeCount', 0),
                        "share_count": pg_data.get('shareCount', 0),
                        "comment_count": pg_data.get('commentCount', 0),
                        "featured": pg_data.get('featured', False),
                        "member_only": pg_data.get('memberOnly', False),
                        "status": pg_data.get('status'),
                        "published_at": pg_data.get('publishedAt').isoformat() if pg_data.get('publishedAt') else None,
                        "content_file_key": pg_data.get('contentFileKey'),
                        "content_storage_type": pg_data.get('contentStorageType')
                    }
                    
                    # 只添加ES中不存在或为空的字段
                    for field_name, pg_value in pg_fields_mapping.items():
                        if pg_value is not None and (
                            field_name not in article or 
                            article.get(field_name) is None or 
                            article.get(field_name) == '' or
                            article.get(field_name) == 0
                        ):
                            article[field_name] = pg_value
                    
                    # 对于metadata，采用智能合并：PG字段只在ES中不存在时才添加
                    if pg_data.get('metadata') and isinstance(pg_data['metadata'], dict):
                        pg_metadata = pg_data['metadata']
                        for meta_key, meta_value in pg_metadata.items():
                            if meta_value is not None and (
                                meta_key not in article['metadata'] or
                                article['metadata'].get(meta_key) is None or
                                article['metadata'].get(meta_key) == ''
                            ):
                                article['metadata'][meta_key] = meta_value
                    
                    logger.info(f"成功拼接PG数据 - 文章ID: {article_id}, 点赞数: {pg_data.get('likeCount', 0)}, 评论数: {pg_data.get('commentCount', 0)}")
                else:
                    logger.warning(f"在PG中未找到对应记录 - ES文档ID: {article_id}")
                    # 设置默认的交互数据
                    article.update({
                        "view_count": 0,
                        "like_count": 0,
                        "share_count": 0,
                        "comment_count": 0,
                        "featured": False,
                        "member_only": False
                    })
                    
            except Exception as pg_error:
                logger.error(f"从PostgreSQL获取数据失败 (文章ID: {article_id}): {str(pg_error)}")
                # 如果PG查询失败，设置默认值，不影响ES数据的返回
                article.update({
                    "view_count": 0,
                    "like_count": 0,
                    "share_count": 0,
                    "comment_count": 0,
                    "featured": False,
                    "member_only": False
                })
            
            return {
                "success": True,
                "article": article
            }
            
        except Exception as e:
            logger.error(f"获取文章失败 (ID: {article_id}): {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "article_id": article_id
            }
    
    async def aggregate_tags(
        self,
        size: int = 50,
        min_doc_count: int = 1
    ) -> Dict[str, Any]:
        """
        聚合所有文章的tags，按数量倒序排序。

        Args:
            size: 返回的tag数量上限
            min_doc_count: 最小文档数量阈值

        Returns:
            Dict[str, Any]: 聚合结果，包含tags列表和统计信息
        """
        try:
            client = await self.get_client()
            
            # 构建聚合查询
            search_body = {
                "size": 0,  # 不需要返回文档，只需要聚合结果
                "aggs": {
                    "tags_aggregation": {
                        "terms": {
                            "field": "tags",
                            "size": size,
                            "min_doc_count": min_doc_count,
                            "order": {
                                "_count": "desc"  # 按数量倒序排序
                            }
                        }
                    }
                }
            }
            
            # 执行聚合查询
            response = await client.search(
                index=self.index_name,
                body=search_body
            )
            
            # 处理聚合结果
            aggregations = response.get('aggregations', {})
            tags_agg = aggregations.get('tags_aggregation', {})
            buckets = tags_agg.get('buckets', [])
            
            # 格式化结果
            tags_list = []
            for bucket in buckets:
                tags_list.append({
                    "tag": bucket['key'],
                    "count": bucket['doc_count']
                })
            
            return {
                "success": True,
                "total_tags": len(tags_list),
                "tags": tags_list,
                "total_documents": response.get('hits', {}).get('total', {}).get('value', 0)
            }
            
        except Exception as e:
            logger.error(f"Tags聚合失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_tags": 0,
                "tags": [],
                "total_documents": 0
            }
    
    async def close(self):
        """
        关闭客户端连接（在生命周期结束时调用）。
        """
        if self.client:
            await self.client.close()
            self.client = None


# 创建全局实例
newsletter_search_service = NewsletterSearchService()