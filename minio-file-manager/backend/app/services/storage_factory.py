from typing import Dict, Any
from functools import lru_cache
from app.services.storage_service import StorageService, StorageType
from app.services.minio_storage_service import MinIOStorageService

try:
    from app.services.oss_service import OSSService
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    OSSService = None
from app.core.config import get_settings


class StorageFactory:
    """存储服务工厂类，根据配置创建相应的存储服务实例"""
    
    _instances: Dict[str, StorageService] = {}
    
    @classmethod
    def create_storage_service(cls, storage_type: StorageType = None) -> StorageService:
        """
        创建存储服务实例
        
        Args:
            storage_type: 存储类型，如果不指定则从配置中读取
            
        Returns:
            存储服务实例
        """
        settings = get_settings()
        
        # 如果没有指定类型，从配置中获取
        if storage_type is None:
            storage_type_str = getattr(settings, 'storage_type', 'minio').lower()
            try:
                storage_type = StorageType(storage_type_str)
            except ValueError:
                # 如果配置的类型无效，默认使用MinIO
                storage_type = StorageType.MINIO
        
        # 使用单例模式，避免重复创建实例
        type_key = storage_type.value
        if type_key not in cls._instances:
            if storage_type == StorageType.MINIO:
                cls._instances[type_key] = MinIOStorageService()
            elif storage_type == StorageType.OSS:
                if not OSS_AVAILABLE:
                    raise ValueError("OSS service is not available. Please install oss2 package.")
                cls._instances[type_key] = OSSService()
            else:
                raise ValueError(f"Unsupported storage type: {storage_type}")
        
        return cls._instances[type_key]
    
    @classmethod
    def get_current_storage_service(cls) -> StorageService:
        """
        获取当前配置的存储服务实例
        
        Returns:
            当前存储服务实例
        """
        return cls.create_storage_service()
    
    @classmethod
    def clear_instances(cls):
        """清空所有实例缓存（主要用于测试）"""
        cls._instances.clear()
    
    @classmethod
    def get_available_storage_types(cls) -> list[str]:
        """
        获取所有可用的存储类型
        
        Returns:
            可用存储类型列表
        """
        return [storage_type.value for storage_type in StorageType]
    
    @classmethod
    def validate_storage_config(cls, storage_type: StorageType) -> Dict[str, Any]:
        """
        验证指定存储类型的配置是否完整
        
        Args:
            storage_type: 存储类型
            
        Returns:
            验证结果字典，包含 is_valid 和 missing_configs
        """
        settings = get_settings()
        missing_configs = []
        
        if storage_type == StorageType.MINIO:
            required_configs = [
                ('minio_endpoint', 'MinIO endpoint'),
                ('minio_access_key', 'MinIO access key'),
                ('minio_secret_key', 'MinIO secret key')
            ]
            
            for config_key, config_desc in required_configs:
                if not hasattr(settings, config_key) or not getattr(settings, config_key):
                    missing_configs.append(config_desc)
        
        elif storage_type == StorageType.OSS:
            required_configs = [
                ('oss_endpoint', 'OSS endpoint'),
                ('oss_access_key', 'OSS access key'),
                ('oss_secret_key', 'OSS secret key'),
                ('oss_region', 'OSS region')
            ]
            
            for config_key, config_desc in required_configs:
                if not hasattr(settings, config_key) or not getattr(settings, config_key):
                    missing_configs.append(config_desc)
        
        return {
            'is_valid': len(missing_configs) == 0,
            'missing_configs': missing_configs,
            'storage_type': storage_type.value
        }


# 创建全局单例实例
@lru_cache()
def get_storage_service() -> StorageService:
    """
    获取存储服务实例的便捷函数
    
    Returns:
        存储服务实例
    """
    return StorageFactory.get_current_storage_service()


# 向后兼容的别名
storage_service = get_storage_service()