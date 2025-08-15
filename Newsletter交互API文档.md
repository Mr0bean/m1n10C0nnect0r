# Newsletter交互API文档

## 基础信息

- **基础URL**: `http://localhost:9011/api/v1`
- **认证方式**: 暂无（使用默认用户）
- **响应格式**: JSON
- **字符编码**: UTF-8

## API接口列表

### 1. 文章点赞/取消点赞

对Newsletter文章进行点赞或取消点赞操作。

**接口地址**
```
POST /api/v1/newsletters/{newsletter_id}/like
```

**请求参数**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| newsletter_id | path | string | 是 | 文章ID |
| action | body | string | 是 | 操作类型: "like" 或 "unlike" |
| userId | body | string | 否 | 用户ID（可选，默认使用测试用户） |

**请求示例**
```bash
curl -X POST "http://localhost:9011/api/v1/newsletters/e8ffb4ac-e3ea-4e3a-835a-e6ec6ff6cf30/like" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "like"
  }'
```

**响应示例**
```json
{
  "success": true,
  "newsletterId": "e8ffb4ac-e3ea-4e3a-835a-e6ec6ff6cf30",
  "isLiked": true,
  "likeCount": 15,
  "userId": "cmdu8uetk007dvjcsfjnqg2wd",
  "timestamp": "2025-08-13T08:30:00.000Z"
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| newsletterId | string | 文章ID |
| isLiked | boolean | 当前用户是否已点赞 |
| likeCount | integer | 文章总点赞数 |
| userId | string | 操作用户ID |
| timestamp | string | 操作时间 |

**错误响应**
```json
{
  "detail": "Newsletter not found"
}
```

---

### 2. 获取文章评论列表

获取指定Newsletter的评论列表，支持分页和排序。

**接口地址**
```
GET /api/v1/newsletters/{newsletter_id}/comments
```

**请求参数**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|------|--------|------|
| newsletter_id | path | string | 是 | - | 文章ID |
| page | query | integer | 否 | 1 | 页码（从1开始） |
| pageSize | query | integer | 否 | 20 | 每页数量（1-100） |
| sortBy | query | string | 否 | latest | 排序方式: "latest"(最新) 或 "popular"(最热) |

**请求示例**
```bash
curl "http://localhost:9011/api/v1/newsletters/e8ffb4ac-e3ea-4e3a-835a-e6ec6ff6cf30/comments?page=1&pageSize=10&sortBy=latest"
```

**响应示例**
```json
{
  "success": true,
  "total": 23,
  "page": 1,
  "pageSize": 10,
  "hasNext": true,
  "comments": [
    {
      "id": "d2ee4c5e-0765-45b2-8c76-e201f218cb88",
      "content": "这篇文章对机器学习的分析很深入，特别是关于transformer架构的部分。",
      "userId": "cmdu8uetk007dvjcsfjnqg2wd",
      "parentId": null,
      "likeCount": 5,
      "replyCount": 2,
      "status": "PUBLISHED",
      "createdAt": "2025-08-13T08:00:00Z",
      "updatedAt": "2025-08-13T08:00:00Z",
      "author": {
        "id": "cmdu8uetk007dvjcsfjnqg2wd",
        "name": "张三",
        "email": "user1@test.com",
        "avatar": "https://example.com/avatar1.jpg"
      },
      "replies": [
        {
          "id": "b8f3a77e-d07d-40a0-b154-c4efe045db1a",
          "content": "同意你的观点，特别是关于注意力机制的解释。",
          "userId": "user_002",
          "parentId": "d2ee4c5e-0765-45b2-8c76-e201f218cb88",
          "likeCount": 2,
          "status": "PUBLISHED",
          "createdAt": "2025-08-13T08:30:00Z",
          "author": {
            "id": "user_002",
            "name": "李四",
            "email": "user2@test.com",
            "avatar": "https://example.com/avatar2.jpg"
          }
        }
      ]
    }
  ],
  "error": null
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| total | integer | 评论总数 |
| page | integer | 当前页码 |
| pageSize | integer | 每页数量 |
| hasNext | boolean | 是否有下一页 |
| comments | array | 评论列表 |
| comments[].id | string | 评论ID |
| comments[].content | string | 评论内容 |
| comments[].userId | string | 评论者用户ID |
| comments[].parentId | string/null | 父评论ID（主评论为null） |
| comments[].likeCount | integer | 点赞数 |
| comments[].replyCount | integer | 回复数 |
| comments[].status | string | 状态: PUBLISHED/DELETED |
| comments[].createdAt | string | 创建时间 |
| comments[].author | object | 作者信息 |
| comments[].author.name | string | 作者名称 |
| comments[].author.avatar | string | 作者头像 |
| comments[].replies | array | 前3条回复（简要列表） |

---

### 3. 发表评论

对Newsletter发表评论或回复其他评论。

**接口地址**
```
POST /api/v1/newsletters/{newsletter_id}/comments
```

**请求参数**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| newsletter_id | path | string | 是 | 文章ID |
| content | body | string | 是 | 评论内容（1-1000字符） |
| parentId | body | string/null | 否 | 父评论ID（回复时填写，主评论为null） |
| userId | body | string | 否 | 用户ID（可选，默认使用测试用户） |

**请求示例**

发表主评论：
```bash
curl -X POST "http://localhost:9011/api/v1/newsletters/e8ffb4ac-e3ea-4e3a-835a-e6ec6ff6cf30/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这篇文章写得很好，对AI的发展趋势分析很到位。",
    "parentId": null
  }'
```

回复评论：
```bash
curl -X POST "http://localhost:9011/api/v1/newsletters/e8ffb4ac-e3ea-4e3a-835a-e6ec6ff6cf30/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "同意你的观点，确实很有见地。",
    "parentId": "d2ee4c5e-0765-45b2-8c76-e201f218cb88"
  }'
```

**响应示例**
```json
{
  "success": true,
  "data": {
    "id": "new-comment-id-123",
    "content": "这篇文章写得很好，对AI的发展趋势分析很到位。",
    "userId": "cmdu8uetk007dvjcsfjnqg2wd",
    "parentId": null,
    "likeCount": 0,
    "replyCount": 0,
    "status": "PUBLISHED",
    "createdAt": "2025-08-13T09:00:00Z",
    "updatedAt": "2025-08-13T09:00:00Z",
    "author": {
      "id": "cmdu8uetk007dvjcsfjnqg2wd",
      "name": "张三",
      "email": "user1@test.com",
      "avatar": "https://example.com/avatar1.jpg"
    },
    "replies": []
  },
  "message": "评论发表成功",
  "error": null
}
```

**错误响应**

空内容错误：
```json
{
  "success": false,
  "error": "评论内容不能为空"
}
```

内容过长错误：
```json
{
  "success": false,
  "error": "评论内容不能超过1000字"
}
```

文章不存在：
```json
{
  "detail": "Newsletter not found"
}
```

---

### 4. 评论点赞/取消点赞

对评论进行点赞或取消点赞操作。

**接口地址**
```
POST /api/v1/newsletters/comments/{comment_id}/like
```

**请求参数**

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|-------|------|------|------|------|
| comment_id | path | string | 是 | 评论ID |
| action | body | string | 是 | 操作类型: "like" 或 "unlike" |
| userId | body | string | 否 | 用户ID（可选，默认使用测试用户） |

**请求示例**
```bash
curl -X POST "http://localhost:9011/api/v1/newsletters/comments/d2ee4c5e-0765-45b2-8c76-e201f218cb88/like" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "like"
  }'
```

**响应示例**
```json
{
  "success": true,
  "commentId": "d2ee4c5e-0765-45b2-8c76-e201f218cb88",
  "isLiked": true,
  "likeCount": 6,
  "userId": "cmdu8uetk007dvjcsfjnqg2wd",
  "timestamp": "2025-08-13T09:15:00.000Z"
}
```

---

### 5. 获取评论的回复列表

获取指定评论的所有回复，支持分页。

**接口地址**
```
GET /api/v1/newsletters/comments/{comment_id}/replies
```

**请求参数**

| 参数名 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|------|--------|------|
| comment_id | path | string | 是 | - | 父评论ID |
| page | query | integer | 否 | 1 | 页码 |
| pageSize | query | integer | 否 | 10 | 每页数量（1-50） |

**请求示例**
```bash
curl "http://localhost:9011/api/v1/newsletters/comments/d2ee4c5e-0765-45b2-8c76-e201f218cb88/replies?page=1&pageSize=10"
```

**响应示例**
```json
{
  "success": true,
  "total": 5,
  "page": 1,
  "pageSize": 10,
  "replies": [
    {
      "id": "reply-001",
      "content": "完全同意你的观点！",
      "userId": "user_002",
      "parentId": "d2ee4c5e-0765-45b2-8c76-e201f218cb88",
      "likeCount": 2,
      "status": "PUBLISHED",
      "createdAt": "2025-08-13T08:30:00Z",
      "author": {
        "id": "user_002",
        "name": "李四",
        "email": "user2@test.com",
        "avatar": "https://example.com/avatar2.jpg"
      }
    }
  ]
}
```

---

## 通用说明

### 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

或

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

### 注意事项

1. **用户认证**：当前使用默认测试用户（张三），userId参数可选。后续集成认证系统时，将从JWT Token中获取用户信息。

2. **点赞逻辑**：点赞接口会自动检测当前状态，如果已点赞则取消，未点赞则添加。action参数暂时保留但不影响逻辑。

3. **评论嵌套**：主评论的`parentId`为`null`，回复评论需要提供父评论的ID。

4. **软删除**：评论删除采用软删除方式，将status改为"DELETED"，不会物理删除数据。

5. **回复限制**：评论列表接口默认返回每条评论的前3条回复，完整回复列表需要调用专门的回复接口。

6. **分页说明**：
   - page从1开始
   - pageSize建议范围：评论列表10-50，回复列表5-20
   - hasNext字段指示是否有下一页

7. **时间格式**：所有时间字段采用ISO 8601格式（UTC时区）

---

## 前端对接建议

### 1. 点赞状态管理

建议前端维护点赞状态的本地缓存，避免频繁请求：

```javascript
// 点赞切换
async function toggleLike(newsletterId) {
  const response = await fetch(`/api/v1/newsletters/${newsletterId}/like`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'like' })
  });
  
  const data = await response.json();
  
  // 更新本地状态
  updateLikeStatus(newsletterId, data.isLiked, data.likeCount);
}
```

### 2. 评论实时更新

发表评论后，建议直接将新评论添加到列表，无需重新请求：

```javascript
// 发表评论
async function postComment(newsletterId, content, parentId = null) {
  const response = await fetch(`/api/v1/newsletters/${newsletterId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, parentId })
  });
  
  const result = await response.json();
  
  if (result.success) {
    // 直接添加到评论列表
    if (parentId) {
      addReplyToComment(parentId, result.data);
    } else {
      prependComment(result.data);
    }
  }
}
```

### 3. 分页加载

使用无限滚动或加载更多按钮：

```javascript
// 加载更多评论
async function loadMoreComments(newsletterId, currentPage) {
  const nextPage = currentPage + 1;
  const response = await fetch(
    `/api/v1/newsletters/${newsletterId}/comments?page=${nextPage}&pageSize=20`
  );
  
  const data = await response.json();
  
  if (data.success) {
    appendComments(data.comments);
    return data.hasNext;
  }
}
```

### 4. 错误处理

统一的错误处理机制：

```javascript
// API请求封装
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error || '请求失败');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API请求失败:', error);
    // 显示错误提示
    showErrorMessage(error.message);
    throw error;
  }
}
```

### 5. 防抖处理

对于点赞等频繁操作，建议添加防抖：

```javascript
// 防抖函数
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 使用防抖的点赞
const debouncedLike = debounce(toggleLike, 300);
```

---

## 测试环境

- **服务器地址**: http://localhost:9011
- **API文档**: http://localhost:9011/docs
- **测试脚本**: `scripts/test_newsletter_apis.py`

## 联系方式

如有问题或需要支持，请联系后端开发团队。