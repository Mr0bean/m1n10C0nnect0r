from abc import ABC, abstractmethod
from typing import List, BinaryIO, Optional, Dict, Any, Tuple
from enum import Enum


class StorageType(Enum):
    """存储服务类型枚举"""
    MINIO = "minio"
    OSS = "oss"


class StorageService(ABC):
    """抽象存储服务接口，支持MinIO和阿里云OSS"""
    
    @abstractmethod
    async def list_buckets(self) -> List[Dict[str, Any]]:
        """列出所有存储桶"""
        pass
    
    @abstractmethod
    async def create_bucket(self, bucket_name: str) -> Dict[str, str]:
        """创建存储桶"""
        pass
    
    @abstractmethod
    async def delete_bucket(self, bucket_name: str) -> Dict[str, str]:
        """删除存储桶"""
        pass
    
    @abstractmethod
    async def list_objects(self, bucket_name: str, prefix: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """列出存储桶中的对象"""
        pass
    
    @abstractmethod
    async def upload_file(self, bucket_name: str, object_name: str, file_data: BinaryIO, 
                         content_type: str = "application/octet-stream", 
                         metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """上传文件"""
        pass
    
    @abstractmethod
    async def download_file(self, bucket_name: str, object_name: str) -> Tuple[bytes, Dict[str, Any]]:
        """下载文件"""
        pass
    
    @abstractmethod
    async def delete_object(self, bucket_name: str, object_name: str) -> Dict[str, str]:
        """删除对象"""
        pass
    
    @abstractmethod
    async def get_object_info(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        """获取对象信息"""
        pass
    
    @abstractmethod
    async def generate_presigned_url(self, bucket_name: str, object_name: str, 
                                   expires: int = 3600, method: str = "GET") -> str:
        """生成预签名URL"""
        pass
    
    @abstractmethod
    async def copy_object(self, source_bucket: str, source_object: str, 
                         dest_bucket: str, dest_object: str) -> Dict[str, Any]:
        """复制对象"""
        pass
    
    @abstractmethod
    async def set_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> Dict[str, str]:
        """设置存储桶策略"""
        pass
    
    @abstractmethod
    async def get_bucket_policy(self, bucket_name: str) -> Dict[str, Any]:
        """获取存储桶策略"""
        pass
    
    @abstractmethod
    async def make_bucket_public(self, bucket_name: str) -> Dict[str, str]:
        """设置存储桶为公开访问"""
        pass
    
    @abstractmethod
    async def make_bucket_private(self, bucket_name: str) -> Dict[str, str]:
        """设置存储桶为私有访问"""
        pass
    
    @abstractmethod
    async def get_public_url(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        """获取公开访问URL"""
        pass
    
    @abstractmethod
    def get_storage_type(self) -> StorageType:
        """获取存储服务类型"""
        pass