# Tags聚合API文档

## 概述

Tags聚合API提供了对Newsletter文章中所有tags进行统计分析的功能，支持按数量倒序排序，可用于生成标签云、分析热门话题趋势等。

## API端点

### GET /api/v1/newsletter/search/tags/aggregate

获取所有Newsletter文章的tags聚合统计信息。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| size | int | 否 | 50 | 返回的tag数量上限 (1-200) |
| min_doc_count | int | 否 | 1 | 最小文档数量阈值 |

#### 请求示例

```bash
# 基本聚合
curl "http://localhost:9011/api/v1/newsletter/search/tags/aggregate"

# 限制返回前10个tags
curl "http://localhost:9011/api/v1/newsletter/search/tags/aggregate?size=10"

# 只返回至少出现2次的tags
curl "http://localhost:9011/api/v1/newsletter/search/tags/aggregate?min_doc_count=2"

# 组合参数
curl "http://localhost:9011/api/v1/newsletter/search/tags/aggregate?size=20&min_doc_count=3"
```

#### 响应格式

```json
{
  "success": true,
  "total_tags": 25,
  "tags": [
    {
      "tag": "AI",
      "count": 45
    },
    {
      "tag": "机器学习",
      "count": 32
    },
    {
      "tag": "GPT",
      "count": 28
    },
    {
      "tag": "深度学习",
      "count": 22
    }
  ],
  "total_documents": 150
}
```

#### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| total_tags | int | 返回的tags总数 |
| tags | array | tags列表，按数量倒序排列 |
| tags[].tag | string | tag名称 |
| tags[].count | int | 该tag出现的文章数量 |
| total_documents | int | 索引中的总文档数量 |

#### 错误响应

```json
{
  "detail": "Tags聚合失败: 具体错误信息"
}
```

## 使用场景

### 1. 生成标签云

```javascript
// 前端示例：生成标签云
async function generateTagCloud() {
  const response = await fetch('/api/v1/newsletter/search/tags/aggregate?size=30');
  const data = await response.json();
  
  if (data.success) {
    const maxCount = Math.max(...data.tags.map(t => t.count));
    
    data.tags.forEach(tagInfo => {
      const fontSize = 12 + (tagInfo.count / maxCount) * 20; // 根据数量计算字体大小
      console.log(`${tagInfo.tag}: ${fontSize}px, ${tagInfo.count}篇文章`);
    });
  }
}
```

### 2. 热门话题分析

```python
# Python示例：分析热门话题
import requests

def analyze_hot_topics():
    response = requests.get('http://localhost:9011/api/v1/newsletter/search/tags/aggregate?size=20&min_doc_count=5')
    data = response.json()
    
    if data['success']:
        print("🔥 热门话题排行榜:")
        for i, tag_info in enumerate(data['tags'], 1):
            print(f"{i:2d}. {tag_info['tag']} - {tag_info['count']} 篇文章")
```

### 3. 内容分类统计

```bash
# 获取所有tags的完整统计
curl "http://localhost:9011/api/v1/newsletter/search/tags/aggregate?size=200" | jq '.tags[] | "\(.tag): \(.count)"'
```

## 性能优化建议

1. **合理设置size参数**: 避免一次性返回过多tags，建议不超过100
2. **使用min_doc_count过滤**: 过滤掉低频tags，提高结果质量
3. **缓存结果**: 对于不经常变化的统计结果，可以在前端缓存

## 测试

运行测试脚本验证API功能：

```bash
cd minio-file-manager/backend
python test_tags_aggregation.py
```

## 注意事项

1. 该API依赖于Elasticsearch中的`tags`字段，确保文档索引时正确设置了tags
2. tags字段在ES映射中定义为`keyword`类型，支持精确聚合
3. 聚合结果按文档数量倒序排列，数量相同的tags按字母顺序排列
4. 如果索引中没有tags数据，将返回空列表
