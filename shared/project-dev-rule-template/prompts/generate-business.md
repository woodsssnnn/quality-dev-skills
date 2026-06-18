# 业务规范生成指南

## 目的

指导AI根据项目业务生成业务规范文档。

## 输入要求

AI需要收集以下信息：

### 1. 项目背景

- 项目名称
- 项目类型（B2B/B2C/SaaS/内部系统等）
- 核心业务流程
- 目标用户群体

### 2. 业务领域

- 行业领域（金融/电商/医疗/教育等）
- 核心业务模块
- 关键业务实体

### 3. 业务规则

- 核心业务规则
- 约束条件
- 异常处理规则

## 生成内容

### 1. 术语表

```markdown
## 术语表

| 术语 | 英文 | 定义 | 使用场景 |
|------|------|------|----------|
| [术语1] | [English] | [定义] | [使用场景] |
| [术语2] | [English] | [定义] | [使用场景] |

### 术语说明

#### [术语1]
- **定义**：[详细定义]
- **示例**：[使用示例]
- **相关术语**：[相关术语]
```

### 2. 业务模块结构

```markdown
## 业务模块结构

### 模块划分
```
项目名称/
├── 用户模块 (User)
│   ├── 注册/登录
│   ├── 个人信息管理
│   └── 权限管理
├── 订单模块 (Order)
│   ├── 创建订单
│   ├── 订单状态管理
│   └── 订单查询
├── 支付模块 (Payment)
│   ├── 支付方式
│   ├── 支付流程
│   └── 退款处理
└── 通知模块 (Notification)
    ├── 站内信
    ├── 邮件
    └── 短信
```

### 模块职责
| 模块 | 职责 | 依赖模块 |
|------|------|----------|
| 用户模块 | 用户认证、授权 | 无 |
| 订单模块 | 订单生命周期管理 | 用户模块、支付模块 |
| 支付模块 | 支付流程处理 | 用户模块 |
| 通知模块 | 消息推送 | 用户模块、订单模块 |

### 模块接口
```typescript
// 用户模块接口
interface UserService {
  register(data: RegisterDTO): Promise<User>;
  login(credentials: LoginDTO): Promise<Token>;
  getUser(id: string): Promise<User>;
  updateUser(id: string, data: UpdateUserDTO): Promise<User>;
}

// 订单模块接口
interface OrderService {
  createOrder(data: CreateOrderDTO): Promise<Order>;
  getOrder(id: string): Promise<Order>;
  updateOrderStatus(id: string, status: OrderStatus): Promise<Order>;
  listOrders(query: OrderQuery): Promise<PaginatedResult<Order>>;
}
```
```

### 3. 通用业务模式

```markdown
## 通用业务模式

### 1. 审批流程
```
提交申请 → 审核中 → 审核通过/驳回 → 执行
    ↓
  撤回申请
```

**实现要点**：
- 状态机管理审批状态
- 支持多级审批
- 记录审批历史

### 2. 生命周期管理
```
草稿 → 进行中 → 已完成 → 已归档
  ↓       ↓
取消    暂停
```

**实现要点**：
- 定义状态流转规则
- 支持状态回退
- 记录状态变更日志

### 3. 权限控制
```
用户 → 角色 → 权限 → 资源
```

**实现要点**：
- RBAC（基于角色的访问控制）
- 资源级别权限
- 前端路由守卫 + 后端接口校验

### 4. 编号生成
```
[前缀][日期][序列号]
如：ORD202606170001
```

**实现要点**：
- 全局唯一性保证
- 支持自定义前缀
- 分布式ID生成（可选）

### 5. 导入导出
```
导入：文件解析 → 数据校验 → 入库
导出：查询数据 → 生成文件 → 下载
```

**实现要点**：
- 大文件分片处理
- 异步任务队列
- 进度反馈

### 6. 锁定机制
```
乐观锁：版本号控制
悲观锁：数据库行锁
分布式锁：Redis实现
```

**实现要点**：
- 根据场景选择锁类型
- 超时释放
- 死锁检测
```

### 4. 核心实体关系

```markdown
## 核心实体关系

### 实体关系图
```
User (用户)
├── 1:N → Order (订单)
├── 1:N → Address (地址)
└── N:M → Role (角色)

Order (订单)
├── N:1 → User (用户)
├── 1:N → OrderItem (订单项)
└── 1:1 → Payment (支付)

Product (商品)
├── 1:N → OrderItem (订单项)
└── N:1 → Category (分类)
```

### 实体定义
```typescript
// 用户实体
interface User {
  id: string;
  username: string;
  email: string;
  phone: string;
  status: UserStatus;
  createdAt: Date;
  updatedAt: Date;
}

// 订单实体
interface Order {
  id: string;
  orderNo: string;
  userId: string;
  totalAmount: number;
  status: OrderStatus;
  items: OrderItem[];
  payment?: Payment;
  createdAt: Date;
  updatedAt: Date;
}

// 订单项实体
interface OrderItem {
  id: string;
  orderId: string;
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}
```

### 状态流转
```typescript
// 用户状态
enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  BANNED = 'banned',
}

// 订单状态
enum OrderStatus {
  PENDING = 'pending',      // 待支付
  PAID = 'paid',            // 已支付
  SHIPPED = 'shipped',      // 已发货
  DELIVERED = 'delivered',  // 已收货
  COMPLETED = 'completed',  // 已完成
  CANCELLED = 'cancelled',  // 已取消
  REFUNDED = 'refunded',    // 已退款
}
```
```

## 输出格式

生成的业务规范应包含：

1. 术语表
2. 业务模块结构（含职责和接口）
3. 通用业务模式（含流程图）
4. 核心实体关系（含关系图和定义）

## 验证清单

生成后验证：

- [ ] 术语表完整且定义清晰
- [ ] 模块划分合理且职责明确
- [ ] 通用模式有流程图
- [ ] 实体关系有关系图
- [ ] 所有实体都有TypeScript定义
