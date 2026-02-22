# 公益网球场订场系统 - API接口文档

> **版本**：v1.0  
> **更新时间**：2026-02-22  
> **适用于**：前端集成开发

---

## 📋 接口概览

| 接口名称 | 请求方法 | 接口地址 | 功能描述 |
|---------|---------|---------|----------|
| [获取公益场次列表](#1-获取公益场次列表) | GET | `/api/free-courts/list` | 查询可抢的公益场次 |
| [抢占公益场次](#2-抢占公益场次) | POST | `/api/free-courts/book` | 用户抢场操作 |
| [我的订场记录](#3-我的订场记录) | GET | `/api/free-courts/my-bookings` | 查询用户订场历史 |
| [查询配额信息](#4-查询配额信息) | GET | `/api/quota/info` | 查询用户配额状态 |
| [分享奖励配额](#5-分享奖励配额) | POST | `/api/quota/bonus` | 分享拉新获得配额 |

---

## 🌐 1. 获取公益场次列表

### 接口信息
- **URL**：`/api/free-courts/list`
- **方法**：`GET`
- **描述**：获取可抢的公益网球场场次列表，支持城市和区域筛选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|-------|------|------|------|------|
| date | String | 否 | 筛选日期，格式 YYYY-MM-DD | `2026-02-23` |
| city | String | 否 | 筛选城市 | `深圳` |
| district | String | 否 | 筛选区域 | `南山区` |
| page | Integer | 否 | 页码，默认1 | `1` |
| pageSize | Integer | 否 | 每页数量，默认20，最大100 | `20` |

### 请求示例
```
GET /api/free-courts/list?city=深圳&district=南山区&page=1&pageSize=20
```

### 响应参数

#### 成功响应 (200)
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "slots": [
      {
        "slotId": "slot_20260223_1",
        "venueId": "venue_001",
        "courtId": "court_001",
        "courtName": "深圳湾体育中心1号场",
        "venueName": "深圳湾体育中心",
        "location": "深圳市南山区滨海大道",
        "city": "深圳",
        "district": "南山区",
        "date": "2026-02-23",
        "timeSlot": "09:00-11:00",
        "totalQuota": 2,
        "bookedQuota": 0,
        "status": 1,
        "openTime": 1761015600,
        "endTime": 1761022800
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 10
  }
}
```

#### 字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| slotId | String | 场次唯一ID |
| venueId | String | 场地ID |
| courtId | String | 球场ID |
| courtName | String | 球场名称（展示用） |
| venueName | String | 场地名称 |
| location | String | 详细地址 |
| city | String | 城市 |
| district | String | 区域 |
| date | String | 日期 YYYY-MM-DD |
| timeSlot | String | 时间段，如"09:00-11:00" |
| totalQuota | Integer | 总名额数 |
| bookedQuota | Integer | 已抢名额数 |
| status | Integer | 状态：0=未开始，1=可抢，2=已抢完，3=已结束 |
| openTime | Integer | 开抢时间 Unix时间戳 |
| endTime | Integer | 抢场截止时间 Unix时间戳 |

---

## 🏃 2. 抢占公益场次

### 接口信息
- **URL**：`/api/free-courts/book`
- **方法**：`POST`
- **描述**：用户抢占公益场次，消耗配额且不可取消

### 请求参数

#### 请求体 (JSON)
```json
{
  "slotId": "slot_20260223_1",
  "userId": "user_123"
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| slotId | String | 是 | 场次ID |
| userId | String | 是 | 用户ID |

### 响应参数

#### 成功响应 (200)
```json
{
  "code": 200,
  "message": "抢场成功",
  "data": {
    "bookingId": "FREE-slot_20260223_1-user_123-a1b2c3d4",
    "slotId": "slot_20260223_1",
    "quotaCost": 1
  }
}
```

#### 错误响应示例

**配额不足**
```json
{
  "code": 400,
  "message": "本月公益抢场配额已用完"
}
```

**名额已满**
```json
{
  "code": 400,
  "message": "本次公益场名额已抢完"
}
```

**时间不符**
```json
{
  "code": 400,
  "message": "未到开抢时间"
}
```

**重复抢场**
```json
{
  "code": 400,
  "message": "您已经抢过此场次"
}
```

---

## 📝 3. 我的订场记录

### 接口信息
- **URL**：`/api/free-courts/my-bookings`
- **方法**：`GET`
- **描述**：获取用户的公益订场记录

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|-------|------|------|------|------|
| userId | String | 是 | 用户ID | `user_123` |
| page | Integer | 否 | 页码，默认1 | `1` |
| pageSize | Integer | 否 | 每页数量，默认20 | `20` |

### 请求示例
```
GET /api/free-courts/my-bookings?userId=user_123&page=1&pageSize=20
```

### 响应参数

#### 成功响应 (200)
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "bookings": [
      {
        "bookingId": "FREE-slot_20260223_1-user_123-a1b2c3d4",
        "slotId": "slot_20260223_1",
        "date": "2026-02-23",
        "timeSlot": "09:00-11:00",
        "courtName": "深圳湾体育中心1号场",
        "venueName": "深圳湾体育中心",
        "location": "深圳市南山区滨海大道",
        "quotaCost": 1,
        "status": "confirmed",
        "createTime": 1708583406
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 3
  }
}
```

#### 字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| bookingId | String | 订场记录ID |
| slotId | String | 场次ID |
| date | String | 日期 |
| timeSlot | String | 时间段 |
| courtName | String | 球场名称 |
| venueName | String | 场地名称 |
| location | String | 地址 |
| quotaCost | Integer | 消耗配额数量 |
| status | String | 状态，公益场固定为"confirmed" |
| createTime | Integer | 抢场时间 Unix时间戳 |

---

## 🎯 4. 查询配额信息

### 接口信息
- **URL**：`/api/quota/info`
- **方法**：`GET`
- **描述**：查询用户当前月份的配额使用情况

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|-------|------|------|------|------|
| userId | String | 是 | 用户ID | `user_123` |

### 请求示例
```
GET /api/quota/info?userId=user_123
```

### 响应参数

#### 成功响应 (200)
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "total_quota": 5,
    "used_quota": 1,
    "available_quota": 4,
    "bonus_quota": 0,
    "current_month": "2026-02",
    "last_reset_time": 1708583406
  }
}
```

#### 字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| total_quota | Integer | 当月总配额（基础5次+分享奖励） |
| used_quota | Integer | 已使用配额 |
| available_quota | Integer | 剩余可用配额 |
| bonus_quota | Integer | 分享奖励配额（累积到下月） |
| current_month | String | 当前月份 YYYY-MM |
| last_reset_time | Integer | 上次重置时间 Unix时间戳 |

---

## 🎁 5. 分享奖励配额

### 接口信息
- **URL**：`/api/quota/bonus`
- **方法**：`POST`
- **描述**：用户通过分享拉新获得额外配额

### 请求参数

#### 请求体 (JSON)
```json
{
  "userId": "user_123",
  "shareId": "share_20260222_001",
  "amount": 1
}
```

| 字段名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| userId | String | 是 | 用户ID |
| shareId | String | 否 | 分享记录ID |
| amount | Integer | 否 | 奖励配额数量，默认1 |

### 响应参数

#### 成功响应 (200)
```json
{
  "code": 200,
  "message": "奖励配额添加成功",
  "data": {
    "added_quota": 1,
    "total_quota": 6,
    "available_quota": 5
  }
}
```

---

## 🚨 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查参数格式和必填项 |
| 404 | 资源不存在 | 检查场次ID或用户ID是否正确 |
| 405 | 请求方法不允许 | 检查HTTP方法 |
| 500 | 服务器内部错误 | 联系后端开发者 |

## 📱 前端集成建议

### 1. 页面加载时序
```javascript
// 1. 加载场次列表和配额信息
async function loadPage() {
  const [slotsRes, quotaRes] = await Promise.all([
    fetch('/api/free-courts/list?city=深圳'),
    fetch('/api/quota/info?userId=' + userId)
  ]);
  
  // 处理响应数据
}
```

### 2. 抢场流程
```javascript
// 2. 用户抢场确认
async function bookCourt(slotId) {
  // 显示确认对话框
  const confirmed = await showConfirm('确认抢场？配额将扣减且不可取消');
  
  if (confirmed) {
    const res = await fetch('/api/free-courts/book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slotId, userId })
    });
    
    // 刷新页面数据
    await loadPage();
  }
}
```

### 3. 状态判断逻辑
```javascript
// 3. 根据场次状态显示按钮
function getSlotStatus(slot) {
  const now = Date.now() / 1000;
  
  if (now < slot.openTime) return '即将开抢';
  if (now > slot.endTime) return '已结束';
  if (slot.bookedQuota >= slot.totalQuota) return '已抢完';
  return '立即抢场';
}
```

---

## 🔧 配额管理机制

### 月度重置规则
- **基础配额**：每月5次
- **重置时间**：每月1号自动重置
- **分享奖励**：累积到下个月
- **计算公式**：新月配额 = 基础配额(5) + 累积分享奖励配额

### 配额消耗规则
- **抢场成功**：消耗1次配额
- **不可恢复**：公益场地不支持取消
- **实时扣减**：抢场成功立即扣减

---

**📞 联系方式**  
如有接口问题，请联系后端开发团队。

**🔄 版本历史**  
- v1.0 (2026-02-22): 初始版本，包含完整的公益订场功能