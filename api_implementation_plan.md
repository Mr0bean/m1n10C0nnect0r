# API实现计划

## 📊 数据库分析结果

### 现有相关表
经过数据库检查，发现已有以下相关表可以直接使用：

1. **users表** - 用户信息表 ✅
2. **likes表** - 点赞记录表（可用于文章和评论点赞）✅
3. **comments表** - 评论表 ✅
4. **newsletters表** - 文章/资讯表 ✅
5. **sessions表** - 会话管理表 ✅
6. **memberships表** - 会员信息表 ✅

### 表结构映射

#### 1. 用户认证
- **users表**：包含用户基本信息
- **sessions表**：用于会话管理
- **memberships表**：用于会员状态管理

#### 2. 文章点赞
- **likes表**：通用点赞表，可通过targetType区分文章/评论点赞
- **newsletters表**：包含likeCount字段用于计数

#### 3. 评论系统
- **comments表**：评论数据
- **newsletters表**：包含commentCount字段
- **likes表**：用于评论点赞

## 🎯 实现计划

### 第一阶段：用户认证系统（优先级：高）

#### 1.1 获取用户信息接口
```
GET /api/v1/users/profile
```

**实现路径调整**：
- 原文档路径：`/api/v1/auth/profile`
- 调整为：`/api/v1/users/profile`（更符合RESTful规范）

**实现要点**：
- 使用JWT进行认证
- 从users表获取基本信息
- 从memberships表获取会员状态
- 返回用户完整信息

### 第二阶段：文章交互功能

#### 2.1 文章点赞/取消点赞
```
POST /api/v1/newsletters/{newsletter_id}/like
```

**实现路径调整**：
- 原文档：`/api/v1/articles/{article_id}/like`
- 调整为：`/api/v1/newsletters/{newsletter_id}/like`（使用实际表名）

**实现要点**：
- 在likes表中记录点赞状态
- 更新newsletters表的likeCount
- 支持点赞/取消点赞切换

### 第三阶段：评论系统

#### 3.1 获取评论列表
```
GET /api/v1/newsletters/{newsletter_id}/comments
```

**实现要点**：
- 从comments表获取评论
- 支持分页和排序
- 包含用户信息关联
- 支持嵌套回复结构

#### 3.2 发表评论
```
POST /api/v1/newsletters/{newsletter_id}/comments
```

**实现要点**：
- 在comments表创建评论
- 更新newsletters表的commentCount
- 支持回复功能（parentId）
- 内容安全过滤

#### 3.3 评论点赞
```
POST /api/v1/comments/{comment_id}/like
```

**实现要点**：
- 复用likes表，通过targetType='comment'区分
- 更新评论的点赞计数
- 防止重复点赞

## 📁 文件结构规划

```
minio-file-manager/backend/app/
├── api/
│   └── endpoints/
│       ├── users.py          # 用户相关接口（新建）
│       ├── newsletters.py    # 文章相关接口（新建）
│       └── comments.py       # 评论相关接口（新建）
├── services/
│   ├── auth_service.py       # 认证服务（新建）
│   ├── user_service.py       # 用户服务（新建）
│   ├── like_service.py       # 点赞服务（新建）
│   └── comment_service.py    # 评论服务（新建）
├── models/
│   ├── user.py              # 用户模型（新建）
│   ├── newsletter.py        # 文章模型（新建）
│   └── comment.py           # 评论模型（新建）
└── core/
    └── auth.py              # JWT认证中间件（新建）
```

## 🔧 技术实现细节

### JWT认证实现
```python
# 使用python-jose库
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 数据库连接
```python
# 使用现有的PostgreSQL配置
import asyncpg
from app.core.config import get_settings

settings = get_settings()

async def get_db_pool():
    return await asyncpg.create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_database,
        min_size=10,
        max_size=20
    )
```

## 📋 实施步骤

### Day 1: 基础架构搭建
- [ ] 创建JWT认证中间件
- [ ] 创建基础模型类
- [ ] 设置路由结构

### Day 2: 用户认证实现
- [ ] 实现用户信息获取接口
- [ ] 集成会员状态查询
- [ ] 添加认证装饰器

### Day 3: 文章交互功能
- [ ] 实现文章点赞接口
- [ ] 处理点赞计数更新
- [ ] 添加防重复点赞逻辑

### Day 4-5: 评论系统
- [ ] 实现评论列表接口
- [ ] 实现发表评论接口
- [ ] 实现评论点赞接口
- [ ] 添加内容过滤

### Day 6: 测试与优化
- [ ] 编写单元测试
- [ ] 性能优化
- [ ] 文档更新

## 🚀 立即开始实现

基于现有数据库表结构，我们可以立即开始实现这些接口，无需创建新表。主要工作是：

1. **利用现有表**：直接使用users、likes、comments、newsletters等表
2. **最小改动**：不修改表结构，通过代码逻辑适配
3. **快速迭代**：先实现基础功能，后续优化

## 注意事项

1. **数据库连接**：使用生产环境配置
   - Host: 60.205.160.74
   - Database: thinkinai
   - User: postgres

2. **表名映射**：
   - articles → newsletters
   - article_id → newsletter_id
   - 使用实际的数据库表名

3. **字段适配**：
   - 某些字段可能需要映射或计算
   - 利用JSONB字段存储扩展信息

准备好开始实现了！