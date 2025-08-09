"""
索引初始化服务
在应用启动时自动创建和配置 Elasticsearch 索引
"""

from typing import Dict, Any
import asyncio
from elasticsearch import AsyncElasticsearch
from app.services.elasticsearch_service import elasticsearch_service
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class IndexInitializer:
    """索引初始化器"""
    
    # 文章内容索引的映射配置
    ARTICLE_INDEX_MAPPING = {
        "mappings": {
            "properties": {
                # PostgreSQL关联
                "pg_id": {"type": "keyword"},
                
                # 文章基本信息
                "id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "summary": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                },
                
                # 分类和标签
                "category": {"type": "keyword"},
                "tags": {"type": "keyword"},
                
                # 作者信息
                "author": {"type": "keyword"},
                
                # 时间信息
                "publish_date": {"type": "date"},
                "upload_time": {"type": "date"},
                "last_modified": {"type": "date"},
                
                # 统计信息
                "read_time": {"type": "integer"},
                "view_count": {"type": "integer"},
                "like_count": {"type": "integer"},
                "word_count": {"type": "integer"},
                
                # 状态标记
                "featured": {"type": "boolean"},
                "member_only": {"type": "boolean"},
                "is_published": {"type": "boolean"},
                
                # MinIO 相关
                "bucket_name": {"type": "keyword"},
                "object_name": {"type": "keyword"},
                "file_path": {"type": "keyword"},
                "minio_public_url": {"type": "keyword"},
                "content_hash": {"type": "keyword"},
                
                # 文件信息
                "file_type": {"type": "keyword"},
                "file_size": {"type": "long"},
                "content_type": {"type": "keyword"},
                
                # 额外的元数据
                "metadata": {
                    "type": "object",
                    "enabled": True
                },
                
                # SEO 相关
                "description": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                },
                "keywords": {"type": "keyword"},
                
                # 搜索优化字段
                "searchable_content": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                }
            }
        },
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "ik_max_word": {
                        "type": "custom",
                        "tokenizer": "ik_max_word"
                    },
                    "ik_smart": {
                        "type": "custom",
                        "tokenizer": "ik_smart"
                    }
                }
            }
        }
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.es_service = elasticsearch_service
        
    async def initialize_indices(self):
        """初始化所有必需的索引"""
        try:
            client = await self.es_service.get_client()
            
            # 创建主文档索引
            await self._create_index_if_not_exists(
                client,
                "minio_articles",  # 新的索引名称
                self.ARTICLE_INDEX_MAPPING
            )
            
            logger.info("索引初始化完成")
            
        except Exception as e:
            logger.error(f"索引初始化失败: {e}")
            raise
    
    async def _create_index_if_not_exists(
        self,
        client: AsyncElasticsearch,
        index_name: str,
        mapping: Dict[str, Any]
    ):
        """创建索引（如果不存在）"""
        try:
            # 检查索引是否存在
            if await client.indices.exists(index=index_name):
                logger.info(f"索引 {index_name} 已存在")
                
                # 可选：更新映射（仅添加新字段）
                # await client.indices.put_mapping(
                #     index=index_name,
                #     body=mapping.get("mappings", {})
                # )
                
            else:
                # 创建新索引
                await client.indices.create(
                    index=index_name,
                    body=mapping
                )
                logger.info(f"成功创建索引: {index_name}")
                
        except Exception as e:
            logger.error(f"创建索引 {index_name} 失败: {e}")
            # 如果是因为分词器不存在，给出提示
            if "analyzer [ik_max_word] has not been configured" in str(e):
                logger.warning(
                    "IK 分词器未安装。如需中文分词支持，请安装 elasticsearch-analysis-ik 插件。"
                    "现在将使用标准分词器创建索引。"
                )
                # 使用标准分词器重新创建
                fallback_mapping = self._get_fallback_mapping(mapping)
                await self._create_index_with_standard_analyzer(
                    client, index_name, fallback_mapping
                )
    
    def _get_fallback_mapping(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """获取使用标准分词器的备用映射"""
        fallback = mapping.copy()
        
        # 替换 IK 分词器为标准分词器
        if "mappings" in fallback:
            for field, config in fallback["mappings"]["properties"].items():
                if isinstance(config, dict):
                    if config.get("analyzer") in ["ik_max_word", "ik_smart"]:
                        config["analyzer"] = "standard"
                    if config.get("search_analyzer") in ["ik_max_word", "ik_smart"]:
                        config["search_analyzer"] = "standard"
        
        # 更新设置
        if "settings" in fallback:
            if "analysis" in fallback["settings"]:
                # 使用标准分析器
                fallback["settings"]["analysis"] = {
                    "analyzer": {
                        "standard": {
                            "type": "standard"
                        }
                    }
                }
        
        return fallback
    
    async def _create_index_with_standard_analyzer(
        self,
        client: AsyncElasticsearch,
        index_name: str,
        mapping: Dict[str, Any]
    ):
        """使用标准分词器创建索引"""
        try:
            if not await client.indices.exists(index=index_name):
                await client.indices.create(
                    index=index_name,
                    body=mapping
                )
                logger.info(f"使用标准分词器创建索引: {index_name}")
        except Exception as e:
            logger.error(f"使用标准分词器创建索引失败: {e}")
            raise
    
    async def delete_index(self, index_name: str):
        """删除索引（仅用于测试或重置）"""
        try:
            client = await self.es_service.get_client()
            if await client.indices.exists(index=index_name):
                await client.indices.delete(index=index_name)
                logger.info(f"已删除索引: {index_name}")
            else:
                logger.info(f"索引不存在: {index_name}")
        except Exception as e:
            logger.error(f"删除索引失败: {e}")
            raise
    
    async def reindex_documents(self, source_index: str, target_index: str):
        """重新索引文档（用于迁移数据）"""
        try:
            client = await self.es_service.get_client()
            
            # 使用 reindex API
            await client.reindex(
                body={
                    "source": {"index": source_index},
                    "dest": {"index": target_index}
                }
            )
            
            logger.info(f"成功将文档从 {source_index} 重新索引到 {target_index}")
            
        except Exception as e:
            logger.error(f"重新索引失败: {e}")
            raise


# 创建全局实例
index_initializer = IndexInitializer()


async def initialize_on_startup():
    """在应用启动时调用的初始化函数"""
    await index_initializer.initialize_indices()