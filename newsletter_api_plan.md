# Newsletter API 实现计划（精简版）

## 📌 实现范围

去掉用户认证接口后，本次需要实现 **4个核心接口**，专注于文章交互和评论系统。

### 待实现接口清单

| 序号 | 接口功能 | HTTP方法 | 路径 | 优先级 |
|------|---------|----------|------|--------|
| 1 | 文章点赞/取消 | POST | `/api/v1/newsletters/{id}/like` | ⭐⭐⭐ |
| 2 | 获取评论列表 | GET | `/api/v1/newsletters/{id}/comments` | ⭐⭐⭐ |
| 3 | 发表评论 | POST | `/api/v1/newsletters/{id}/comments` | ⭐⭐ |
| 4 | 评论点赞 | POST | `/api/v1/comments/{id}/like` | ⭐⭐ |

## 🗄️ 数据库表使用

### 核心表结构
```sql
-- newsletters表（文章表）- 已存在
newsletters:
  - id (text): 文章ID
  - likeCount (integer): 点赞数
  - commentCount (integer): 评论数
  - 其他字段...

-- likes表（点赞表）- 已存在
likes:
  - id
  - userId
  - targetId (对应文章ID或评论ID)
  - targetType (区分文章/评论)
  - createdAt

-- comments表（评论表）- 已存在  
comments:
  - id
  - userId
  - targetId (文章ID)
  - parentId (父评论ID，用于回复)
  - content
  - likeCount
  - createdAt
  - status
```

## 🚀 实现方案

### 1. 文章点赞接口
**POST `/api/v1/newsletters/{id}/like`**

```python
async def toggle_newsletter_like(newsletter_id: str, user_id: str = None):
    """
    文章点赞/取消点赞
    - 检查是否已点赞
    - 切换点赞状态
    - 更新newsletters.likeCount
    """
    # 使用Mock用户ID（暂时不需要认证）
    if not user_id:
        user_id = "mock_user_001"
    
    # 查询现有点赞记录
    existing_like = await db.fetch_one(
        "SELECT id FROM likes WHERE userId = $1 AND targetId = $2 AND targetType = 'newsletter'",
        user_id, newsletter_id
    )
    
    if existing_like:
        # 取消点赞
        await db.execute("DELETE FROM likes WHERE id = $1", existing_like['id'])
        await db.execute("UPDATE newsletters SET likeCount = likeCount - 1 WHERE id = $1", newsletter_id)
        is_liked = False
    else:
        # 添加点赞
        await db.execute(
            "INSERT INTO likes (userId, targetId, targetType) VALUES ($1, $2, 'newsletter')",
            user_id, newsletter_id
        )
        await db.execute("UPDATE newsletters SET likeCount = likeCount + 1 WHERE id = $1", newsletter_id)
        is_liked = True
    
    # 获取最新点赞数
    result = await db.fetch_one("SELECT likeCount FROM newsletters WHERE id = $1", newsletter_id)
    
    return {
        "newsletterId": newsletter_id,
        "isLiked": is_liked,
        "likeCount": result['likeCount']
    }
```

### 2. 获取评论列表接口
**GET `/api/v1/newsletters/{id}/comments`**

```python
async def get_newsletter_comments(
    newsletter_id: str,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "latest"
):
    """
    获取文章评论列表
    - 支持分页
    - 支持排序（最新/最热）
    - 包含用户信息
    - 支持嵌套回复
    """
    offset = (page - 1) * page_size
    
    # 排序条件
    order_by = "c.createdAt DESC" if sort_by == "latest" else "c.likeCount DESC"
    
    # 查询主评论
    query = f"""
        SELECT 
            c.*,
            u.name as userName,
            u.avatar as userAvatar,
            (SELECT COUNT(*) FROM comments WHERE parentId = c.id) as replyCount
        FROM comments c
        LEFT JOIN users u ON c.userId = u.id
        WHERE c.targetId = $1 AND c.parentId IS NULL
        ORDER BY {order_by}
        LIMIT $2 OFFSET $3
    """
    
    comments = await db.fetch_all(query, newsletter_id, page_size, offset)
    
    # 获取每个评论的回复（限制数量）
    for comment in comments:
        replies = await db.fetch_all("""
            SELECT c.*, u.name as userName, u.avatar as userAvatar
            FROM comments c
            LEFT JOIN users u ON c.userId = u.id
            WHERE c.parentId = $1
            ORDER BY c.createdAt ASC
            LIMIT 3
        """, comment['id'])
        comment['replies'] = replies
    
    # 获取总数
    total = await db.fetch_one(
        "SELECT COUNT(*) as count FROM comments WHERE targetId = $1 AND parentId IS NULL",
        newsletter_id
    )
    
    return {
        "total": total['count'],
        "page": page,
        "pageSize": page_size,
        "comments": comments
    }
```

### 3. 发表评论接口
**POST `/api/v1/newsletters/{id}/comments`**

```python
async def create_comment(
    newsletter_id: str,
    content: str,
    parent_id: str = None,
    user_id: str = None
):
    """
    发表评论或回复
    - 创建评论记录
    - 更新文章评论数
    - 支持回复功能
    """
    # Mock用户ID
    if not user_id:
        user_id = "mock_user_001"
    
    # 生成评论ID
    comment_id = f"comment_{int(time.time() * 1000)}"
    
    # 插入评论
    await db.execute("""
        INSERT INTO comments (id, userId, targetId, parentId, content, likeCount, status)
        VALUES ($1, $2, $3, $4, $5, 0, 'published')
    """, comment_id, user_id, newsletter_id, parent_id, content)
    
    # 更新文章评论数（仅主评论）
    if not parent_id:
        await db.execute(
            "UPDATE newsletters SET commentCount = commentCount + 1 WHERE id = $1",
            newsletter_id
        )
    
    # 返回新评论信息
    comment = await db.fetch_one("""
        SELECT c.*, u.name as userName, u.avatar as userAvatar
        FROM comments c
        LEFT JOIN users u ON c.userId = u.id
        WHERE c.id = $1
    """, comment_id)
    
    return comment
```

### 4. 评论点赞接口
**POST `/api/v1/comments/{id}/like`**

```python
async def toggle_comment_like(comment_id: str, user_id: str = None):
    """
    评论点赞/取消点赞
    - 复用likes表
    - targetType = 'comment'
    """
    if not user_id:
        user_id = "mock_user_001"
    
    # 查询现有点赞
    existing_like = await db.fetch_one(
        "SELECT id FROM likes WHERE userId = $1 AND targetId = $2 AND targetType = 'comment'",
        user_id, comment_id
    )
    
    if existing_like:
        # 取消点赞
        await db.execute("DELETE FROM likes WHERE id = $1", existing_like['id'])
        await db.execute("UPDATE comments SET likeCount = likeCount - 1 WHERE id = $1", comment_id)
        is_liked = False
    else:
        # 添加点赞
        await db.execute(
            "INSERT INTO likes (userId, targetId, targetType) VALUES ($1, $2, 'comment')",
            user_id, comment_id
        )
        await db.execute("UPDATE comments SET likeCount = likeCount + 1 WHERE id = $1", comment_id)
        is_liked = True
    
    # 获取最新点赞数
    result = await db.fetch_one("SELECT likeCount FROM comments WHERE id = $1", comment_id)
    
    return {
        "commentId": comment_id,
        "isLiked": is_liked,
        "likeCount": result['likeCount']
    }
```

## 📁 项目结构

```
minio-file-manager/backend/app/
├── api/endpoints/
│   └── newsletter_interactions.py  # 新建：所有4个接口
├── services/
│   ├── like_service.py            # 点赞服务
│   └── comment_service.py         # 评论服务
└── schemas/
    └── newsletter_schemas.py       # 请求/响应模型
```

## 🎯 实施计划（3天完成）

### Day 1: 点赞功能
- [x] 上午：实现文章点赞接口
- [x] 下午：测试点赞功能，处理边界情况

### Day 2: 评论系统（查询）
- [x] 上午：实现评论列表接口
- [x] 下午：优化查询性能，添加嵌套回复

### Day 3: 评论系统（交互）
- [x] 上午：实现发表评论接口
- [x] 下午：实现评论点赞接口
- [x] 晚上：整体测试和优化

## 🔑 关键技术点

### 1. 临时用户处理
由于暂时不实现用户认证，使用Mock用户ID：
```python
DEFAULT_USER_ID = "mock_user_001"  # 可配置的默认用户
```

### 2. 数据库连接池
```python
# 复用现有配置
from app.services.postgresql_service import postgresql_service

async def get_db():
    return await postgresql_service.get_pool()
```

### 3. 错误处理
```python
from fastapi import HTTPException

# 统一错误响应
def handle_not_found(resource: str):
    raise HTTPException(status_code=404, detail=f"{resource} not found")

def handle_db_error(error: Exception):
    raise HTTPException(status_code=500, detail=str(error))
```

### 4. 响应格式统一
```python
# 成功响应
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}

# 错误响应
{
    "success": false,
    "error": "错误信息",
    "code": 404
}
```

## ✅ 预期成果

完成后将提供：
1. **4个可用的REST API接口**
2. **完整的接口文档**（Swagger）
3. **测试脚本**
4. **与前端对接说明**

## 🚦 立即开始

现在可以开始实现第一个接口：**文章点赞功能**！

无需等待用户认证系统，可以独立完成这4个接口的开发。