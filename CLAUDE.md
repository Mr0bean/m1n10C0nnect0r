# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Quick Start (Recommended)

```bash
# Start backend service (from project root)
./scripts/start_backend.sh  # Runs on http://localhost:8000

# Start frontend service (from project root) 
./scripts/start_frontend.sh  # Runs on http://localhost:9010
```

### MinIO File Manager Backend

```bash
# Navigate to backend
cd minio-file-manager/backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server (development)
python -m uvicorn app.main:app --reload --port 9011

# Alternative: Run with convenience script (uses port 8000)
../scripts/start_backend.sh

# Access API documentation
# Swagger UI: http://localhost:9011/docs (or :8000/docs with script)
# ReDoc: http://localhost:9011/redoc (or :8000/redoc with script)
```

### MinIO File Manager Frontend

```bash
# Navigate to frontend
cd minio-file-manager/frontend

# Install dependencies
npm install

# Run development server
npm run dev  # Runs on http://localhost:9010

# Build for production
npm run build

# Start production build
npm run start

# Lint code
npm run lint

# Alternative: Run with convenience script
../scripts/start_frontend.sh
```

### Newsletter Upload to Elasticsearch

```bash
# Test Newsletter upload functionality
python minio-file-manager/backend/test_newsletter_upload.py

# Upload articles from crawler data
python minio-file-manager/backend/upload_crawled_articles.py [JSON_FILE] --verify

# Batch upload with custom size
python minio-file-manager/backend/upload_crawled_articles.py articles.json --batch-size 50
```

### Testing and Utilities

```bash
# Test multi-storage configuration and switching
python minio-file-manager/backend/test_storage_factory.py

# Test bucket operations (works with any storage backend)
python minio-file-manager/backend/test_public_bucket.py

# Test public URL generation
python minio-file-manager/backend/test_public_url.py

# Test delete operations
python minio-file-manager/backend/test_delete_api.py

# Test PostgreSQL integration
python minio-file-manager/backend/test_pg_integration.py

# Test complete document pipeline
python minio-file-manager/backend/test_complete_pipeline.py

# Clear Elasticsearch indices
python scripts/clear_es.py

# Clear MinIO storage
python scripts/clear_minio.py

# Show Elasticsearch cluster details
python scripts/show_es_details.py
```

## Architecture Overview

This project is a multi-cloud object storage management system that supports both MinIO and Aliyun OSS, with Elasticsearch integration for content indexing. It consists of two main components:

### 1. Multi-Cloud File Manager
A full-stack application for managing files across different storage backends:

**Backend (FastAPI)**:
- `app/services/storage_service.py`: Abstract storage interface for multi-cloud support
- `app/services/storage_factory.py`: Factory pattern for creating storage instances
- `app/services/minio_storage_service.py`: MinIO storage implementation
- `app/services/oss_service.py`: Aliyun OSS storage implementation  
- `app/services/minio_service.py`: Legacy MinIO service (deprecated)
- `app/services/elasticsearch_service.py`: Basic ES integration for file metadata
- `app/services/postgresql_service.py`: PostgreSQL integration for logging and metadata
- `app/services/article_processing_service.py`: Article processing and index management
- `app/services/index_initializer.py`: Elasticsearch index setup and configuration
- `app/api/endpoints/`: RESTful endpoints for buckets, objects, search, and document operations

**Frontend (Next.js 15 + React 19)**:
- Modern UI with Tailwind CSS and shadcn/ui components
- Zustand for state management
- Drag-and-drop file upload support

### 2. Newsletter Article System
Specialized system for managing Newsletter articles with Elasticsearch integration:

**Key Features**:
- **Deduplication**: Uses content_hash (SHA256) and article ID to prevent duplicates
- **Multi-dimensional Scoring**: Calculates popularity, freshness, quality, and combined scores
- **Advanced Search**: Full-text search with field boosting, tag filtering, date ranges
- **Recommendations**: Similar articles (More Like This), trending articles

**Elasticsearch Index Structure**:
- Index: `newsletter_articles`
- Custom analyzers: English analyzer with synonyms, N-gram analyzer for fuzzy matching
- Nested tags structure for complex queries
- Dense vector field (384 dims) prepared for future embeddings

## Data Flow

### Article Upload Pipeline
1. **Source**: Crawler output from `/Users/ruanchuhao/Downloads/Codes/NewsLetters/爬虫mlp`
2. **Processing**: Article data with metadata and local images
3. **Deduplication**: Check by ID and content hash
4. **Score Calculation**: Popularity, freshness, quality scores
5. **Storage**: 
   - Optional: MinIO for raw JSON files
   - Required: Elasticsearch for searchable index

### API Integration Points

**Newsletter Endpoints** (`/api/v1/newsletter/`):
- `POST /upload-article`: Single article with dedup check
- `POST /bulk-upload`: Batch upload with progress tracking
- `POST /search`: Advanced search with multiple filters
- `GET /article/{id}/similar`: Find similar articles
- `GET /trending`: Get popular articles by time range
- `GET /statistics`: Aggregated statistics

**MinIO Endpoints** (`/api/v1/`):
- Bucket management: create, delete, list, set public/private
- Object operations: upload, download, copy, delete
- URL generation: public URLs and presigned URLs

## Configuration

### Multi-Cloud Storage Configuration

The system supports seamless switching between different storage backends by modifying only the configuration file. No code changes are required.

### Backend Configuration (.env)

#### Storage Type Selection
```env
# Storage backend type: minio or oss
STORAGE_TYPE=minio
```

#### MinIO Configuration (when STORAGE_TYPE=minio)
```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin  
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=false
```

#### Aliyun OSS Configuration (when STORAGE_TYPE=oss)
```env
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY=your-oss-access-key-id
OSS_SECRET_KEY=your-oss-access-key-secret  
OSS_REGION=cn-hangzhou
OSS_USE_SSL=true
OSS_USE_CNAME=false
OSS_CNAME_DOMAIN=
```

#### Other Services Configuration
```env
# Elasticsearch Settings
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=minio_files
ELASTICSEARCH_USE_SSL=false

# PostgreSQL Settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=newsletters
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# API Settings
API_HOST=0.0.0.0
API_PORT=9011
```

### Newsletter Article Structure
Articles from the crawler follow this structure:
```python
{
    "id": int,                      # Unique identifier
    "title": str,                   # Article title
    "subtitle": str,                # Subtitle
    "content": str,                 # Full content (optional)
    "post_date": str,              # ISO format date
    "type": str,                   # newsletter/tutorial/paper
    "wordcount": int,              # Word count
    "reactions": dict,             # {"❤": count}
    "postTags": list,              # [{"id", "name", "slug"}]
    "local_images": list,          # Image metadata
    "content_hash": str            # SHA256 for deduplication
}
```

## Key Implementation Details

### Deduplication Logic
The system prevents duplicate articles using:
1. Article ID check (primary key)
2. Content hash check (SHA256 of title + subtitle + content)
3. Automatic skip with detailed reporting in bulk operations

### Scoring Algorithm
```python
# Popularity Score (0-100+)
popularity = reaction_count * 0.3 + wordcount_bonus + time_decay + type_bonus

# Freshness Score (0-100)
freshness = max(0, 100 - days_since_publish * 0.5)

# Quality Score (0-100)
quality = wordcount_score + reaction_score + tag_score

# Combined Score (weighted average)
combined = popularity * 0.4 + freshness * 0.3 + quality * 0.3
```

### Error Handling
- All newsletter operations return success/failure status with messages
- Bulk operations provide detailed skipped/error reports
- Elasticsearch connection failures handled gracefully
- MinIO operations include retry logic

## Integration with Crawler Data

The system is designed to work with output from the Newsletter crawler at `/Users/ruanchuhao/Downloads/Codes/NewsLetters/爬虫mlp`:

1. **Input Format**: `processed_articles.json` from crawler
2. **Preprocessing**: Handles both single articles and arrays
3. **Field Mapping**: Automatic conversion of `postTags` format
4. **Image References**: Preserves local_images metadata

## Performance Considerations

- **Batch Processing**: Default 100 articles per batch
- **Concurrent Uploads**: Async processing for efficiency
- **Index Optimization**: 2 shards, 1 replica for newsletter index
- **Connection Pooling**: Reuses Elasticsearch client connections
- **Memory Management**: Streaming for large file uploads

## Testing Strategy

The codebase includes comprehensive test scripts:
- `test_newsletter_upload.py`: Tests all Newsletter ES features
- `upload_crawled_articles.py`: Production upload with verification
- `test_public_bucket.py`: MinIO bucket operations
- `test_elasticsearch.py`: Basic ES connectivity

Each test includes sample data generation and verification steps.

## Storage Backend Switching

### Seamless Migration Strategy

The system implements a factory pattern that allows switching between MinIO and OSS without code changes:

#### 1. Configuration-Only Switching
```bash
# Switch to MinIO
echo "STORAGE_TYPE=minio" > .env

# Switch to OSS  
echo "STORAGE_TYPE=oss" > .env

# Restart the service
python -m uvicorn app.main:app --reload --port 9011
```

#### 2. Validation and Testing
```bash
# Test current storage configuration
python minio-file-manager/backend/test_storage_factory.py

# Validate configuration for specific storage type
python -c "
from app.services.storage_factory import StorageFactory
from app.services.storage_service import StorageType

# Test MinIO config
result = StorageFactory.validate_storage_config(StorageType.MINIO)
print(f'MinIO config valid: {result[\"is_valid\"]}')

# Test OSS config  
result = StorageFactory.validate_storage_config(StorageType.OSS)
print(f'OSS config valid: {result[\"is_valid\"]}')
"
```

#### 3. Migration Considerations

**Data Migration**: 
- The system provides unified APIs but data doesn't automatically migrate between backends
- Use the copy/download APIs to manually migrate data if needed
- Consider running both backends temporarily during migration

**URL Compatibility**:
- Public URLs will change when switching backends
- Presigned URLs are backend-specific and will need regeneration
- Update any hardcoded URLs in client applications

**Feature Differences**:
- MinIO: Full S3 API compatibility, self-hosted
- OSS: Alibaba Cloud managed service, additional features like image processing
- Both support the same core operations through the unified interface

#### 4. Deployment Best Practices

**Development**:
- Use MinIO for local development (easier setup)
- Test with actual OSS in staging environment

**Production**: 
- Choose based on requirements (cost, performance, compliance)
- OSS for China-based deployments, MinIO for self-hosted solutions
- Configure monitoring and backup strategies for chosen backend

**Rollback Strategy**:
- Keep configuration backups for quick rollback
- Test rollback procedures in non-production environment
- Monitor application metrics after switching