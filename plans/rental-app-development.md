# 租房软件开发技术方案

## 一、项目概述

### 1.1 项目目标
开发一套完整的租房软件，支持 Android、iOS App 和微信小程序，提供房源搜索、预约看房、在线签约、支付等完整功能。

### 1.2 核心功能
- **房源管理**：发布、编辑、下架房源
- **搜索筛选**：位置、价格、户型、面积等多维度搜索
- **用户系统**：注册登录、个人中心、收藏管理
- **预约看房**：在线预约、时间管理、到店签到
- **在线签约**：电子合同、身份认证、电子签名
- **支付系统**：租金支付、押金管理、账单记录
- **评价系统**：房源评价、房东评价
- **消息通知**：系统消息、预约提醒、合同通知

---

## 二、技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          客户端层                                │
├─────────────┬─────────────┬─────────────┬─────────────────────┤
│  Android    │    iOS      │  微信小程序  │     管理后台         │
│  (RN App)   │  (RN App)   │   (原生)    │    (Web)            │
└──────┬──────┴──────┬──────┴──────┬──────┴──────────┬──────────┘
       │             │             │                 │
       └─────────────┴─────────────┴─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   API Gateway   │
                    │  (Nginx/Kong)   │
                    └────────┬────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐    ┌────────▼────────┐    ┌───────▼──────┐
│  房源服务   │    │   用户/认证服务  │    │  支付/合约服务│
└─────────────┘    └─────────────────┘    └──────────────┘
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐    ┌────────▼────────┐    ┌───────▼──────┐
│ PostgreSQL  │    │     Redis       │    │    OSS       │
│  (主数据库) │    │   (缓存/队列)    │    │  (文件存储)   │
└─────────────┘    └─────────────────┘    └──────────────┘
```

### 2.2 技术选型

#### 前端技术栈

| 端 | 技术方案 | 说明 |
|---|---------|------|
| **Android/iOS App** | React Native + Expo | 一套代码双端运行，成熟稳定 |
| **微信小程序** | 原生小程序 / Taro | 使用原生开发保证最佳体验 |
| **管理后台** | React + Ant Design | 后台管理系统 |

#### 后端技术栈

| 组件 | 技术方案 | 说明 |
|-----|---------|------|
| **后端框架** | FastAPI (Python) | 高性能、自动文档、类型安全 |
| **数据库** | PostgreSQL 15+ | 关系型数据库，支持 JSONB |
| **缓存** | Redis | 会话、验证码、限流 |
| **消息队列** | Celery + Redis | 异步任务、定时任务 |
| **文件存储** | 阿里云 OSS / 腾讯云 COS | 图片、视频存储 |
| **搜索服务** | PostgreSQL Full-Text Search | 中小规模够用，后期可切换 ES |

#### 第三方服务

| 服务 | 提供商 | 用途 |
|-----|--------|------|
| **支付** | 微信支付、支付宝 | 租金、押金支付 |
| **地图** | 高德地图 / 腾讯地图 | 房源位置、周边配套 |
| **实名认证** | 腾讯云、阿里云 | 身份证 OCR、人脸核身 |
| **电子签名** | e签宝 / 法大大 | 电子合同签署 |
| **短信** | 阿里云、腾讯云 | 验证码、通知 |
| **推送** | 极光推送 / 个推 | App 消息推送 |

---

## 三、数据库设计

### 3.1 核心数据表

```sql
-- 用户表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    nickname VARCHAR(50),
    avatar_url VARCHAR(500),
    real_name VARCHAR(50),
    id_card VARCHAR(18),
    id_card_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'tenant', -- tenant, landlord, admin
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 房源表
CREATE TABLE listings (
    id BIGSERIAL PRIMARY KEY,
    landlord_id BIGINT REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    province VARCHAR(50),
    city VARCHAR(50),
    district VARCHAR(50),
    address VARCHAR(500),
    longitude DECIMAL(10, 7),
    latitude DECIMAL(10, 7),
    price DECIMAL(10, 2),
    payment_type VARCHAR(50), -- 押一付三、押一付一
    area DECIMAL(6, 2),
    rooms INT, -- 室
    halls INT, -- 厅
    bathrooms INT, -- 卫
    floor INT,
    total_floors INT,
    orientation VARCHAR(20), -- 朝向
    decoration VARCHAR(50), -- 精装、简装、毛坯
    facilities JSONB, -- 设施列表
    images JSONB, -- 图片URL数组
    video_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending', -- pending, active, rented, inactive
    view_count INT DEFAULT 0,
    favorite_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 预约看房表
CREATE TABLE appointments (
    id BIGSERIAL PRIMARY KEY,
    listing_id BIGINT REFERENCES listings(id),
    tenant_id BIGINT REFERENCES users(id),
    landlord_id BIGINT REFERENCES users(id),
    appointment_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, completed, cancelled
    tenant_arrived BOOLEAN DEFAULT FALSE,
    landlord_arrived BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 合同表
CREATE TABLE contracts (
    id BIGSERIAL PRIMARY KEY,
    listing_id BIGINT REFERENCES listings(id),
    landlord_id BIGINT REFERENCES users(id),
    tenant_id BIGINT REFERENCES users(id),
    contract_no VARCHAR(50) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_rent DECIMAL(10, 2) NOT NULL,
    deposit DECIMAL(10, 2),
    payment_type VARCHAR(50),
    signing_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active', -- active, terminated, expired
    contract_url VARCHAR(500), -- 电子合同PDF
    created_at TIMESTAMP DEFAULT NOW()
);

-- 支付记录表
CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    contract_id BIGINT REFERENCES contracts(id),
    payer_id BIGINT REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    type VARCHAR(20), -- rent, deposit, utility
    payment_method VARCHAR(50), -- wechat, alipay
    transaction_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending', -- pending, success, failed, refunded
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 收藏表
CREATE TABLE favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    listing_id BIGINT REFERENCES listings(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, listing_id)
);

-- 评价表
CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,
    contract_id BIGINT REFERENCES contracts(id),
    reviewer_id BIGINT REFERENCES users(id),
    target_id BIGINT REFERENCES users(id), -- 被评价人（房东或租客）
    rating INT CHECK (rating >= 1 AND rating <= 5),
    content TEXT,
    images JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 四、API 接口设计

### 4.1 RESTful API 规范

```
基础路径: /api/v1

认证方式: JWT Bearer Token
响应格式: JSON
```

### 4.2 核心接口

#### 用户模块
```
POST   /auth/register           # 注册
POST   /auth/login              # 登录
POST   /auth/logout             # 登出
POST   /auth/refresh-token      # 刷新token
POST   /auth/send-code          # 发送验证码
GET    /users/profile           # 获取个人信息
PUT    /users/profile           # 更新个人信息
POST   /users/verify-id         # 实名认证
```

#### 房源模块
```
GET    /listings                # 房源列表（支持筛选、分页）
GET    /listings/:id            # 房源详情
POST   /listings                # 发布房源（房东）
PUT    /listings/:id            # 更新房源
DELETE /listings/:id            # 删除房源
POST   /listings/:id/favorite   # 收藏/取消收藏
GET    /listings/favorites      # 我的收藏
```

#### 预约模块
```
POST   /appointments            # 创建预约
GET    /appointments            # 我的预约列表
PUT    /appointments/:id        # 修改预约
DELETE /appointments/:id        # 取消预约
PUT    /appointments/:id/confirm # 确认预约
POST   /appointments/:id/checkin # 到店签到
```

#### 合同模块
```
POST   /contracts               # 创建合同
GET    /contracts               # 我的合同列表
GET    /contracts/:id           # 合同详情
POST   /contracts/:id/sign      # 签署合同
GET    /contracts/:id/download  # 下载合同
```

#### 支付模块
```
POST   /payments/create         # 创建支付订单
POST   /payments/notify         # 支付回调
GET    /payments/:id            # 支付详情
GET    /payments/history        # 支付历史
```

---

## 五、项目目录结构

```
rental-app/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── listings.py
│   │   │   │   ├── appointments.py
│   │   │   │   ├── contracts.py
│   │   │   │   └── payments.py
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models/             # 数据模型
│   │   │   ├── user.py
│   │   │   ├── listing.py
│   │   │   ├── contract.py
│   │   │   └── ...
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # 业务逻辑
│   │   │   ├── auth_service.py
│   │   │   ├── listing_service.py
│   │   │   ├── payment_service.py
│   │   │   └── ...
│   │   └── utils/              # 工具函数
│   ├── tests/                  # 测试
│   ├── migrations/             # 数据库迁移
│   ├── requirements.txt
│   └── main.py
│
├── mobile/                     # React Native App
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── screens/            # 页面
│   │   │   ├── Auth/
│   │   │   ├── Home/
│   │   │   ├── Listing/
│   │   │   ├── Appointment/
│   │   │   └── Profile/
│   │   ├── navigation/         # 导航配置
│   │   ├── services/           # API 服务
│   │   ├── store/              # 状态管理
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── utils/              # 工具函数
│   │   └── types/              # TypeScript 类型
│   ├── package.json
│   ├── app.json
│   └── tsconfig.json
│
├── miniprogram/                # 微信小程序
│   ├── pages/                  # 页面
│   ├── components/             # 组件
│   ├── utils/                  # 工具函数
│   ├── services/               # API 服务
│   ├── app.json
│   └── project.config.json
│
└── admin/                      # 管理后台
    ├── src/
    │   ├── pages/              # 页面
    │   ├── components/         # 组件
    │   ├── services/           # API 服务
    │   └── utils/              # 工具函数
    └── package.json
```

---

## 六、开发计划

### 6.1 第一阶段：MVP（2-3个月）

| 模块 | 功能 | 优先级 |
|-----|------|--------|
| 用户系统 | 注册、登录、个人中心 | P0 |
| 房源管理 | 发布、列表、详情、搜索 | P0 |
| 预约看房 | 创建预约、状态管理 | P0 |
| 收藏功能 | 收藏/取消收藏 | P1 |

### 6.2 第二阶段：完整功能（2-3个月）

| 模块 | 功能 | 优先级 |
|-----|------|--------|
| 实名认证 | 身份证 OCR、人脸核身 | P0 |
| 电子合同 | 合同生成、电子签名 | P0 |
| 支付系统 | 租金支付、押金管理 | P0 |
| 评价系统 | 房源评价、用户评价 | P1 |

### 6.3 第三阶段：增强功能（持续）

| 模块 | 功能 |
|-----|------|
| 智能推荐 | 基于用户行为的房源推荐 |
| 智能客服 | AI 驱动的自动问答 |
| 数据分析 | 用户行为分析、成交分析 |

---

## 七、安全设计

### 7.1 认证授权
- JWT Token 认证
- Refresh Token 机制
- Token 刷新策略

### 7.2 数据安全
- 密码 bcrypt 加密
- 敏感信息脱敏
- HTTPS 传输加密
- SQL 注入防护

### 7.3 业务安全
- 手机号验证码限流
- 接口防刷（Rate Limiting）
- 文件上传类型和大小限制
- 支付签名验证

---

## 八、运维部署

### 8.1 部署架构

```
                    ┌─────────────┐
                    │   CDN/DNS   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
        │   Nginx   │ │  Nginx │ │   Nginx   │
        │  (静态资源)│ │ (API)  │ │ (WebSocket)│
        └───────────┘ └───┬────┘ └───────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
        │  FastAPI  │ │FastAPI │ │  FastAPI  │
        │  Instance1│ │Instance2│ │  Instance3│
        └─────┬─────┘ └───┬────┘ └─────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
  ┌─────▼─────┐     ┌──────▼──────┐   ┌──────▼──────┐
  │ PostgreSQL │     │    Redis    │   │     OSS     │
  │  (主从)    │     │  (哨兵模式)  │   │  (对象存储)  │
  └───────────┘     └─────────────┘   └─────────────┘
```

### 8.2 技术栈
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **进程管理**: Gunicorn / Uvicorn
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack
- **CI/CD**: GitHub Actions

---

## 九、成本估算

### 9.1 开发成本

| 角色 | 人数 | 周期 | 说明 |
|-----|------|------|------|
| 后端开发 | 2 | 4-6月 | Python/FastAPI |
| 前端开发(RN) | 2 | 4-6月 | React Native |
| 小程序开发 | 1 | 3-4月 | 微信小程序 |
| UI设计 | 1 | 1-2月 | 界面设计 |
| 产品经理 | 1 | 全程 | 需求管理 |
| 测试 | 1 | 2-3月 | 功能测试 |

### 9.2 运营成本（月度）

| 项目 | 成本 |
|-----|------|
| 云服务器 | ¥2000-5000 |
| 数据库 | ¥500-2000 |
| OSS 存储 | ¥500-2000 |
| CDN | ¥500-1500 |
| 短信/推送 | ¥500-2000 |
| 第三方API | ¥1000-3000 |
| **合计** | **¥5000-15000/月** |

---

## 十、风险与应对

| 风险 | 影响 | 应对措施 |
|-----|------|----------|
| 微信审核不通过 | 高 | 严格遵守平台规范，准备资质材料 |
| 支付接口限制 | 中 | 提前申请企业资质，准备备选方案 |
| 电子合同法律效力 | 高 | 选择有资质的第三方电子签名服务 |
| 用户增长不及预期 | 中 | 加强市场推广，优化用户体验 |
| 技术团队人员流失 | 高 | 做好代码文档，知识沉淀 |

---

## 十一、总结

本方案采用 **React Native + FastAPI + PostgreSQL** 的技术栈，具有以下优势：

1. **跨平台高效开发**: 一套后端服务支持多端
2. **技术成熟稳定**: 选用经过大规模验证的技术
3. **易于扩展维护**: 清晰的架构设计，模块化开发
4. **成本可控**: 开源技术栈，降低授权成本
5. **快速迭代**: 敏捷开发，支持快速响应市场变化

建议采用 **敏捷开发模式**，优先完成 MVP 功能上线验证，再逐步迭代完善。
