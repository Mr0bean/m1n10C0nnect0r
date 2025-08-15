# 用户阅读行为追踪API文档

## 概述

这套API用于追踪和存储用户的阅读行为数据，支持阅读进度保存、会话管理、滚动行为追踪等功能。所有数据基于现有的PostgreSQL `user_behaviors` 表，通过JSONB字段存储复杂的前端数据结构。

**API基础路径**: `/api/v1/user-behaviors`

---

## 1. 阅读进度管理

### 1.1 保存完整阅读进度

**接口**: `POST /reading-progress/save`

**描述**: 保存用户的完整阅读进度数据，包括整体进度、章节进度、滚动行为等。

**请求体**:

```json
{
  "userId": "user123",
  "documentId": "doc456",
  "sessionId": "session789",
  "overallProgress": {
    "scrollProgress": 45.5,
    "readingProgress": 40.0,
    "totalReadingTime": 180000,
    "activeReadingTime": 150000,
    "estimatedTimeRemaining": 15,
    "totalSections": 10,
    "readSections": 4,
    "completionRate": 0.4,
    "currentBehavior": {
      "isActivelyReading": true,
      "readingMode": "normal",
      "avgReadingSpeed": 250,
      "readingEfficiency": 85
    },
    "lastScrollPosition": 2340,
    "lastUpdateTime": "2024-01-01T10:30:00Z",
    "isCompleted": false
  },
  "sectionProgress": [
    {
      "id": "section-0",
      "title": "引言",
      "level": 1,
      "position": {
        "startOffset": 0,
        "endOffset": 500,
        "elementTop": 0,
        "elementHeight": 120
      },
      "isRead": true,
      "readPercentage": 100,
      "firstReadTime": "2024-01-01T10:00:00Z",
      "lastReadTime": "2024-01-01T10:05:00Z",
      "totalReadTime": 30000,
      "engagementScore": 90,
      "scrollPauses": 2,
      "timeSpent": 35000,
      "interactionCount": 1
    }
  ],
  "scrollBehavior": {
    "timestamp": "2024-01-01T10:30:00Z",
    "scrollTop": 2340,
    "scrollHeight": 5000,
    "clientHeight": 1080,
    "scrollProgress": 46.8,
    "scrollDirection": "down",
    "scrollSpeed": 120,
    "isPaused": true,
    "pauseDuration": 3000,
    "visibleSections": ["section-1", "section-2"],
    "focusedSection": "section-2"
  },
  "insights": {
    "dominantReadingMode": "normal",
    "readingModeDistribution": {
      "careful": 0.3,
      "normal": 0.5,
      "scanning": 0.15,
      "rapid": 0.05
    },
    "personalizedTips": [
      "您的阅读速度适中，可以尝试提高滚动速度",
      "建议在重要章节增加停留时间"
    ],
    "recommendedReadingTime": 25,
    "difficultyAssessment": "medium",
    "avgCompletionTime": 30,
    "userRank": 65
  },
  "saveType": "auto",
  "timestamp": "2024-01-01T10:30:00Z",
  "clientVersion": "1.0.0"
}
```

**响应**:

```json
{
  "success": true,
  "message": "阅读进度保存成功",
  "saved_components": [
    {
      "type": "overall_progress",
      "result": {
        "success": true,
        "behavior_id": "uuid-1",
        "created_at": "2024-01-01T10:30:00Z"
      }
    },
    {
      "type": "section_progress",
      "count": 1,
      "results": [...]
    }
  ],
  "errors": []
}
```

### 1.2 加载阅读进度

**接口**: `GET /reading-progress/load/{user_id}/{document_id}`

**描述**: 加载指定用户和文档的阅读进度数据。

**响应**:

```json
{
  "success": true,
  "data": {
    "overall_progress": {
      "scrollProgress": 45.5,
      "readingProgress": 40.0,
      "totalReadingTime": 180000,
      "isCompleted": false
    },
    "section_progress": [
      {
        "id": "section-0",
        "title": "引言",
        "isRead": true,
        "readPercentage": 100
      }
    ],
    "last_session": {
      "id": "session789",
      "sessionStart": "2024-01-01T10:00:00Z",
      "device": {
        "isMobile": false,
        "viewport": {"width": 1920, "height": 1080}
      }
    },
    "reading_history": {
      "total_sessions": 5,
      "total_reading_time": 900000,
      "average_session_time": 180000,
      "last_read_time": "2024-01-01T10:30:00Z"
    },
    "insights": {
      "dominantReadingMode": "normal",
      "personalizedTips": ["..."]
    },
    "should_resume": true,
    "resume_position": 2340
  }
}
```

---

## 2. 阅读会话管理

### 2.1 统一会话管理

**接口**: `POST /reading-session`

**描述**: 统一的阅读会话管理接口，支持开始、结束、更新会话。

**请求体**:

```json
{
  "user_id": "user123",
  "document_id": "doc456",
  "action": "start", // "start" | "end" | "update"
  "session_data": {
    "id": "session789",
    "sessionStart": "2024-01-01T10:00:00Z",
    "sessionEnd": "2024-01-01T11:00:00Z", // 仅action为"end"时需要
    "isActive": true,
    "device": {
      "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
      "viewport": {
        "width": 1920,
        "height": 1080
      },
      "isMobile": false
    },
    // action为"end"时的额外字段
    "totalTime": 3600000,     // 总时长（毫秒）
    "isCompleted": true,      // 是否完成阅读
    "exitReason": "finished"  // 退出原因: "finished" | "closed" | "switched"
  }
}
```

**响应**:

```json
{
  "success": true,
  "action": "start",
  "session_id": "session789",
  "message": "阅读会话已开始",
  "behavior_id": "uuid-123",
  "created_at": "2024-01-01T10:00:00Z"
}
```

### 2.2 获取活跃会话

**接口**: `GET /reading-session/active/{user_id}`

**描述**: 获取用户当前活跃的阅读会话列表。

**响应**:

```json
{
  "user_id": "user123",
  "active_sessions": [
    {
      "id": "session789",
      "documentId": "doc456",
      "sessionStart": "2024-01-01T10:00:00Z",
      "device": {
        "isMobile": false,
        "viewport": {"width": 1920, "height": 1080}
      },
      "behavior_id": "uuid-123",
      "started_at": "2024-01-01T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 2.3 清理过期会话

**接口**: `POST /reading-session/cleanup/{user_id}?max_session_duration_hours=24`

**描述**: 自动清理用户的过期会话（超过指定时间未结束的会话）。

**响应**:

```json
{
  "user_id": "user123",
  "cleaned_sessions": 2,
  "remaining_active": 1,
  "max_duration_hours": 24
}
```

---

## 3. 阅读分析与统计

### 3.1 用户阅读分析

**接口**: `GET /reading-analytics/user/{user_id}?days=30`

**描述**: 获取用户的阅读分析数据，包括阅读习惯、设备使用情况等。

**响应**:

```json
{
  "user_id": "user123",
  "period": {
    "start": "2023-12-01T00:00:00Z",
    "end": "2024-01-01T00:00:00Z",
    "days": 30
  },
  "statistics": {
    "total_sessions": 25,
    "total_documents_read": 15,
    "avg_sessions_per_day": 0.83,
    "device_distribution": {
      "desktop": 18,
      "mobile": 7
    },
    "reading_mode_distribution": {
      "normal": 15,
      "careful": 8,
      "scanning": 2
    }
  },
  "raw_data_count": 125
}
```

---

## 4. 通用行为追踪

### 4.1 记录单个行为

**接口**: `POST /record`

**描述**: 记录单个用户行为，支持所有类型的行为追踪。

**请求体**:

```json
{
  "behavior_type": "newsletter_view", // 行为类型
  "user_id": "user123",              // 用户ID（可选）
  "session_id": "session789",        // 会话ID（可选）
  "target_type": "newsletter",       // 目标类型
  "target_id": "newsletter456",      // 目标ID
  "action_details": {                // 行为详细信息
    "view_duration": 30000,
    "scroll_depth": 80
  },
  "metadata": {                      // 额外元数据
    "source": "search_result",
    "position": 3
  }
}
```

### 4.2 批量记录行为

**接口**: `POST /batch-record`

**描述**: 批量记录多个用户行为，提高性能。

**请求体**:

```json
[
  {
    "behavior_type": "scroll_behavior_track",
    "user_id": "user123",
    "session_id": "session789",
    "target_type": "document",
    "target_id": "doc456",
    "action_details": {
      "scrollTop": 1200,
      "scrollProgress": 24.0,
      "scrollDirection": "down"
    }
  },
  {
    "behavior_type": "section_progress_update",
    "user_id": "user123",
    "session_id": "session789", 
    "target_type": "section",
    "target_id": "section-2",
    "action_details": {
      "readPercentage": 75,
      "timeSpent": 45000
    }
  }
]
```

### 4.3 查询行为记录

**接口**: `GET /query`

**参数**:
- `user_id`: 用户ID
- `session_id`: 会话ID
- `behavior_type`: 行为类型
- `target_type`: 目标类型
- `target_id`: 目标ID
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `page`: 页码
- `size`: 每页数量

---

## 5. 数据类型定义

### 5.1 ReadingMode 阅读模式

- `careful`: 仔细阅读
- `normal`: 正常阅读
- `scanning`: 浏览模式
- `rapid`: 快速滚动

### 5.2 ExitReason 退出原因

- `finished`: 正常完成阅读
- `closed`: 用户主动关闭
- `switched`: 切换到其他文档
- `timeout_cleanup`: 系统自动清理

### 5.3 SaveType 保存类型

- `auto`: 自动保存
- `manual`: 手动保存
- `exit`: 退出时保存

### 5.4 DifficultyAssessment 难度评估

- `easy`: 简单
- `medium`: 中等
- `hard`: 困难

---

## 6. 前端集成示例

### 6.1 初始化阅读会话

```javascript
class ReadingTracker {
  constructor(userId, documentId) {
    this.userId = userId;
    this.documentId = documentId;
    this.sessionId = this.generateSessionId();
    this.isActive = false;
  }

  // 开始阅读会话
  async startSession() {
    const response = await fetch('/api/v1/user-behaviors/reading-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: this.userId,
        document_id: this.documentId,
        action: 'start',
        session_data: {
          id: this.sessionId,
          sessionStart: new Date().toISOString(),
          isActive: true,
          device: this.getDeviceInfo()
        }
      })
    });
    
    const result = await response.json();
    this.isActive = result.success;
    return result;
  }

  // 结束阅读会话
  async endSession(isCompleted = false, exitReason = 'closed') {
    if (!this.isActive) return;
    
    const response = await fetch('/api/v1/user-behaviors/reading-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: this.userId,
        document_id: this.documentId,
        action: 'end',
        session_data: {
          id: this.sessionId,
          sessionEnd: new Date().toISOString(),
          isActive: false,
          totalTime: this.getTotalTime(),
          isCompleted,
          exitReason
        }
      })
    });
    
    this.isActive = false;
    return await response.json();
  }

  // 获取设备信息
  getDeviceInfo() {
    return {
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      isMobile: /Mobi|Android/i.test(navigator.userAgent)
    };
  }

  // 生成会话ID
  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
}
```

### 6.2 保存阅读进度

```javascript
class ProgressManager {
  constructor(tracker) {
    this.tracker = tracker;
    this.lastSaveTime = Date.now();
    this.autoSaveInterval = 30000; // 30秒自动保存
  }

  // 自动保存进度
  startAutoSave() {
    setInterval(() => {
      if (this.tracker.isActive) {
        this.saveProgress('auto');
      }
    }, this.autoSaveInterval);
  }

  // 保存进度
  async saveProgress(saveType = 'manual') {
    const progressData = {
      userId: this.tracker.userId,
      documentId: this.tracker.documentId,
      sessionId: this.tracker.sessionId,
      overallProgress: this.getOverallProgress(),
      sectionProgress: this.getSectionProgress(),
      scrollBehavior: this.getScrollBehavior(),
      saveType,
      timestamp: new Date().toISOString(),
      clientVersion: '1.0.0'
    };

    const response = await fetch('/api/v1/user-behaviors/reading-progress/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(progressData)
    });

    return await response.json();
  }

  // 加载进度
  async loadProgress() {
    const response = await fetch(
      `/api/v1/user-behaviors/reading-progress/load/${this.tracker.userId}/${this.tracker.documentId}`
    );
    return await response.json();
  }

  // 获取整体进度
  getOverallProgress() {
    return {
      scrollProgress: this.getScrollProgress(),
      readingProgress: this.getReadingProgress(),
      totalReadingTime: this.tracker.getTotalTime(),
      activeReadingTime: this.getActiveReadingTime(),
      estimatedTimeRemaining: this.getEstimatedTimeRemaining(),
      totalSections: this.getTotalSections(),
      readSections: this.getReadSections(),
      completionRate: this.getCompletionRate(),
      currentBehavior: {
        isActivelyReading: this.isActivelyReading(),
        readingMode: this.getReadingMode(),
        avgReadingSpeed: this.getAvgReadingSpeed(),
        readingEfficiency: this.getReadingEfficiency()
      },
      lastScrollPosition: window.pageYOffset,
      lastUpdateTime: new Date().toISOString(),
      isCompleted: this.isCompleted()
    };
  }

  // 获取章节进度
  getSectionProgress() {
    return this.getAllSections().map(section => ({
      id: section.id,
      title: section.title,
      level: section.level,
      position: section.position,
      isRead: section.isRead,
      readPercentage: section.readPercentage,
      firstReadTime: section.firstReadTime,
      lastReadTime: section.lastReadTime,
      totalReadTime: section.totalReadTime,
      engagementScore: section.engagementScore,
      scrollPauses: section.scrollPauses,
      timeSpent: section.timeSpent,
      interactionCount: section.interactionCount
    }));
  }

  // 获取滚动行为
  getScrollBehavior() {
    return {
      timestamp: new Date().toISOString(),
      scrollTop: window.pageYOffset,
      scrollHeight: document.documentElement.scrollHeight,
      clientHeight: window.innerHeight,
      scrollProgress: this.getScrollProgress(),
      scrollDirection: this.getScrollDirection(),
      scrollSpeed: this.getScrollSpeed(),
      isPaused: this.isScrollPaused(),
      pauseDuration: this.getPauseDuration(),
      visibleSections: this.getVisibleSections(),
      focusedSection: this.getFocusedSection()
    };
  }
}
```

### 6.3 滚动行为追踪

```javascript
class ScrollTracker {
  constructor(progressManager) {
    this.progressManager = progressManager;
    this.lastScrollTop = 0;
    this.lastScrollTime = Date.now();
    this.scrollDirection = 'none';
    this.scrollSpeed = 0;
    this.pauseStart = null;
    this.isScrolling = false;
    
    this.initScrollTracking();
  }

  initScrollTracking() {
    let scrollTimer;
    
    window.addEventListener('scroll', () => {
      const currentScrollTop = window.pageYOffset;
      const currentTime = Date.now();
      
      // 计算滚动方向和速度
      this.updateScrollMetrics(currentScrollTop, currentTime);
      
      // 标记正在滚动
      this.isScrolling = true;
      if (this.pauseStart) {
        this.pauseStart = null;
      }
      
      // 清除之前的定时器
      clearTimeout(scrollTimer);
      
      // 设置停止滚动检测
      scrollTimer = setTimeout(() => {
        this.isScrolling = false;
        this.pauseStart = Date.now();
        this.scrollDirection = 'none';
        this.scrollSpeed = 0;
      }, 150);
      
      // 记录滚动行为（节流）
      this.throttledTrackScroll();
    });
  }

  updateScrollMetrics(currentScrollTop, currentTime) {
    const scrollDelta = currentScrollTop - this.lastScrollTop;
    const timeDelta = currentTime - this.lastScrollTime;
    
    // 计算滚动方向
    if (scrollDelta > 0) {
      this.scrollDirection = 'down';
    } else if (scrollDelta < 0) {
      this.scrollDirection = 'up';
    }
    
    // 计算滚动速度（像素/秒）
    if (timeDelta > 0) {
      this.scrollSpeed = Math.abs(scrollDelta) / (timeDelta / 1000);
    }
    
    this.lastScrollTop = currentScrollTop;
    this.lastScrollTime = currentTime;
  }

  throttledTrackScroll = this.throttle(() => {
    if (this.progressManager.tracker.isActive) {
      this.trackScrollBehavior();
    }
  }, 1000);

  async trackScrollBehavior() {
    const scrollData = this.progressManager.getScrollBehavior();
    
    await fetch('/api/v1/user-behaviors/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        behavior_type: 'scroll_behavior_track',
        user_id: this.progressManager.tracker.userId,
        session_id: this.progressManager.tracker.sessionId,
        target_type: 'document',
        target_id: this.progressManager.tracker.documentId,
        action_details: scrollData
      })
    });
  }

  throttle(func, delay) {
    let timeoutId;
    let lastExecTime = 0;
    return function (...args) {
      const currentTime = Date.now();
      
      if (currentTime - lastExecTime > delay) {
        func.apply(this, args);
        lastExecTime = currentTime;
      } else {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
          func.apply(this, args);
          lastExecTime = Date.now();
        }, delay - (currentTime - lastExecTime));
      }
    };
  }
}
```

### 6.4 页面卸载时保存

```javascript
// 页面卸载时保存进度
window.addEventListener('beforeunload', async (event) => {
  if (readingTracker.isActive) {
    // 保存最终进度
    await progressManager.saveProgress('exit');
    
    // 结束会话
    await readingTracker.endSession(
      progressManager.isCompleted(),
      'closed'
    );
  }
});

// 页面可见性变化时的处理
document.addEventListener('visibilitychange', async () => {
  if (document.hidden) {
    // 页面隐藏时保存进度
    if (readingTracker.isActive) {
      await progressManager.saveProgress('auto');
    }
  } else {
    // 页面显示时恢复
    if (readingTracker.isActive) {
      // 可以在这里加载最新进度
    }
  }
});
```

---

## 7. 错误处理

所有API在出错时返回统一的错误格式：

```json
{
  "detail": "错误描述信息"
}
```

常见的HTTP状态码：

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 8. 注意事项

1. **数据隐私**: 确保用户同意收集阅读行为数据
2. **性能优化**: 使用节流和防抖来控制API调用频率
3. **离线支持**: 考虑在网络不可用时缓存数据
4. **数据清理**: 定期清理过期的行为数据
5. **GDPR合规**: 提供数据删除和导出功能

---

**版本**: v1.0.0  
**最后更新**: 2024-01-01
