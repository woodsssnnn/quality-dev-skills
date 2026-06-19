# 简易 TODO List — 前后端协同需求

## §1 概述
为测试项目开发简易 TODO List 功能，覆盖前后端协同全链路。

## §2 后端 API
| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建 TODO | POST | /api/todos | title（必填 max 200字）、description（选填）|
| 查询列表 | GET | /api/todos | status 筛选（all/pending/done），分页 page=1 size=20 |
| 更新状态 | PATCH | /api/todos/{id} | status（pending/done），返回更新后对象 |
| 删除 | DELETE | /api/todos/{id} | 逻辑删除 is_deleted=1 |

## §3 数据模型
表名：todo_item
| 字段 | 类型 | 约束 |
|------|------|------|
| id | varchar(64) | PK |
| title | varchar(200) | NOT NULL |
| description | text | NULL |
| status | varchar(20) | DEFAULT 'pending' |
| is_deleted | tinyint | DEFAULT 0 |
| created_at | datetime | NOT NULL |
| updated_at | datetime | NOT NULL |

## §4 前端页面
- TODO 列表页（/todos）：新建按钮 + 筛选 + 列表 + 空状态
- 新建弹窗：title 必填 + description 选填 + 校验 + toast

## §5 技术约束
- 后端：Java + Spring Boot + MyBatis + Liquibase
- 前端：React + antd + TypeScript
