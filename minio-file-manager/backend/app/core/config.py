from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    # 存储类型选择 (minio 或 oss)
    storage_type: str = "minio"
    
    # MinIO 配置
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_use_ssl: bool = False
    
    # 阿里云OSS 配置
    oss_endpoint: str = ""
    oss_access_key: str = ""
    oss_secret_key: str = ""
    oss_region: str = ""
    oss_use_ssl: bool = True
    oss_use_cname: bool = False
    oss_cname_domain: str = ""
    
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_index: str = "minio_files"
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""
    elasticsearch_use_ssl: bool = False
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "newsletters"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    
    document_pipeline_enabled: bool = True
    document_pipeline_types: List[str] = ["markdown", "html"]
    document_pipeline_index: str = "minio_documents"
    document_pipeline_max_content_size: int = 50000
    
    api_port: int = 9011
    api_host: str = "0.0.0.0"
    
    api_title: str = "多云存储文件管理系统 API"
    api_version: str = "1.0.0"
    api_description: str = """
## 多云存储文件管理系统 API 文档

这是一个功能完整的多云对象存储管理系统，支持 MinIO 和阿里云 OSS，提供了统一的文件和存储桶管理接口。

### 主要功能模块

#### 🗂️ 存储桶管理
- **列出存储桶**：获取所有存储桶的列表和创建时间
- **创建存储桶**：创建新的存储桶，支持自定义命名
- **删除存储桶**：安全删除空存储桶
- **存储桶策略**：设置和获取存储桶的访问策略

#### 📁 文件对象管理
- **文件列表**：浏览存储桶中的所有文件和文件夹
- **文件上传**：支持单文件和多文件上传，可自定义元数据
- **文件下载**：直接下载文件到本地
- **文件删除**：删除指定的文件对象
- **文件信息**：获取文件的详细元数据信息
- **文件复制**：在存储桶之间复制文件

#### 🔐 高级功能
- **预签名 URL**：生成临时访问链接，支持上传和下载
- **访问策略**：精细化的存储桶访问权限控制
- **元数据管理**：为文件添加自定义元数据

### 技术特性
- ✅ RESTful API 设计
- ✅ 异步处理支持
- ✅ 完整的错误处理
- ✅ 模块化架构，易于集成
- ✅ 支持大文件上传
- ✅ CORS 跨域支持

### 使用说明
1. 所有 API 端点都以 `/api/v1` 为前缀
2. 文件上传使用 multipart/form-data 格式
3. 响应格式统一为 JSON
4. 错误响应包含详细的错误信息

### 认证说明
当前版本支持多种存储后端的认证：
- MinIO: 使用 Access Key 和 Secret Key 进行认证
- 阿里云OSS: 使用 Access Key ID 和 Access Key Secret 进行认证

所有认证凭据在服务器端配置，客户端无需处理认证逻辑。
未来版本将支持 JWT 令牌认证。

### 存储类型切换
通过配置文件中的 `STORAGE_TYPE` 参数可以在不同存储后端之间切换：
- `minio`: 使用 MinIO 作为存储后端
- `oss`: 使用阿里云 OSS 作为存储后端
"""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()