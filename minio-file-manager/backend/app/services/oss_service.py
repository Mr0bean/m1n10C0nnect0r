import oss2
from oss2.exceptions import OssError, NoSuchBucket, NoSuchKey
from starlette.concurrency import run_in_threadpool
from typing import List, BinaryIO, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
from app.services.storage_service import StorageService, StorageType
from app.core.config import get_settings


class OSSService(StorageService):
    """阿里云OSS存储服务实现"""
    
    def __init__(self):
        settings = get_settings()
        # OSS认证信息
        auth = oss2.Auth(settings.oss_access_key, settings.oss_secret_key)
        # OSS服务实例
        self.service = oss2.Service(auth, settings.oss_endpoint)
        # Bucket操作需要指定endpoint和bucket名称，这里先保存认证和endpoint
        self.auth = auth
        self.endpoint = settings.oss_endpoint
        self.region = settings.oss_region
    
    def _get_bucket(self, bucket_name: str) -> oss2.Bucket:
        """获取指定的Bucket实例"""
        return oss2.Bucket(self.auth, self.endpoint, bucket_name)
    
    def _sanitize_metadata_for_oss(self, metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """将元数据清洗为OSS支持的格式"""
        if not metadata:
            return None
        
        safe: Dict[str, str] = {}
        for key, value in metadata.items():
            try:
                # OSS元数据key必须以x-oss-meta-开头（如果不是的话会自动添加）
                key_str = str(key)
                val_str = str(value)
                
                # OSS支持UTF-8编码，但有长度限制
                if len(key_str) <= 1024 and len(val_str) <= 2048:
                    safe[key_str] = val_str
            except Exception:
                continue
        return safe if safe else None
    
    async def list_buckets(self) -> List[Dict[str, Any]]:
        try:
            response = await run_in_threadpool(self.service.list_buckets)
            return [
                {
                    "name": bucket.name,
                    "creation_date": bucket.creation_date.isoformat() if bucket.creation_date else None,
                    "location": getattr(bucket, 'location', None),
                    "storage_class": getattr(bucket, 'storage_class', None)
                }
                for bucket in response.buckets
            ]
        except OssError as e:
            raise Exception(f"Error listing buckets: {str(e)}")
    
    async def create_bucket(self, bucket_name: str) -> Dict[str, str]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # 检查bucket是否已存在
            try:
                await run_in_threadpool(bucket.get_bucket_info)
                raise Exception(f"Bucket '{bucket_name}' already exists")
            except NoSuchBucket:
                # Bucket不存在，可以创建
                pass
            
            # 创建bucket，可以指定ACL和存储类型
            await run_in_threadpool(
                bucket.create_bucket,
                oss2.BUCKET_ACL_PRIVATE  # 默认私有
            )
            return {"message": f"Bucket '{bucket_name}' created successfully"}
        except OssError as e:
            raise Exception(f"Error creating bucket: {str(e)}")
    
    async def delete_bucket(self, bucket_name: str) -> Dict[str, str]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # 检查bucket是否为空
            objects_iter = await run_in_threadpool(
                lambda: oss2.ObjectIterator(bucket, max_keys=1)
            )
            objects = list(objects_iter)
            if objects:
                raise Exception(f"Bucket '{bucket_name}' is not empty")
            
            await run_in_threadpool(bucket.delete_bucket)
            return {"message": f"Bucket '{bucket_name}' deleted successfully"}
        except OssError as e:
            raise Exception(f"Error deleting bucket: {str(e)}")
    
    async def list_objects(self, bucket_name: str, prefix: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # OSS的delimiter用于控制是否递归列出
            delimiter = '' if recursive else '/'
            
            def _list_objects():
                objects_iter = oss2.ObjectIterator(
                    bucket, 
                    prefix=prefix, 
                    delimiter=delimiter,
                    max_keys=1000  # 每次最多返回1000个对象
                )
                return list(objects_iter)
            
            objects = await run_in_threadpool(_list_objects)
            
            result = []
            for obj in objects:
                # OSS返回的对象信息
                result.append({
                    "name": obj.key,
                    "size": obj.size,
                    "etag": obj.etag.strip('"'),  # OSS的etag包含引号
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "storage_class": obj.storage_class,
                    "is_dir": obj.key.endswith('/') and obj.size == 0
                })
            
            return result
        except OssError as e:
            raise Exception(f"Error listing objects: {str(e)}")
    
    async def upload_file(self, bucket_name: str, object_name: str, file_data: BinaryIO, 
                         content_type: str = "application/octet-stream", 
                         metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # 获取文件大小
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            # 准备headers
            headers = {'Content-Type': content_type}
            
            # 处理元数据
            oss_metadata = self._sanitize_metadata_for_oss(metadata)
            if oss_metadata:
                for key, value in oss_metadata.items():
                    # OSS自定义元数据以x-oss-meta-开头
                    if not key.startswith('x-oss-meta-'):
                        headers[f'x-oss-meta-{key}'] = value
                    else:
                        headers[key] = value
            
            # 上传文件
            result = await run_in_threadpool(
                bucket.put_object,
                object_name,
                file_data,
                headers=headers
            )
            
            upload_result = {
                "bucket": bucket_name,
                "object_name": object_name,
                "etag": result.etag.strip('"'),
                "request_id": result.request_id,
                "crc": getattr(result, 'crc', None)
            }
            
            # 同步索引到Elasticsearch
            try:
                from app.services.elasticsearch_service import elasticsearch_service
                file_info = {
                    "content_type": content_type,
                    "size": file_size,
                    "etag": result.etag.strip('"'),
                    "metadata": metadata or {},
                    "last_modified": datetime.now().isoformat(),
                    "storage_type": "oss"
                }
                await elasticsearch_service.index_file(bucket_name, object_name, file_info)
            except Exception as es_error:
                print(f"Elasticsearch indexing failed: {es_error}")
            
            return upload_result
        except OssError as e:
            raise Exception(f"Error uploading file: {str(e)}")
    
    async def download_file(self, bucket_name: str, object_name: str) -> Tuple[bytes, Dict[str, Any]]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            def _read_object():
                resp = bucket.get_object(object_name)
                data_bytes = resp.read()
                
                # 获取对象信息
                obj_info = bucket.head_object(object_name)
                
                meta = {
                    "content_type": obj_info.content_type,
                    "etag": obj_info.etag.strip('"'),
                    "last_modified": obj_info.last_modified.isoformat() if obj_info.last_modified else None,
                    "size": len(data_bytes),
                    "storage_class": getattr(obj_info, 'storage_class', None)
                }
                return data_bytes, meta
            
            data, metadata = await run_in_threadpool(_read_object)
            return data, metadata
        except OssError as e:
            raise Exception(f"Error downloading file: {str(e)}")
    
    async def delete_object(self, bucket_name: str, object_name: str) -> Dict[str, str]:
        try:
            bucket = self._get_bucket(bucket_name)
            await run_in_threadpool(bucket.delete_object, object_name)
            
            # 从Elasticsearch中删除索引
            try:
                from app.services.elasticsearch_service import elasticsearch_service
                await elasticsearch_service.delete_file(bucket_name, object_name)
            except Exception as es_error:
                print(f"Elasticsearch deletion failed: {es_error}")
            
            return {"message": f"Object '{object_name}' deleted successfully from bucket '{bucket_name}'"}
        except OssError as e:
            raise Exception(f"Error deleting object: {str(e)}")
    
    async def get_object_info(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        try:
            bucket = self._get_bucket(bucket_name)
            obj_info = await run_in_threadpool(bucket.head_object, object_name)
            
            # 提取自定义元数据
            custom_metadata = {}
            for key, value in obj_info.headers.items():
                if key.startswith('x-oss-meta-'):
                    custom_key = key[11:]  # 移除'x-oss-meta-'前缀
                    custom_metadata[custom_key] = value
            
            return {
                "name": object_name,
                "size": obj_info.content_length,
                "etag": obj_info.etag.strip('"'),
                "content_type": obj_info.content_type,
                "last_modified": obj_info.last_modified.isoformat() if obj_info.last_modified else None,
                "storage_class": getattr(obj_info, 'storage_class', None),
                "metadata": custom_metadata
            }
        except OssError as e:
            raise Exception(f"Error getting object info: {str(e)}")
    
    async def generate_presigned_url(self, bucket_name: str, object_name: str, 
                                   expires: int = 3600, method: str = "GET") -> str:
        try:
            bucket = self._get_bucket(bucket_name)
            
            if method.upper() == "GET":
                url = await run_in_threadpool(
                    bucket.sign_url,
                    'GET',
                    object_name,
                    expires
                )
            elif method.upper() == "PUT":
                url = await run_in_threadpool(
                    bucket.sign_url,
                    'PUT',
                    object_name,
                    expires
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return url
        except OssError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    async def copy_object(self, source_bucket: str, source_object: str, 
                         dest_bucket: str, dest_object: str) -> Dict[str, Any]:
        try:
            dest_bucket_obj = self._get_bucket(dest_bucket)
            
            # OSS复制对象的源格式
            copy_source = f'{source_bucket}/{source_object}'
            
            result = await run_in_threadpool(
                dest_bucket_obj.copy_object,
                copy_source,
                dest_object
            )
            
            return {
                "source": f"{source_bucket}/{source_object}",
                "destination": f"{dest_bucket}/{dest_object}",
                "etag": result.etag.strip('"'),
                "request_id": result.request_id
            }
        except OssError as e:
            raise Exception(f"Error copying object: {str(e)}")
    
    async def set_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> Dict[str, str]:
        try:
            bucket = self._get_bucket(bucket_name)
            policy_text = json.dumps(policy, ensure_ascii=False, indent=2)
            
            await run_in_threadpool(bucket.put_bucket_policy, policy_text)
            return {"message": f"Policy set successfully for bucket '{bucket_name}'"}
        except OssError as e:
            raise Exception(f"Error setting bucket policy: {str(e)}")
    
    async def get_bucket_policy(self, bucket_name: str) -> Dict[str, Any]:
        try:
            bucket = self._get_bucket(bucket_name)
            policy_result = await run_in_threadpool(bucket.get_bucket_policy)
            return json.loads(policy_result.policy) if policy_result.policy else {}
        except OssError as e:
            # 如果bucket没有设置策略，OSS会返回错误
            if 'NoSuchBucketPolicy' in str(e):
                return {}
            raise Exception(f"Error getting bucket policy: {str(e)}")
    
    async def make_bucket_public(self, bucket_name: str) -> Dict[str, str]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # OSS设置公共读权限
            await run_in_threadpool(bucket.put_bucket_acl, oss2.BUCKET_ACL_PUBLIC_READ)
            return {"message": f"Bucket '{bucket_name}' is now public"}
        except OssError as e:
            raise Exception(f"Error making bucket public: {str(e)}")
    
    async def make_bucket_private(self, bucket_name: str) -> Dict[str, str]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # OSS设置私有权限
            await run_in_threadpool(bucket.put_bucket_acl, oss2.BUCKET_ACL_PRIVATE)
            return {"message": f"Bucket '{bucket_name}' is now private"}
        except OssError as e:
            raise Exception(f"Error making bucket private: {str(e)}")
    
    async def get_public_url(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        try:
            bucket = self._get_bucket(bucket_name)
            
            # 检查对象是否存在
            await run_in_threadpool(bucket.head_object, object_name)
            
            # 构建公开访问URL
            settings = get_settings()
            protocol = "https" if settings.oss_use_ssl else "http"
            
            # OSS公开URL格式: https://bucket-name.endpoint/object-name
            # 或者: https://endpoint/bucket-name/object-name (如果使用路径风格)
            if settings.oss_use_cname:
                # 如果使用自定义域名
                public_url = f"{protocol}://{settings.oss_cname_domain}/{object_name}"
            else:
                # 标准OSS域名格式
                endpoint_without_protocol = settings.oss_endpoint.replace('http://', '').replace('https://', '')
                public_url = f"{protocol}://{bucket_name}.{endpoint_without_protocol}/{object_name}"
            
            # 检查bucket是否为公开读
            is_public = False
            try:
                acl_result = await run_in_threadpool(bucket.get_bucket_acl)
                is_public = acl_result.acl == oss2.BUCKET_ACL_PUBLIC_READ or acl_result.acl == oss2.BUCKET_ACL_PUBLIC_READ_WRITE
            except Exception as e:
                print(f"ACL check error: {e}")
            
            return {
                "public_url": public_url,
                "is_public": is_public,
                "bucket": bucket_name,
                "object": object_name,
                "note": "此URL仅在bucket设置为公开读时有效" if not is_public else "此URL可以直接访问"
            }
        except OssError as e:
            raise Exception(f"Error getting public URL: {str(e)}")
    
    def get_storage_type(self) -> StorageType:
        return StorageType.OSS