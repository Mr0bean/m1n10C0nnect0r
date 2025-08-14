# m1n10C0nnect0r - 多云存储文件管理系统 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2.5-black.svg)](https://nextjs.org)

一个功能完整的多云对象存储管理系统，支持 **MinIO** 和 **阿里云 OSS**，集成 **Elasticsearch** 全文搜索和 **PostgreSQL** 数据存储，提供统一的文件管理接口和智能文档处理管道。

## ✨ 核心特性

### 🌐 多云存储支持
- **MinIO**: 私有云对象存储，完全 S3 兼容
- **阿里云 OSS**: 公有云对象存储服务
- **一键切换**: 通过配置文件无缝切换存储后端
- **统一接口**: 相同的 API 支持不同的存储提供商

### 📁 文件管理功能
- **存储桶管理**: 创建、删除、列表、权限控制
- **文件操作**: 上传、下载、删除、复制、移动
- **批量处理**: 支持多文件上传和批量操作
- **预签名 URL**: 生成临时访问链接
- **元数据管理**: 自定义文件元数据和标签

### 🔍 智能搜索与推荐
- **全文搜索**: 基于 Elasticsearch 的强大搜索能力
- **模糊搜索**: 智能拼写纠错和相似度匹配
- **文档推荐**: More Like This (MLT) 相似文档推荐
- **多维过滤**: 按类型、日期、标签等多维度筛选

### 📰 Newsletter 管理系统
- **智能去重**: 基于内容哈希的重复检测
- **多维评分**: 热度、新鲜度、质量综合评分算法
- **高级搜索**: 支持复杂查询和聚合统计
- **趋势分析**: 热门文章和趋势追踪

### 🔄 文档处理管道
- **自动识别**: 智能检测 Markdown、HTML 文档
- **内容提取**: 自动解析和结构化处理
- **双重存储**: 同时存储到对象存储和搜索引擎
- **实时索引**: 上传即索引，立即可搜索

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │  文件管理界面  │ │   搜索界面    │ │    Elasticsearch 管理    │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────┴───────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │   存储桶 API  │ │   文件 API    │ │      搜索 & 推荐 API      │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ Newsletter API│ │ 文档管道服务  │ │      多存储工厂模式       │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                        存储 & 数据层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐ │
│  │    MinIO    │  │ 阿里云 OSS   │  │      Elasticsearch       │ │
│  │  对象存储    │  │   对象存储   │  │       搜索引擎           │ │
│  └─────────────┘  └─────────────┘  └──────────────────────────┘ │
│                    ┌─────────────────────────────────────────┐  │
│                    │           PostgreSQL 数据库             │  │
│                    │         元数据 & 日志存储               │  │
│                    └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.12+
- **Node.js**: 18+
- **MinIO**: 最新版本 (可选)
- **Elasticsearch**: 8.12+
- **PostgreSQL**: 14+ (可选)

### 1. 克隆项目

```bash
git clone https://github.com/Mr0bean/m1n10C0nnect0r.git
cd m1n10C0nnect0r
```

### 2. 后端设置

```bash
cd minio-file-manager/backend

# 安装依赖
pip install -r requirements.txt

# 创建环境配置文件
cat > .env << EOF
# 存储类型选择 (minio 或 oss)
STORAGE_TYPE=minio

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=false

# Elasticsearch 配置
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=minio_files
ELASTICSEARCH_USE_SSL=false

# PostgreSQL 配置 (可选)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=newsletters
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# 文档管道配置
DOCUMENT_PIPELINE_ENABLED=true
DOCUMENT_PIPELINE_TYPES=["markdown", "html"]
DOCUMENT_PIPELINE_INDEX=minio_documents
DOCUMENT_PIPELINE_MAX_CONTENT_SIZE=50000

# API 配置
API_HOST=0.0.0.0
API_PORT=9011
EOF

# 启动后端服务
python -m uvicorn app.main:app --reload --port 9011
```

### 3. 前端设置

```bash
cd minio-file-manager/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 便捷启动脚本

```bash
# 从项目根目录启动
./scripts/start_backend.sh   # 后端服务 (端口 8000)
./scripts/start_frontend.sh  # 前端服务 (端口 9010)
```

### 5. 访问应用

- **前端界面**: http://localhost:9010
- **API 文档**: http://localhost:9011/docs
- **ReDoc 文档**: http://localhost:9011/redoc

## 📖 API 文档

### 存储桶管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/buckets` | 列出所有存储桶 |
| POST | `/api/v1/buckets` | 创建新存储桶 |
| DELETE | `/api/v1/buckets/{bucket_name}` | 删除存储桶 |
| PUT | `/api/v1/buckets/{bucket_name}/public` | 设置公开访问 |
| PUT | `/api/v1/buckets/{bucket_name}/private` | 设置私有访问 |

### 文件对象管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/objects/{bucket_name}` | 列出对象 |
| POST | `/api/v1/objects/{bucket_name}/upload` | 上传文件 |
| GET | `/api/v1/objects/{bucket_name}/{object_name}/download` | 下载文件 |
| GET | `/api/v1/objects/{bucket_name}/{object_name}/info` | 获取文件信息 |
| DELETE | `/api/v1/objects/{bucket_name}/{object_name}` | 删除文件 |
| POST | `/api/v1/objects/copy` | 复制文件 |
| POST | `/api/v1/objects/presigned-url` | 生成预签名URL |

### 文档搜索与推荐

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/documents/search` | 搜索文档 |
| GET | `/api/v1/documents/similar/{document_id}` | 获取相似文档 |
| GET | `/api/v1/documents/types` | 支持的文档类型 |
| GET | `/api/v1/documents/stats` | 统计信息 |

### Newsletter 管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/newsletter/upload-article` | 上传单篇文章 |
| POST | `/api/v1/newsletter/bulk-upload` | 批量上传文章 |
| POST | `/api/v1/newsletter/search` | 搜索文章 |
| GET | `/api/v1/newsletter/article/{id}/similar` | 相似文章推荐 |
| GET | `/api/v1/newsletter/trending` | 热门文章 |
| GET | `/api/v1/newsletter/statistics` | 统计信息 |

## ⚙️ 配置指南

### 多云存储配置

#### MinIO 配置
```env
STORAGE_TYPE=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=false
```

#### 阿里云 OSS 配置
```env
STORAGE_TYPE=oss
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY=your-access-key-id
OSS_SECRET_KEY=your-access-key-secret
OSS_REGION=cn-hangzhou
OSS_USE_SSL=true
OSS_USE_CNAME=false
OSS_CNAME_DOMAIN=
```

### 存储后端切换

系统支持运行时无缝切换存储后端：

```bash
# 切换到 MinIO
echo "STORAGE_TYPE=minio" >> .env

# 切换到阿里云 OSS
echo "STORAGE_TYPE=oss" >> .env

# 重启服务生效
```

### Elasticsearch 配置

```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=minio_files
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_USE_SSL=false
```

### PostgreSQL 配置

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=newsletters
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
```

## 🧪 测试与验证

### 测试脚本

```bash
# 测试多存储配置
python minio-file-manager/backend/test_storage_factory.py

# 测试文档管道
python minio-file-manager/backend/test_document_pipeline.py

# 测试 Newsletter 功能
python minio-file-manager/backend/test_newsletter_upload.py

# 测试公开 URL 生成
python minio-file-manager/backend/test_public_url.py

# 测试 PostgreSQL 集成
python minio-file-manager/backend/test_pg_integration.py

# 测试完整管道
python minio-file-manager/backend/test_complete_pipeline.py
```

### 验证存储配置

```bash
# 验证 MinIO 配置
python -c "
from app.services.storage_factory import StorageFactory
from app.services.storage_service import StorageType
result = StorageFactory.validate_storage_config(StorageType.MINIO)
print(f'MinIO 配置有效: {result[\"is_valid\"]}')
"

# 验证 OSS 配置
python -c "
from app.services.storage_factory import StorageFactory
from app.services.storage_service import StorageType
result = StorageFactory.validate_storage_config(StorageType.OSS)
print(f'OSS 配置有效: {result[\"is_valid\"]}')
"
```

## 📊 性能特性

### 文档处理性能
- **批量处理**: 默认 100 文档/批次
- **异步处理**: 并发上传和索引
- **内存优化**: 流式处理大文件
- **连接池**: 复用 Elasticsearch 连接

### 搜索性能
- **索引优化**: 2 分片，1 副本
- **查询优化**: 字段权重和模糊匹配
- **缓存策略**: 查询结果缓存
- **分页支持**: 高效的深度分页

### Newsletter 评分算法

```python
# 热度评分 (0-100+)
popularity = reaction_count * 0.3 + wordcount_bonus + time_decay + type_bonus

# 新鲜度评分 (0-100)
freshness = max(0, 100 - days_since_publish * 0.5)

# 质量评分 (0-100)
quality = wordcount_score + reaction_score + tag_score

# 综合评分 (加权平均)
combined = popularity * 0.4 + freshness * 0.3 + quality * 0.3
```

## 🛠️ 开发指南

### 项目结构

```
m1n10C0nnect0r/
├── minio-file-manager/
│   ├── backend/                 # FastAPI 后端
│   │   ├── app/
│   │   │   ├── api/            # API 路由
│   │   │   ├── core/           # 核心配置
│   │   │   ├── services/       # 业务服务
│   │   │   └── schemas/        # 数据模型
│   │   ├── config/             # Elasticsearch 配置
│   │   └── requirements.txt    # Python 依赖
│   └── frontend/               # Next.js 前端
│       ├── app/                # App Router
│       ├── components/         # React 组件
│       ├── lib/                # 工具库
│       └── store/              # 状态管理
├── scripts/                    # 便捷脚本
├── docs/                       # 文档
└── backups/                    # 备份文件
```

### 添加新的存储后端

1. 实现 `StorageService` 接口
2. 在 `StorageFactory` 中注册新类型
3. 更新配置文件和环境变量
4. 添加相应的测试用例

### 扩展文档处理类型

1. 在 `document_pipeline_service.py` 中添加新的处理器
2. 更新 `DOCUMENT_PIPELINE_TYPES` 配置
3. 实现内容提取逻辑
4. 添加测试验证

## 🔧 运维指南

### 备份策略

```bash
# 创建完整备份
./backup_project.sh

# 恢复备份
tar -xzf backups/backup_TIMESTAMP.tar.gz
```

### 监控与日志

```bash
# 查看 Elasticsearch 集群状态
python scripts/show_es_details.py

# 清理 Elasticsearch 索引
python scripts/clear_es.py

# 清理 MinIO 存储
python scripts/clear_minio.py
```

### 生产部署

1. **环境变量**: 使用生产环境配置
2. **HTTPS**: 配置 SSL/TLS 证书
3. **负载均衡**: 使用 Nginx 或类似服务
4. **监控**: 集成 Prometheus 和 Grafana
5. **日志**: 配置集中化日志收集

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2025-01-XX)
- ✅ 多云存储支持 (MinIO + 阿里云 OSS)
- ✅ 文档处理管道
- ✅ Newsletter 管理系统
- ✅ Elasticsearch 全文搜索
- ✅ PostgreSQL 数据存储
- ✅ Next.js 现代化前端界面

### 计划中的功能
- [ ] 用户认证与权限管理
- [ ] 文件版本控制
- [ ] 向量搜索 (Embeddings)
- [ ] 实时通知系统
- [ ] 分片上传支持
- [ ] Docker 容器化部署

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Next.js](https://nextjs.org/) - React 全栈框架
- [MinIO](https://min.io/) - 高性能对象存储
- [Elasticsearch](https://www.elastic.co/) - 分布式搜索引擎
- [shadcn/ui](https://ui.shadcn.com/) - 现代化 UI 组件库

## 📞 支持与联系

- **GitHub Issues**: [项目问题追踪](https://github.com/Mr0bean/m1n10C0nnect0r/issues)
- **文档**: 查看 `docs/` 目录获取详细文档
- **示例**: 查看 `examples/` 目录获取使用示例

---

⭐ 如果这个项目对你有帮助，请给个 Star！

