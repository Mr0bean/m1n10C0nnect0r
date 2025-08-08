#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章处理服务
处理上传到MinIO的文档，并按照新的索引结构格式化后存入Elasticsearch
"""

from typing import Optional, Dict, Any, List
import hashlib
import re
import html2text
import markdown
from datetime import datetime
from pathlib import Path
import json
from io import BytesIO

from app.services.minio_service import MinioService
from elasticsearch import AsyncElasticsearch
from app.core.config import get_settings


class ArticleProcessingService:
    """文章处理服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.minio_service = MinioService()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.index_name = "minio_articles"  # 使用新的索引名
        
    async def get_es_client(self) -> AsyncElasticsearch:
        """获取ES客户端"""
        scheme = "https" if self.settings.elasticsearch_use_ssl else "http"
        host = f"{scheme}://{self.settings.elasticsearch_host}:{self.settings.elasticsearch_port}"
        
        if self.settings.elasticsearch_username and self.settings.elasticsearch_password:
            auth = (self.settings.elasticsearch_username, self.settings.elasticsearch_password)
        else:
            auth = None
        
        return AsyncElasticsearch(
            [host],
            basic_auth=auth,
            verify_certs=self.settings.elasticsearch_use_ssl,
            ssl_show_warn=False
        )
    
    def extract_text_content(self, file_content: bytes, filename: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """从文件中提取文本内容"""
        file_ext = Path(filename).suffix.lower()
        content_str = file_content.decode('utf-8', errors='ignore')
        
        result = {
            'content': '',
            'summary': '',
            'title': '',
            'format': '',
            'metadata': {}
        }
        
        # Markdown文件处理
        if file_ext in ['.md', '.markdown'] or content_type in ['text/markdown', 'text/x-markdown']:
            html_content = markdown.markdown(content_str, extensions=['extra', 'codehilite', 'tables'])
            plain_text = self.html_converter.handle(html_content)
            
            result['content'] = plain_text
            result['format'] = 'markdown'
            
            # 提取标题
            title_match = re.search(r'^#\s+(.+)$', content_str, re.MULTILINE)
            if title_match:
                result['title'] = title_match.group(1).strip()
            
            # 提取摘要（第一段非标题文本）
            paragraphs = [p.strip() for p in plain_text.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            if paragraphs:
                result['summary'] = paragraphs[0][:500]  # 限制摘要长度
            
            # 提取元数据
            result['metadata']['headings'] = re.findall(r'^#{1,6}\s+(.+)$', content_str, re.MULTILINE)
            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content_str, re.DOTALL)
            result['metadata']['has_code'] = len(code_blocks) > 0
            result['metadata']['code_blocks_count'] = len(code_blocks)
            
        # HTML文件处理
        elif file_ext in ['.html', '.htm'] or content_type in ['text/html', 'application/xhtml+xml']:
            plain_text = self.html_converter.handle(content_str)
            
            result['content'] = plain_text
            result['format'] = 'html'
            
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', content_str, re.IGNORECASE | re.DOTALL)
            if title_match:
                result['title'] = title_match.group(1).strip()
            
            # 提取摘要
            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content_str, re.IGNORECASE)
            if desc_match:
                result['summary'] = desc_match.group(1).strip()
            elif plain_text:
                paragraphs = [p.strip() for p in plain_text.split('\n\n') if p.strip()]
                if paragraphs:
                    result['summary'] = paragraphs[0][:500]
            
            # 提取关键词
            keywords_match = re.search(r'<meta\s+name=["\']keywords["\']\s+content=["\'](.*?)["\']', content_str, re.IGNORECASE)
            if keywords_match:
                result['metadata']['keywords'] = keywords_match.group(1).strip()
                
        # 纯文本文件处理
        elif file_ext in ['.txt'] or content_type == 'text/plain':
            result['content'] = content_str
            result['format'] = 'text'
            
            # 尝试提取标题（第一行）
            lines = content_str.split('\n')
            if lines:
                result['title'] = lines[0].strip()[:200]
            
            # 提取摘要
            if len(lines) > 1:
                result['summary'] = '\n'.join(lines[1:3]).strip()[:500]
        
        # 计算字数
        result['word_count'] = len(re.findall(r'\w+', plain_text if 'plain_text' in locals() else content_str))
        
        return result
    
    def determine_category(self, filename: str, content: str, metadata: Dict) -> str:
        """根据文件名和内容判断分类"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # 根据文件名判断
        if 'tutorial' in filename_lower or '教程' in filename_lower:
            return 'tutorial'
        elif 'news' in filename_lower or '新闻' in filename_lower:
            return 'news'
        elif 'blog' in filename_lower or '博客' in filename_lower:
            return 'blog'
        elif 'doc' in filename_lower or '文档' in filename_lower:
            return 'documentation'
        elif 'readme' in filename_lower:
            return 'readme'
        
        # 根据内容判断
        if metadata.get('has_code', False):
            return 'technical'
        elif len(content) > 5000:
            return 'article'
        else:
            return 'note'
    
    def extract_tags(self, content: str, title: str, metadata: Dict) -> List[str]:
        """从内容中提取标签"""
        tags = []
        
        # 从标题中提取关键词
        title_words = re.findall(r'\b[A-Z][a-z]+\b', title)  # 提取首字母大写的词
        tags.extend(title_words[:5])
        
        # 从内容中提取技术关键词
        tech_keywords = [
            'python', 'javascript', 'java', 'react', 'vue', 'docker', 
            'kubernetes', 'ai', 'machine learning', 'deep learning',
            'api', 'database', 'sql', 'nosql', 'mongodb', 'redis'
        ]
        
        content_lower = content.lower()
        for keyword in tech_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        # 从元数据中提取关键词
        if 'keywords' in metadata:
            keywords = metadata['keywords'].split(',')
            tags.extend([k.strip() for k in keywords])
        
        # 去重并限制数量
        tags = list(set(tags))[:10]
        
        return tags
    
    async def process_and_index(
        self, 
        bucket_name: str, 
        object_name: str, 
        file_content: bytes,
        content_type: Optional[str] = None,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理文件并索引到Elasticsearch"""
        
        client = await self.get_es_client()
        
        try:
            # 提取内容
            extracted = self.extract_text_content(file_content, object_name, content_type)
            
            # 生成文档ID
            doc_id = hashlib.sha256(f"{bucket_name}/{object_name}".encode()).hexdigest()
            
            # 生成内容哈希
            content_hash = hashlib.sha256(file_content).hexdigest()
            
            # 获取MinIO公开URL（如果文件已存在）
            try:
                public_url = await self.minio_service.get_public_url(bucket_name, object_name)
            except Exception:
                # 如果文件不存在，生成预期的URL
                public_url = f"http://{self.settings.minio_endpoint}/{bucket_name}/{object_name}"
            
            # 构建文档
            document = {
                # 基本信息
                "id": doc_id,
                "title": extracted['title'] or Path(object_name).stem,
                "summary": extracted['summary'],
                "content": extracted['content'],
                
                # 分类和标签
                "category": self.determine_category(object_name, extracted['content'], extracted['metadata']),
                "tags": self.extract_tags(extracted['content'], extracted['title'], extracted['metadata']),
                
                # 作者信息
                "author": author or "anonymous",
                
                # 时间信息
                "publish_date": datetime.utcnow().isoformat(),
                "upload_time": datetime.utcnow().isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
                
                # 统计信息
                "read_time": max(1, extracted['word_count'] // 200),  # 假设每分钟200字
                "view_count": 0,
                "like_count": 0,
                "word_count": extracted['word_count'],
                
                # 状态标记
                "featured": False,
                "member_only": False,
                "is_published": True,
                
                # MinIO相关
                "bucket_name": bucket_name,
                "object_name": object_name,
                "file_path": f"/{bucket_name}/{object_name}",
                "minio_public_url": public_url,
                "content_hash": content_hash,
                
                # 文件信息
                "file_type": extracted['format'],
                "file_size": len(file_content),
                "content_type": content_type or "application/octet-stream",
                
                # 额外的元数据
                "metadata": extracted['metadata'],
                
                # SEO相关
                "description": extracted['summary'][:160] if extracted['summary'] else "",
                "keywords": extracted.get('metadata', {}).get('keywords', []),
                
                # 搜索优化字段（组合标题、摘要和内容的前500字）
                "searchable_content": f"{extracted['title']} {extracted['summary']} {extracted['content'][:500]}"
            }
            
            # 索引到Elasticsearch
            response = await client.index(
                index=self.index_name,
                id=doc_id,
                body=document
            )
            
            return {
                "success": True,
                "doc_id": doc_id,
                "index": self.index_name,
                "public_url": public_url,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await client.close()
    
    async def search_articles(
        self,
        query: str,
        size: int = 10,
        from_: int = 0,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """搜索文章"""
        client = await self.get_es_client()
        
        try:
            # 构建查询
            must_conditions = []
            
            # 全文搜索
            if query:
                must_conditions.append({
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "summary^2", "content", "searchable_content"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
            
            # 分类过滤
            if category:
                must_conditions.append({"term": {"category": category}})
            
            # 标签过滤
            if tags:
                must_conditions.append({"terms": {"tags": tags}})
            
            # 作者过滤
            if author:
                must_conditions.append({"term": {"author": author}})
            
            # 执行搜索
            body = {
                "query": {
                    "bool": {
                        "must": must_conditions if must_conditions else [{"match_all": {}}]
                    }
                },
                "size": size,
                "from": from_,
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"publish_date": {"order": "desc"}}
                ],
                "highlight": {
                    "fields": {
                        "content": {"fragment_size": 150, "number_of_fragments": 3},
                        "title": {},
                        "summary": {}
                    }
                }
            }
            
            response = await client.search(index=self.index_name, body=body)
            
            return {
                "success": True,
                "total": response['hits']['total']['value'],
                "hits": response['hits']['hits']
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await client.close()


# 创建全局实例
article_processing_service = ArticleProcessingService()