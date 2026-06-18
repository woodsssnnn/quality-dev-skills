# Gate 1 Constitution 模板

## 什么是 Constitution

Constitution 是项目级的需求解析规则。当 Gate 1 从 PRD 提取可验证项时，除了逐字段提取外，还要检查这些项目级约束是否被遵守。

Constitution 防止的是：需求本身没有歧义，但项目有隐含的业务规则或技术约束，代理不知道就忽略了。

## 声明方式（二选一）

### 方式 A：CLAUDE.md 声明（传统）

在项目 CLAUDE.md 中添加：

```markdown
**Gate 1 项目 constitution**：
- 审批/废止表单是双映射机制，新增字段必须两边都加
- T_PATH 匹配必须带 del_state=0 条件
- 报表数据范围必须用 T_PATH 前缀匹配，不能仅用 ORG_ID
- JPA 原生查询数值类型用 Number 接收
- 流程穿透 SQL 别名用 snake_case，前端递归转 camelCase
- useRequest 必须 manual:false + ready 模式
- 前端禁止 theme.useToken()（antd v4 项目）
```

### 方式 B：`.qgw/constitution.md` 文件（推荐）

在项目根目录创建 `.qgw/constitution.md`：

```markdown
# Project Constitution

## 需求解析约束
- 审批/废止表单是双映射机制，新增字段必须两边都加
- T_PATH 匹配必须带 del_state=0 条件

## 编码规范
- JPA 原生查询数值类型用 Number 接收
- 前端禁止 theme.useToken()（antd v4 项目）

## 架构约束
- 流程穿透 SQL 别名用 snake_case，前端递归转 camelCase
```

**优先级**：`.qgw/constitution.md` > CLAUDE.md `gate1_constitution` > 无 constitution

## 如何发现需要添加的 Constitution

当 verifier 多次发现同类型的 PLAN 根因时（如"又忘了审批/废止双映射"），说明项目有一个隐含规则没被显式声明。此时：

1. 将规则添加到 `.qgw/constitution.md` 或项目 CLAUDE.md 的 `gate1_constitution` 中
2. 后续 Gate 1 在 P1 阶段自动检查该规则

## 与 gate2_dev_rules 的区别

| 配置 | 检查阶段 | 检查内容 |
|------|---------|---------|
| constitution | Gate 1 P1 | 需求解析时的隐含业务规则 |
| gate2_dev_rules | Gate 2 Step 4 | 代码实现时的编码规范 |
