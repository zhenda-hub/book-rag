# 移动 App 开发流程指南

## 概述

本文档描述从零开始开发一个 Android/iOS 应用的完整流程，包括技术选型、开发、测试、上架等各个环节。

---

## 快速导航：开发流程一览

```
第一步：选技术栈（选1个）
┌─────────────────────────────────────────────────────────────┐
│  只开发 Android？→ Kotlin + Android Studio                 │
│  只开发 iOS？     → Swift + Xcode                           │
│  要跨平台？       → React Native（推荐）或 Flutter          │
└─────────────────────────────────────────────────────────────┘
                              ↓
第二步：学基础（1-2周）
┌─────────────────────────────────────────────────────────────┐
│  • 语言的语法基础（Kotlin/Swift/JS/Dart）                    │
│  • 基本的 UI 组件（按钮、列表、输入框）                      │
│  • 页面导航（页面跳转）                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
第三步：做第一个 App（2-4周）
┌─────────────────────────────────────────────────────────────┐
│  • 简单的待办事项/记事本 App                                 │
│  • 练习：列表展示、增删改查、页面跳转                        │
│  • 熟悉开发工具的调试功能                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
第四步：学网络请求（1-2周）
┌─────────────────────────────────────────────────────────────┐
│  • HTTP 请求基础（GET/POST）                                 │
│  • JSON 数据解析                                             │
│  • 异步处理（不阻塞 UI）                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
第五步：学数据存储（1周）
┌─────────────────────────────────────────────────────────────┐
│  • 轻量级存储：保存用户设置、Token                           │
│  • 本地数据库：保存离线数据                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
第六步：做正式项目（4-8周）
┌─────────────────────────────────────────────────────────────┐
│  • 搭建项目架构（MVVM）                                      │
│  • 对接后端 API                                             │
│  • 完善功能和交互                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
第七步：测试和上架（1-2周）
┌─────────────────────────────────────────────────────────────┐
│  • 真机测试、修复 Bug                                        │
│  • 准备上架材料、提交审核                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术栈对比：一次只学一个

| 如果你想... | 技术栈选择 | 开发工具 | 学习曲线 |
|------------|-----------|---------|---------|
| **最快上手** | React Native + Expo | VS Code | ⭐⭐ |
| **Android 原生** | Kotlin | Android Studio | ⭐⭐⭐ |
| **iOS 原生** | Swift | Xcode（仅 Mac） | ⭐⭐⭐ |
| **性能最优** | Flutter | VS Code / Android Studio | ⭐⭐⭐⭐ |

**建议**：新手从 **React Native + Expo** 开始，原因：
- 用 JavaScript/TypeScript（Web 开发者无障碍）
- Expo 提供很多现成功能（相机、地图等）
- 一套代码跑 Android + iOS
- 有大量学习资源和社区支持

---

## 最简学习路径（以 React Native 为例）

### 第1周：环境搭建 + Hello World
```bash
# 1. 安装 Node.js
# 2. 安装 Expo CLI
npm install -g expo-cli

# 3. 创建项目
npx create-expo-app my-first-app

# 4. 运行
cd my-first-app
npx expo start
```

**本周目标**：
- 能跑起来一个 Demo
- 修改文字，看到效果
- 理解基本的组件（View, Text, Button）

### 第2周：基础组件
```
需要掌握的组件（就这几个）：
├── View（容器，像 HTML 的 div）
├── Text（文字）
├── Button（按钮）
├── TextInput（输入框）
├── Image（图片）
├── ScrollView（滚动列表）
└── FlatList（高性能列表，重要！）
```

### 第3周：导航
```
页面跳转：
├── React Navigation（推荐）
│   ├── Stack Navigation（堆栈导航）
│   └── Tab Navigation（底部标签栏）
```

### 第4周：第一个完整 App
```
做一个简单 App，比如：
├── 待办事项（Todo List）
├── 天气查询 App
└── 笔记 App

练手功能：
├── 列表展示
├── 添加/删除
├── 页面跳转
└── 本地存储
```

### 第5-6周：网络请求
```typescript
// 就这么简单
import axios from 'axios'

// 获取数据
const response = await axios.get('https://api.example.com/users')
console.log(response.data)

// 发送数据
await axios.post('https://api.example.com/users', {
  name: '张三',
  age: 25
})
```

### 第7-8周：本地存储
```typescript
// 安装
npm install @react-native-async-storage/async-storage

// 使用
import AsyncStorage from '@react-native-async-storage/async-storage'

// 保存
await AsyncStorage.setItem('userToken', 'abc123')

// 读取
const token = await AsyncStorage.getItem('userToken')

// 删除
await AsyncStorage.removeItem('userToken')
```

### 第9-12周：正式项目
```
选一个项目方向：
├── 租房 App（房源列表、详情、收藏）
├── 电商 App（商品列表、购物车、订单）
├── 社交 App（动态列表、发布、评论）
└── 工具 App（记账、天气、新闻）

技术要点：
├── 搭建 Tab 导航结构
├── 实现列表页+详情页
├── 对接真实 API
├── 实现下拉刷新、上拉加载
├── 添加登录注册
└── 本地缓存数据
```

### 第13-14周：完善和上架
```
• 修复 Bug
• 优化性能
• 准备图标、截图
• 提交审核
```

---

## 不需要一次学完的东西

以下技术**按需学习**，不要一开始就全学：

| 技术 | 什么时候学 |
|-----|----------|
| 状态管理（Redux/MobX） | 当多个页面需要共享数据时 |
| 原生模块开发 | 当需要调用硬件功能（蓝牙、NFC）时 |
| 动画库（Reanimated） | 当需要复杂动画时 |
| 性能优化 | 当 App 变卡顿的时候 |
| CI/CD 自动构建 | 当需要频繁发布版本时 |

**核心原则**：先用最简单的方式做出来，再逐步优化！

---

## 一、前期准备阶段

### 1.1 需求分析
1. **明确核心功能** - App 要解决什么问题
2. **目标用户画像** - 谁会使用这个 App
3. **竞品分析** - 市场上有哪些类似产品
4. **商业模式** - 如何盈利（免费/付费/内购/广告）

### 1.2 技术选型决策

| 技术路线 | 适用场景 | 优势 | 劣势 |
|---------|---------|------|------|
| **原生开发** | 大型项目、追求极致性能 | 性能最好、功能完整 | 成本高、开发周期长 |
| **React Native** | 中小型项目、Web 技术团队 | 一套代码双端、热更新 | 性能略逊于原生 |
| **Flutter** | 追求 UI 一致性、Google 技术栈 | 高性能、UI 精美 | 生态相对较新 |
| ** uni-app / Taro** | 主要面向国内市场 | 支持小程序 | 功能受限 |

### 1.3 团队配置建议
- **产品经理** x1：需求管理、原型设计
- **UI 设计师** x1：界面设计、图标切图
- **前端开发** x1-2：根据技术栈确定
- **后端开发** x1：API 接口开发
- **测试** x1：功能测试、兼容性测试

---

## 二、移动端架构详解

### 2.1 主流架构模式

移动端 App 主要采用以下几种架构模式：

#### MVVM (Model-View-ViewModel) - **最主流**

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer (View)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Activity │  │ Fragment │  │ Compose  │  │  SwiftUI │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼────────────┼────────────┼────────────┼────────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                             │ observes
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  ViewModel Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  State   │  │  Events  │  │ Business │                  │
│  │  Holder  │  │ Handler  │  │   Logic  │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
└───────┼────────────┼────────────┼──────────────────────────┘
        │            │            │
        └────────────┴────────────┘
                             │ calls
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer (Model)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Repository│  │   API    │  │ Database │  │  Cache   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**特点**：
- View 不包含业务逻辑，只负责 UI 渲染
- ViewModel 持有 UI 状态和业务逻辑
- Data Layer 负责数据获取和缓存
- **优势**：可测试性强、职责清晰、易于维护

#### MVI (Model-View-Intent) - **新兴趋势**

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   View   │ ──▶ │ Intent   │ ──▶ │  Model   │ ──▶ │  State   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                                                           │
     │                                                           │
     └───────────────────────────────────────────────────────────┘
                          renders
```

**特点**：
- 单向数据流
- Intent 代表用户意图
- Model 是不可变的状态
- **优势**：状态可预测、易于调试

#### Clean Architecture - **大型项目**

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                     │
│        (ViewModel, Compose, SwiftUI, Activities)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                          │
│         (Use Cases, Business Logic, Entities)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                           │
│    (Repository, API, Database, Cache, Models)               │
└─────────────────────────────────────────────────────────────┘
```

**特点**：
- 依赖倒置（内层不依赖外层）
- 业务逻辑独立于框架
- **优势**：高度解耦、易于测试和扩展

---

### 2.2 数据存储方案

#### 移动端数据存储层级

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层级存储                            │
├─────────────────────────────────────────────────────────────┤
│  1. 内存存储 (In-Memory)                                    │
│     ├── StateFlow / LiveData (Android)                      │
│     ├── @State / @ObservedObject (iOS)                     │
│     └── Redux Store / Bloc (跨平台)                         │
│                                                             │
│  2. 本地持久化 (Local Persistence)                          │
│     ├── 关系型数据库                                        │
│     │   ├── Room (Android)                                  │
│     │   ├── CoreData (iOS)                                  │
│     │   └── Realm / SQLite                                 │
│     │                                                        │
│     ├── 键值存储                                             │
│     │   ├── SharedPreferences (Android)                     │
│     │   ├── UserDefaults (iOS)                              │
│     │   └── MMKV (高性能跨平台)                             │
│     │                                                        │
│     ├── 文件存储                                             │
│     │   ├── Internal Storage (私有)                         │
│     │   ├── External Storage (公开)                         │
│     │   └── Sandbox (iOS)                                   │
│     │                                                        │
│     └── NoSQL 数据库                                        │
│         ├── Hive (Flutter)                                  │
│         ├── Realm (跨平台)                                  │
│         └── ObjectBox                                       │
│                                                             │
│  3. 远程服务器 (Remote Server)                              │
│     ├── REST API                                            │
│     ├── GraphQL                                             │
│     └── WebSocket (实时通信)                                │
└─────────────────────────────────────────────────────────────┘
```

#### 数据存储选择指南

| 数据类型 | 推荐方案 | 说明 |
|---------|---------|------|
| 用户 Token | SharedPreferences / Keychain | 敏感信息加密存储 |
| UI 状态 | StateFlow / @State | 内存存储，随页面释放 |
| 用户设置 | UserDefaults / MMKV | 轻量级键值对 |
| 离线数据 | Room / CoreData | 关系型本地数据库 |
| 大文件 | Internal Storage | 图片、视频、文档 |
| 缓存数据 | LRU Cache / DiskLruCache | 图片、网络响应缓存 |

---

### 2.3 前后端交互方式

#### 完整的数据交互流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Mobile App (前端)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │     View    │───▶│ ViewModel   │───▶│ Repository  │            │
│  │   (UI层)    │◀───│  (业务层)   │◀───│  (数据层)   │            │
│  └─────────────┘    └─────────────┘    └──────┬──────┘            │
│                                              │                     │
│                                              │ calls               │
│                                              ▼                     │
│  ┌─────────────────────────────────────────────────────┐          │
│  │                    API Service                       │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │          │
│  │  │  Retrofit│  │   Axios  │  │    Dio   │          │          │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘          │          │
│  └───────┼────────────┼────────────┼──────────────────┘          │
└──────────┼────────────┼────────────┼───────────────────────────────┘
           │            │            │
           │            │            │ HTTP/HTTPS
           │            │            │
           ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Network (网络层)                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │   DNS    │───▶│   CDN    │───▶│ Firewall │───▶│ Load     │     │
│  │          │    │          │    │          │    │ Balancer │     │
│  └──────────┘    └──────────┘    └──────────┘    └─────┬────┘     │
└────────────────────────────────────────────────────────┼───────────┘
                                                         │
                                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend Server (后端)                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      API Gateway                            │   │
│  │         (Nginx / Kong / AWS API Gateway)                    │   │
│  └────────────────────────┬────────────────────────────────────┘   │
│                           │                                        │
│      ┌────────────────────┼────────────────────┐                   │
│      ▼                    ▼                    ▼                   │
│  ┌─────────┐        ┌─────────┐          ┌─────────┐             │
│  │  Auth   │        │ Business│          │ Payment │             │
│  │ Service │        │ Service │          │ Service │             │
│  └────┬────┘        └────┬────┘          └────┬────┘             │
│       │                  │                    │                   │
│       └──────────────────┴────────────────────┘                   │
│                          │                                         │
│                          ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Data Layer (后端)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │PostgreSQL│  │  Redis   │  │   OSS    │  │  Rabbit  │   │   │
│  │  │(主数据库) │  │  (缓存)  │  │(文件存储)│  │  (消息)  │   │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

#### 常用通信协议

| 协议 | 用途 | 特点 |
|-----|------|------|
| **REST API** | 常规数据交互 | 简单、通用、缓存友好 |
| **GraphQL** | 复杂数据查询 | 按需获取、减少请求次数 |
| **WebSocket** | 实时通信 | 双向通信、低延迟 |
| **gRPC** | 微服务通信 | 高性能、类型安全 |

#### API 请求示例

```typescript
// React Native / Flutter 中的典型 API 调用

// 1. 定义 API Service
class UserService {
  private api = 'https://api.example.com/v1'

  // 获取用户信息
  async getUserProfile(userId: string) {
    const response = await fetch(`${this.api}/users/${userId}`, {
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      }
    })
    return response.json()
  }

  // 更新用户信息
  async updateUser(userId: string, data: any) {
    const response = await fetch(`${this.api}/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    return response.json()
  }
}

// 2. 在 ViewModel 中调用
class ProfileViewModel {
  private userService = new UserService()
  private state = writable<User | null>(null)
  private loading = writable(false)
  private error = writable<string | null>(null)

  async loadProfile(userId: string) {
    this.loading.set(true)
    try {
      const user = await this.userService.getUserProfile(userId)
      this.state.set(user)
    } catch (e) {
      this.error.set('加载失败')
    } finally {
      this.loading.set(false)
    }
  }
}

// 3. UI 层观察状态
function ProfileScreen({ userId }: { userId: string }) {
  const viewModel = new ProfileViewModel()
  const state = useStore(viewModel.state)
  const loading = useStore(viewModel.loading)

  useEffect(() => {
    viewModel.loadProfile(userId)
  }, [userId])

  if (loading) return <Loading />
  return <UserProfile user={state} />
}
```

---

### 2.4 状态管理方案

| 框架 | 状态管理方案 | 特点 |
|-----|-------------|------|
| **Android** | StateFlow + LiveData | 官方推荐、与生命周期绑定 |
| **iOS** | @State + @ObservedObject | SwiftUI 原生支持 |
| **React Native** | Redux Toolkit / Zustand | 生态成熟、调试工具完善 |
| **Flutter** | Riverpod / Bloc | 类型安全、依赖注入 |

---

## 三、技术方案设计

### 3.1 原生开发方案

#### Android (Kotlin/Java)
```
技术栈：
- 语言：Kotlin (推荐) / Java
- 架构：MVVM / MVI
- UI：Jetpack Compose (推荐) / XML
- 网络：Retrofit + OkHttp
- 异步：Kotlin Coroutines / Flow
- 依赖注入：Hilt / Koin
- 数据库：Room
```

#### iOS (Swift)
```
技术栈：
- 语言：Swift
- 架构：MVVM / VIPER
- UI：SwiftUI (推荐) / UIKit
- 网络：URLSession / Alamofire
- 异步：Swift Concurrency (async/await)
- 依赖注入：SwiftUI @Environment / Combine
- 数据库：CoreData / SwiftData
```

### 3.2 跨平台方案

#### React Native
```
技术栈：
- 语言：JavaScript/TypeScript
- 框架：React Native + Expo
- 导航：React Navigation
- 状态管理：Redux Toolkit / Zustand / Jotai
- UI 组件：React Native Paper / NativeBase
- 网络：axios / fetch
- 本地存储：AsyncStorage / MMKV
```

#### Flutter
```
技术栈：
- 语言：Dart
- 框架：Flutter
- 状态管理：Riverpod / Bloc / Provider
- UI 组件：Material Design / Cupertino
- 网络：dio
- 本地存储：hive / shared_preferences
```

---

## 四、开发流程

### 4.1 项目初始化

#### 原生 Android
```bash
# 使用 Android Studio 创建新项目
# 或使用命令行
flutter create my_app  # Flutter
npx react-native init MyApp  # React Native
```

#### 原生 iOS
```bash
# 使用 Xcode 创建新项目
# File > New > Project > iOS App
```

### 4.2 目录结构规范

```
my-app/
├── src/
│   ├── api/              # API 请求
│   ├── assets/           # 静态资源
│   ├── components/       # 通用组件
│   ├── screens/          # 页面
│   ├── navigation/       # 导航配置
│   ├── store/            # 状态管理
│   ├── utils/            # 工具函数
│   ├── hooks/            # 自定义 Hooks (RN)
│   ├── constants/        # 常量
│   └── types/            # 类型定义
├── android/              # Android 原生代码
├── ios/                  # iOS 原生代码
├── package.json          # 依赖配置
└── README.md
```

### 4.3 开发顺序建议

| 阶段 | 内容 | 优先级 |
|-----|------|--------|
| 1 | 搭建项目框架、导航、主题 | P0 |
| 2 | 开发登录注册、用户系统 | P0 |
| 3 | 开发核心业务功能 | P0 |
| 4 | 完善细节交互、动画 | P1 |
| 5 | 性能优化、错误处理 | P1 |

---

## 五、测试阶段

### 5.1 测试类型

| 测试类型 | 工具 | 说明 |
|---------|------|------|
| 单元测试 | Jest / XCTest | 测试函数、组件 |
| 集成测试 | Detox / XCUITest | 测试用户流程 |
| 真机测试 | TestFlight / 内测 | 真实环境验证 |

### 5.2 兼容性测试

#### Android
- 不同 Android 版本（API 21-34）
- 不同屏幕尺寸
- 不同厂商（华为、小米、OPPO、vivo）

#### iOS
- 不同 iOS 版本（iOS 15-17）
- 不同机型（iPhone SE 到 iPhone 15 Pro Max）
- iPad 适配

### 5.3 性能测试
- 启动时间 < 3秒
- 页面帧率 > 60fps
- 内存占用合理
- APK/IPA 体积优化

---

## 六、上架发布阶段

### 6.1 Android 上架流程

#### 1. 准备材料
```
- 应用图标（多种尺寸）
- 应用截图（手机、平板）
- 应用描述（简短、详细）
- 隐私政策
- 签名证书（.jks）
```

#### 2. 生成签名包
```bash
# Android
./gradlew assembleRelease

# 生成签名文件
keytool -genkey -v -keystore my-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias my-key-alias
```

#### 3. 上架到应用商店
- **Google Play**（国际）
  - 开发者账号 $25（一次性）
  - 审核周期：1-3天

- **国内应用商店**
  - 华为应用市场
  - 小米应用商店
  - OPPO 软件商店
  - vivo 应用商店
  - 应用宝（腾讯）
  - 360 手机助手
  - 审核周期：1-7天不等

### 6.2 iOS 上架流程

#### 1. 准备材料
```
- Apple Developer 账号（$99/年）
- 应用图标（多种尺寸）
- 启动屏幕
- 应用截图
- 应用描述
- 隐私政策
```

#### 2. 证书配置
```
步骤：
1. 创建 App ID
2. 创建 Distribution Certificate
3. 创建 Provisioning Profile
4. Xcode 配置签名
```

#### 3. 上架到 App Store
```bash
# Archive 打包
Xcode > Product > Archive

# 使用 Transporter 上传
或通过 Xcode 直接上传
```

#### 4. 填写应用信息
- 在 App Store Connect 创建应用
- 填写版本信息、截图、描述
- 提交审核
- **审核周期：1-3天**（首次可能更长）

---

## 七、上线后运营

### 7.1 监控工具
- **崩溃监控**：Firebase Crashlytics / Bugly
- **数据分析**：Firebase Analytics / 友盟
- **性能监控**：Firebase Performance

### 7.2 版本更新
```
1. 收集用户反馈
2. 分析数据，规划新版本
3. 开发测试
4. 提交审核
5. 发布更新
```

---

## 八、成本估算

### 8.1 开发成本

| 项目 | 成本 | 说明 |
|-----|------|------|
| Apple Developer | $99/年 | iOS 上架必需 |
| Google Play | $25（一次性） | Android 上架必需 |
| 服务器 | ¥200-2000/月 | 根据流量 |
| 第三方服务 | ¥500-5000/月 | 短信、推送、存储等 |
| 人工成本 | - | 根据团队规模 |

### 8.2 时间估算

| 项目类型 | 开发周期 |
|---------|---------|
| 简单 App | 1-2 月 |
| 中等 App | 3-6 月 |
| 复杂 App | 6-12 月 |

---

## 九、常见问题

### Q1: 选择原生还是跨平台？
- 预算充足、追求极致体验 → 原生
- 预算有限、快速迭代 → 跨平台（React Native 推荐）

### Q2: 如何处理 Android 碎片化？
- 使用 androidx 库
- 最低支持 API 21（Android 5.0）
- 充分测试主流机型

### Q3: App 审核被拒怎么办？
- 仔细阅读拒审原因
- 对照审核指南修改
- 申诉或重新提交

### Q4: 如何保护源代码？
- Android：代码混淆（R8/ProGuard）
- iOS：Swift 代码默认有一定保护

---

## 十、推荐资源

### 学习资源
- **Android**: https://developer.android.com/
- **iOS**: https://developer.apple.com/
- **React Native**: https://reactnative.dev/
- **Flutter**: https://flutter.dev/

### UI 设计
- **Figma**: 界面设计工具
- **Sketch**: Mac 平台设计工具
- **Material Design**: Android 设计规范
- **Human Interface Guidelines**: iOS 设计规范

### 图标资源
- **iconfont**: 阿里巴巴图标库
- **Flaticon**: 免费图标
- **AppIconGenerator**: 自动生成各尺寸图标
