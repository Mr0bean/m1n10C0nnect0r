# 用户行为追踪API文档

## 概述

用户行为追踪API提供了记录、查询和分析用户在系统中各种操作行为的功能。所有行为数据存储在PostgreSQL数据库的`user_behaviors`表中。

## API端点

基础URL: `http://localhost:9011/api/v1/user-behaviors`

### 1. 记录单个用户行为

**端点**: `POST /record`

**描述**: 记录单个用户行为事件

**请求体**:
```json
{
  "behavior_type": "newsletter_view",  // 行为类型（必填）
  "user_id": "user_123",               // 用户ID（需要是users表中存在的ID）
  "session_id": "session_456",         // 会话ID（可选）
  "target_type": "newsletter",         // 目标类型（可选）
  "target_id": "nl_001",              // 目标ID（可选）
  "action_details": {                  // 行为详细信息（可选）
    "view_duration": 120,
    "scroll_depth": 0.75
  },
  "metadata": {                        // 额外元数据（可选）
    "device": "desktop",
    "browser": "Chrome"
  }
}
```

**支持的行为类型** (BehaviorType):
- 搜索相关: `search_query`, `search_result_click`, `search_filter_apply`
- 文档操作: `document_view`, `document_download`, `document_upload`, `document_delete`, `document_share`
- Newsletter相关: `newsletter_view`, `newsletter_like`, `newsletter_share`, `newsletter_comment`
- 系统操作: `user_login`, `user_logout`, `page_view`, `feature_use`
- MinIO操作: `bucket_create`, `bucket_delete`, `object_list`

**响应**:
```json
{
  "success": true,
  "behavior_id": "uuid-string",
  "created_at": "2025-08-12T12:34:04.698000",
  "error": null
}
```

### 2. 批量记录用户行为

**端点**: `POST /batch-record`

**描述**: 一次性记录多个用户行为

**请求体**:
```json
[
  {
    "behavior_type": "newsletter_view",
    "user_id": "user_123",
    "target_type": "newsletter",
    "target_id": "nl_001"
  },
  {
    "behavior_type": "newsletter_like",
    "user_id": "user_123",
    "target_type": "newsletter",
    "target_id": "nl_001"
  }
]
```

**响应**:
```json
{
  "total": 2,
  "success": 2,
  "failed": 0,
  "results": [...]
}
```

### 3. 查询用户行为

**端点**: `GET /query`

**查询参数**:
- `user_id`: 用户ID
- `session_id`: 会话ID
- `behavior_type`: 行为类型
- `target_type`: 目标类型
- `target_id`: 目标ID
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `page`: 页码（默认1）
- `size`: 每页数量（默认20，最大100）

**响应**:
```json
{
  "behaviors": [
    {
      "id": "uuid-string",
      "user_id": "user_123",
      "behavior_type": "newsletter_view",
      "target_type": "newsletter",
      "target_id": "nl_001",
      "created_at": "2025-08-12T12:34:04.698000"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20
}
```

### 4. 获取行为统计

**端点**: `GET /statistics`

**查询参数**:
- `user_id`: 用户ID（可选）
- `behavior_type`: 行为类型（可选）
- `days`: 统计天数（默认7，最大365）

**响应**:
```json
{
  "total_behaviors": 150,
  "unique_users": 25,
  "unique_sessions": 45,
  "behavior_counts": {
    "newsletter_view": 80,
    "document_download": 30,
    "search_query": 40
  },
  "period": {
    "start": "2025-08-05T00:00:00",
    "end": "2025-08-12T00:00:00",
    "days": 7
  }
}
```

### 5. 获取热门目标

**端点**: `GET /popular/{target_type}`

**路径参数**:
- `target_type`: 目标类型（如：newsletter, document, search_query）

**查询参数**:
- `behavior_type`: 行为类型（可选）
- `limit`: 返回数量（默认10，最大100）
- `days`: 统计天数（默认7，最大365）

**响应**:
```json
{
  "target_type": "newsletter",
  "targets": [
    {
      "target_id": "nl_001",
      "access_count": 120,
      "unique_users": 45,
      "last_accessed": "2025-08-12T12:00:00"
    }
  ],
  "period": {
    "start": "2025-08-05T00:00:00",
    "end": "2025-08-12T00:00:00",
    "days": 7
  }
}
```

### 6. 获取用户时间线

**端点**: `GET /user/{user_id}/timeline`

**路径参数**:
- `user_id`: 用户ID

**查询参数**:
- `days`: 查看最近N天的行为（默认7，最大365）
- `page`: 页码（默认1）
- `size`: 每页数量（默认50，最大200）

**响应**:
```json
{
  "user_id": "user_123",
  "timeline": [...],
  "statistics": {...},
  "period": {...},
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 100
  }
}
```

## 数据库表结构

```sql
CREATE TABLE public.user_behaviors (
    id TEXT PRIMARY KEY,
    "userId" TEXT REFERENCES users(id),
    action TEXT NOT NULL,
    "targetType" TEXT,
    "targetId" TEXT NOT NULL,
    metadata JSONB,
    "createdAt" TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 使用示例

### Python示例

```python
import requests
import json

# 记录用户查看Newsletter的行为
behavior = {
    "behavior_type": "newsletter_view",
    "user_id": "cmdu8uetk007dvjcsfjnqg2wd",  # 需要是存在的用户ID
    "target_type": "newsletter",
    "target_id": "newsletter_001",
    "action_details": {
        "view_duration": 120,
        "scroll_depth": 0.75
    },
    "metadata": {
        "device": "desktop",
        "browser": "Chrome",
        "source": "homepage"
    }
}

response = requests.post(
    "http://localhost:9011/api/v1/user-behaviors/record",
    json=behavior,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://localhost:3000"
    }
)

if response.status_code == 200:
    result = response.json()
    if result["success"]:
        print(f"行为记录成功，ID: {result['behavior_id']}")
    else:
        print(f"记录失败: {result['error']}")
```

### JavaScript/TypeScript示例

```typescript
// 记录搜索行为
const recordSearchBehavior = async (query: string, userId: string) => {
  const behavior = {
    behavior_type: 'search_query',
    user_id: userId,
    target_type: 'search',
    target_id: '',
    action_details: {
      query: query,
      timestamp: new Date().toISOString()
    }
  };

  const response = await fetch('http://localhost:9011/api/v1/user-behaviors/record', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(behavior)
  });

  return await response.json();
};
```

## 注意事项

1. **用户ID约束**: `userId`字段必须引用`users`表中存在的用户ID。如果用户未登录，可以传入NULL，但需要注意数据库约束。

2. **必填字段**: 
   - `action` (behavior_type): 行为类型必须提供
   - `targetId`: 目标ID不能为NULL，如果没有具体目标，可以使用空字符串

3. **元数据存储**: 所有额外信息（如session_id、ip_address、user_agent等）都存储在`metadata` JSONB字段中

4. **性能优化**: 表已创建以下索引：
   - userId索引
   - action索引
   - targetType和targetId组合索引
   - createdAt索引

5. **数据清理**: 建议定期清理过期的行为记录以保持数据库性能

## 错误处理

常见错误：
- `500`: 服务器内部错误
- `400`: 请求参数错误
- `404`: 资源不存在

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 扩展建议

1. **添加数据分析功能**：
   - 用户行为漏斗分析
   - 用户路径分析
   - 留存率分析

2. **实时统计**：
   - 使用WebSocket推送实时行为数据
   - 集成实时分析工具

3. **数据导出**：
   - 支持导出CSV/Excel格式的行为数据
   - 提供数据可视化报表

4. **隐私保护**：
   - 添加数据脱敏功能
   - 支持GDPR合规的数据删除请求