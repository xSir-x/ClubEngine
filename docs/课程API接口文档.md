# 课程API接口文档

## 概述

本文档描述了教练课程管理系统的API接口，支持批量发布课程、课程查询、更新、删除和学员报名等功能。

**⚠️ 重要：所有接口都需要传递有效的 access_token 进行身份验证！**

---

## 基础信息

**Base URL**: `http://your-domain.com`

**Content-Type**: `application/json`

**字符编码**: `UTF-8`

**认证方式**: 所有接口都需要 `access_token` 进行身份验证

### Access Token 获取

调用课程接口前，需要先通过登录接口获取 `access_token`：

```bash
POST /userlogin
{
  "js_code": "微信登录返回的code"
}

# 返回
{
  "code": 200,
  "result": {
    "access_token": "oABC123...",
    "openid": "oABC123XYZ789"
  },
  "succeed": true
}
```

### Access Token 传递方式

**POST 请求**：在请求体中传递
```json
{
  "access_token": "your_access_token_here",
  "courseId": "xxx",
  ...
}
```

**GET 请求**：在 URL 参数中传递
```
GET /api/courses/list?access_token=your_access_token_here&coachId=xxx
```

或在 Header 中传递：
```
Authorization: Bearer your_access_token_here
```

---

## 1. 批量发布课程

### 接口说明
教练可以一次性发布多个日期的课程，所有课程使用相同的课程信息，仅日期不同。

### 请求信息

- **URL**: `/api/courses/publish`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **需要认证**: ✅ 是

### 请求参数

```json
{
  "access_token": "oABC123XYZ789timestamp...",
  "coachId": "oABC123XYZ789",
  "coachName": "张教练",
  "courseInfo": {
    "title": "网球正手技术提升训练",
    "description": "本课程专注于提升网球正手技术，包括握拍、挥拍动作、击球点选择等核心要素。适合有一定基础的学员。",
    "coverImage": "https://cdn.example.com/images/forehand.jpeg",
    "level": "intermediate",
    "category": "technique",
    "time": "10:00",
    "duration": 90,
    "location": "深圳湾体育中心1号场",
    "minStudents": 3,
    "maxStudents": 10,
    "originalPrice": 180.00,
    "currentPrice": 150.00
  },
  "dates": [
    "2026-01-10",
    "2026-01-11",
    "2026-01-12"
  ]
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **access_token** | string | **是** | **用户身份令牌（必须）** |
| coachId | string | 是 | 教练ID（微信openid） |
| coachName | string | 是 | 教练姓名 |
| courseInfo | object | 是 | 课程信息对象 |
| dates | array | 是 | 课程日期数组，格式：YYYY-MM-DD |

**courseInfo 对象说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 课程标题 |
| description | string | 是 | 课程描述 |
| coverImage | string | 是 | 封面图片URL |
| level | string | 是 | 课程级别：beginner/intermediate/advanced |
| category | string | 是 | 课程分类：technique/physical/strategy/mental |
| time | string | 是 | 上课时间，格式：HH:MM |
| duration | integer | 是 | 课程时长（分钟） |
| location | string | 是 | 上课地点 |
| minStudents | integer | 是 | 最少学员数 |
| maxStudents | integer | 是 | 最多学员数 |
| originalPrice | decimal | 是 | 原价 |
| currentPrice | decimal | 是 | 现价 |

### 响应示例

**成功响应：**

```json
{
  "code": 200,
  "message": "课程发布成功",
  "data": {
    "success_count": 3,
    "courses": [
      {
        "course_id": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
        "title": "网球正手技术提升训练",
        "date": "2026-01-10",
        "time": "10:00",
        "location": "深圳湾体育中心1号场",
        "price": 150.00
      },
      {
        "course_id": "COURSE-oABC123XYZ789-2026-01-11-e5f6g7h8",
        "title": "网球正手技术提升训练",
        "date": "2026-01-11",
        "time": "10:00",
        "location": "深圳湾体育中心1号场",
        "price": 150.00
      },
      {
        "course_id": "COURSE-oABC123XYZ789-2026-01-12-i9j0k1l2",
        "title": "网球正手技术提升训练",
        "date": "2026-01-12",
        "time": "10:00",
        "location": "深圳湾体育中心1号场",
        "price": 150.00
      }
    ]
  }
}
```

**错误响应：**

```json
{
  "code": 400,
  "message": "课程信息缺少必填字段: title"
}
```

**错误响应（Token无效）：**

```json
{
  "code": 100,
  "message": "Invalidate access token."
}
```

---

## 2. 获取课程列表

### 接口说明
查询课程列表，支持按教练ID、日期、状态筛选和分页。

### 请求信息

- **URL**: `/api/courses/list`
- **Method**: `GET`
- **需要认证**: ✅ 是

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **access_token** | string | **是** | **用户身份令牌（必须）** |
| coachId | string | 否 | 教练ID，筛选特定教练的课程 |
| date | string | 否 | 课程日期，格式：YYYY-MM-DD |
| status | integer | 否 | 课程状态：1-待开课 2-进行中 3-已结束 4-已取消 |
| page | integer | 否 | 页码，默认1 |
| pageSize | integer | 否 | 每页数量，默认20 |

### 请求示例

```
GET /api/courses/list?access_token=xxx&coachId=oABC123XYZ789&date=2026-01-10&status=1&page=1&pageSize=10
```

或使用 Header：
```bash
curl -H "Authorization: Bearer your_access_token" \
  "http://your-domain.com/api/courses/list?coachId=oABC123XYZ789"
```

### 响应示例

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "total": 3,
    "page": 1,
    "pageSize": 10,
    "courses": [
      {
        "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
        "coachId": "oABC123XYZ789",
        "coachName": "张教练",
        "title": "网球正手技术提升训练",
        "description": "本课程专注于提升网球正手技术...",
        "coverImage": "https://cdn.example.com/images/forehand.jpeg",
        "level": "intermediate",
        "category": "technique",
        "date": "2026-01-10",
        "time": "10:00",
        "duration": 90,
        "location": "深圳湾体育中心1号场",
        "minStudents": 3,
        "maxStudents": 10,
        "currentStudents": 5,
        "originalPrice": 180.00,
        "currentPrice": 150.00,
        "status": 1,
        "createTime": "1735977600"
      }
    ]
  }
}
```

---

## 3. 获取课程详情

### 接口说明
获取指定课程的详细信息。

### 请求信息

- **URL**: `/api/courses/detail`
- **Method**: `GET`
- **需要认证**: ✅ 是

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **access_token** | string | **是** | **用户身份令牌（必须）** |
| courseId | string | 是 | 课程ID |

### 请求示例

```
GET /api/courses/detail?access_token=xxx&courseId=COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4
```

### 响应示例

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
    "coachId": "oABC123XYZ789",
    "coachName": "张教练",
    "title": "网球正手技术提升训练",
    "description": "本课程专注于提升网球正手技术...",
    "coverImage": "https://cdn.example.com/images/forehand.jpeg",
    "level": "intermediate",
    "category": "technique",
    "date": "2026-01-10",
    "time": "10:00",
    "duration": 90,
    "location": "深圳湾体育中心1号场",
    "minStudents": 3,
    "maxStudents": 10,
    "currentStudents": 5,
    "originalPrice": 180.00,
    "currentPrice": 150.00,
    "status": 1,
    "createTime": "1735977600",
    "updateTime": null
  }
}
```

---

## 4. 更新课程信息

### 接口说明
更新课程的信息，支持部分字段更新。

### 请求信息

- **URL**: `/api/courses/update`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **需要认证**: ✅ 是

### 请求参数

```json
{
  "access_token": "your_access_token_here",
  "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
  "title": "网球正手技术强化训练",
  "currentPrice": 120.00,
  "maxStudents": 12
}
```

### 可更新字段

| 参数 | 类型 | 说明 |
|------|------|------|
| **access_token** | string | **用户身份令牌（必须）** |
| courseId | string | 课程ID（必填） |
| title | string | 课程标题 |
| description | string | 课程描述 |
| coverImage | string | 封面图片URL |
| level | string | 课程级别 |
| category | string | 课程分类 |
| time | string | 上课时间 |
| duration | integer | 课程时长 |
| location | string | 上课地点 |
| minStudents | integer | 最少学员数 |
| maxStudents | integer | 最多学员数 |
| originalPrice | decimal | 原价 |
| currentPrice | decimal | 现价 |
| status | integer | 课程状态 |

### 响应示例

```json
{
  "code": 200,
  "message": "课程更新成功"
}
```

---

## 5. 删除课程

### 接口说明
删除课程（软删除），只有没有学员报名的课程才能删除。

### 请求信息

- **URL**: `/api/courses/delete`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **需要认证**: ✅ 是

### 请求参数

```json
{
  "access_token": "your_access_token_here",
  "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4"
}
```

### 响应示例

**成功响应：**

```json
{
  "code": 200,
  "message": "课程删除成功"
}
```

**失败响应（有学员报名）：**

```json
{
  "code": 400,
  "message": "课程已有5名学员报名，无法删除"
}
```

---

## 6. 学员报名课程

### 接口说明
学员报名课程，会检查课程状态、人数限制和是否重复报名。

### 请求信息

- **URL**: `/api/courses/enroll`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **需要认证**: ✅ 是

### 请求参数

```json
{
  "access_token": "your_access_token_here",
  "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
  "userId": "oUSER123456789",
  "userName": "李学员"
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| **access_token** | string | **是** | **用户身份令牌（必须）** |
| courseId | string | 是 | 课程ID |
| userId | string | 是 | 用户ID（微信openid） |
| userName | string | 是 | 用户姓名 |

### 响应示例

**成功响应：**

```json
{
  "code": 200,
  "message": "报名成功",
  "data": {
    "enrollmentId": "ENROLL-COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4-oUSER123456789-m3n4o5p6",
    "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
    "amount": 150.00
  }
}
```

**失败响应（课程已满）：**

```json
{
  "code": 400,
  "message": "课程报名人数已满"
}
```

**失败响应（已报名）：**

```json
{
  "code": 400,
  "message": "您已报名此课程"
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| **100** | **Access Token 无效或已过期** |
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 405 | 请求方法不允许 |
| 500 | 服务器内部错误 |

---

## 数据字典

### 课程级别 (level)

| 值 | 说明 |
|----|------|
| beginner | 初级 |
| intermediate | 中级 |
| advanced | 高级 |

### 课程分类 (category)

| 值 | 说明 |
|----|------|
| technique | 技术训练 |
| physical | 体能训练 |
| strategy | 战术策略 |
| mental | 心理训练 |

### 课程状态 (status)

| 值 | 说明 |
|----|------|
| 1 | 待开课 |
| 2 | 进行中 |
| 3 | 已结束 |
| 4 | 已取消 |

### 支付状态 (payment_status)

| 值 | 说明 |
|----|------|
| 1 | 未支付 |
| 2 | 已支付 |
| 3 | 已退款 |

### 报名状态 (enrollment_status)

| 值 | 说明 |
|----|------|
| 1 | 已报名 |
| 2 | 已取消 |
| 3 | 已完成 |

---

## 使用示例

### Python 示例

```python
import requests
import json

# 先获取 access_token
login_url = "http://your-domain.com/userlogin"
login_data = {"js_code": "微信小程序登录返回的code"}
login_response = requests.post(login_url, json=login_data)
access_token = login_response.json()['result']['access_token']

# 1. 批量发布课程
url = "http://your-domain.com/api/courses/publish"
data = {
    "access_token": access_token,  # 必须传递
    "coachId": "oABC123XYZ789",
    "coachName": "张教练",
    "courseInfo": {
        "title": "网球正手技术提升训练",
        "description": "本课程专注于提升网球正手技术...",
        "coverImage": "https://cdn.example.com/images/forehand.jpeg",
        "level": "intermediate",
        "category": "technique",
        "time": "10:00",
        "duration": 90,
        "location": "深圳湾体育中心1号场",
        "minStudents": 3,
        "maxStudents": 10,
        "originalPrice": 180.00,
        "currentPrice": 150.00
    },
    "dates": ["2026-01-10", "2026-01-11", "2026-01-12"]
}

response = requests.post(url, json=data)
result = response.json()
print(result)

# 2. 查询课程列表（URL参数方式）
url = "http://your-domain.com/api/courses/list"
params = {
    "access_token": access_token,  # 必须传递
    "coachId": "oABC123XYZ789",
    "status": 1,
    "page": 1,
    "pageSize": 10
}

response = requests.get(url, params=params)
result = response.json()
print(result)

# 或使用 Header 方式
headers = {
    "Authorization": f"Bearer {access_token}"
}
response = requests.get(url, params={"coachId": "oABC123XYZ789"}, headers=headers)
result = response.json()
print(result)

# 3. 学员报名
url = "http://your-domain.com/api/courses/enroll"
data = {
    "access_token": access_token,  # 必须传递
    "courseId": "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
    "userId": "oUSER123456789",
    "userName": "李学员"
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

### JavaScript 示例

```javascript
// 先获取 access_token
const getAccessToken = async (jsCode) => {
  const response = await fetch('/userlogin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ js_code: jsCode })
  });
  const result = await response.json();
  return result.result.access_token;
};

// 1. 批量发布课程
const publishCourses = async (accessToken) => {
  const data = {
    access_token: accessToken,  // 必须传递
    coachId: "oABC123XYZ789",
    coachName: "张教练",
    courseInfo: {
      title: "网球正手技术提升训练",
      description: "本课程专注于提升网球正手技术...",
      coverImage: "https://cdn.example.com/images/forehand.jpeg",
      level: "intermediate",
      category: "technique",
      time: "10:00",
      duration: 90,
      location: "深圳湾体育中心1号场",
      minStudents: 3,
      maxStudents: 10,
      originalPrice: 180.00,
      currentPrice: 150.00
    },
    dates: ["2026-01-10", "2026-01-11", "2026-01-12"]
  };

  const response = await fetch('/api/courses/publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });

  const result = await response.json();
  console.log(result);
};

// 2. 查询课程列表
const getCourses = async (accessToken) => {
  const params = new URLSearchParams({
    access_token: accessToken,  // 必须传递
    coachId: "oABC123XYZ789",
    status: 1,
    page: 1,
    pageSize: 10
  });

  const response = await fetch(`/api/courses/list?${params}`);
  const result = await response.json();
  console.log(result);
};

// 3. 学员报名
const enrollCourse = async (accessToken) => {
  const data = {
    access_token: accessToken,  // 必须传递
    courseId: "COURSE-oABC123XYZ789-2026-01-10-a1b2c3d4",
    userId: "oUSER123456789",
    userName: "李学员"
  };

  const response = await fetch('/api/courses/enroll', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });

  const result = await response.json();
  console.log(result);
};

// 使用示例
(async () => {
  const accessToken = await getAccessToken('微信小程序返回的code');
  await publishCourses(accessToken);
  await getCourses(accessToken);
  await enrollCourse(accessToken);
})();
```

---

## 注意事项

1. **⚠️ Access Token 必须传递**：所有接口都需要有效的 access_token
2. **Token 过期时间**：access_token 有效期为 2 天，过期后需要重新登录获取
3. **Token 传递方式**：
   - POST 请求：在请求体中传递 `access_token` 字段
   - GET 请求：在 URL 参数中传递或使用 Authorization Header
4. **批量发布课程**：一次性发布多个日期的课程，所有课程共享相同的课程信息
5. **事务处理**：批量发布使用数据库事务，确保全部成功或全部失败
6. **软删除**：删除课程不会真正从数据库删除，只是标记为已删除
7. **报名限制**：报名前会检查课程状态、人数限制和是否重复报名
8. **课程ID生成规则**：`COURSE-{教练ID}-{日期}-{随机字符串}`
9. **报名ID生成规则**：`ENROLL-{课程ID}-{用户ID}-{随机字符串}`

---

**文档版本**: v1.1  
**最后更新**: 2026年1月5日  
**维护者**: ClubEngine Team  
**重要更新**: ✅ 所有接口已添加 access_token 身份验证
