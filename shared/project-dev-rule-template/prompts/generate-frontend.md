# 前端规范生成指南

## 目的

指导AI根据项目技术栈生成前端开发规范。

## 输入要求

AI需要收集以下信息：

### 1. 技术栈

- 框架：React / Vue / Angular / Next.js / Nuxt.js 等
- UI库：antd / element-ui / material-ui / Tailwind CSS 等
- 状态管理：Redux / Vuex / MobX / Zustand 等
- 样式方案：CSS Modules / styled-components / Tailwind / SASS 等

### 2. 项目类型

- 浏览器端（Browser）
- 移动端（Mobile）
- 设计端（Designer）
- 管理后台（Admin）

### 3. 基线仓库

- 是否有基线仓库：是 / 否
- 基线仓库路径：[如有]
- 基线UI库版本：[如有]

## 生成内容

### 1. 目录结构规范

```markdown
## 目录结构

[项目名称]前端采用[框架]，目录结构如下：

```
project-name/
├── src/
│   ├── components/          # 通用组件
│   │   ├── Button/
│   │   │   ├── index.tsx
│   │   │   ├── index.module.css
│   │   │   └── index.test.tsx
│   │   └── ...
│   ├── pages/               # 页面组件
│   │   ├── Home/
│   │   │   ├── index.tsx
│   │   │   ├── index.module.css
│   │   │   └── index.test.tsx
│   │   └── ...
│   ├── layouts/             # 布局组件
│   ├── hooks/               # 自定义hooks
│   ├── utils/               # 工具函数
│   ├── services/            # API服务
│   ├── stores/              # 状态管理
│   ├── types/               # TypeScript类型
│   ├── constants/           # 常量
│   └── styles/              # 全局样式
├── public/
├── package.json
└── tsconfig.json
```
```

### 2. 组件规范

```markdown
## 组件规范

### 组件文件结构
```
ComponentName/
├── index.tsx              # 组件主文件
├── index.module.css       # 样式文件
├── index.test.tsx         # 测试文件
├── index.stories.tsx      # Storybook（可选）
└── types.ts               # 类型定义（可选）
```

### 组件命名
| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 页面组件 | [功能]Page | UserPage |
| 业务组件 | [功能]Component | UserForm |
| 通用组件 | [名称]Component | ButtonComponent |

### 组件模板
```tsx
import React from 'react';
import styles from './index.module.css';

interface Props {
  // props定义
}

const ComponentName: React.FC<Props> = ({ prop1, prop2 }) => {
  // hooks
  
  // 事件处理
  
  // 渲染
  return (
    <div className={styles.container}>
      {/* 内容 */}
    </div>
  );
};

export default ComponentName;
```

### Props规范
1. 使用interface定义Props
2. 必需属性在前，可选属性在后
3. 复杂类型单独定义
4. 回调函数以on开头
```

### 3. 状态管理规范

```markdown
## 状态管理规范

### 状态分类
| 类型 | 说明 | 存储位置 |
|------|------|----------|
| 全局状态 | 应用级状态 | Store |
| 页面状态 | 页面级状态 | useState |
| 组件状态 | 组件级状态 | useState |
| 服务端状态 | API数据 | React Query / SWR |

### 状态管理原则
1. 最小化全局状态
2. 派生状态使用useMemo
3. 副作用使用useEffect
4. 复杂状态使用useReducer

### Store结构
```typescript
// stores/userStore.ts
interface UserState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface UserActions {
  fetchUser: (id: string) => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  clearUser: () => void;
}
```
```

### 4. 样式规范

```markdown
## 样式规范

### 样式方案选择
| 方案 | 适用场景 | 优缺点 |
|------|----------|--------|
| CSS Modules | 组件级样式 | 局部作用域，无全局污染 |
| styled-components | 动态样式 | CSS-in-JS，运行时开销 |
| Tailwind CSS | 快速开发 | 原子化CSS，体积大 |

### 命名规范
- 类名使用camelCase：`container`, `userCard`
- 修饰符使用`--`：`button--primary`
- 状态使用`is`前缀：`isActive`, `isLoading`

### 样式组织
```css
/* index.module.css */
.container {
  /* 布局样式 */
}

.title {
  /* 标题样式 */
}

/* 响应式 */
@media (max-width: 768px) {
  .container {
    /* 移动端样式 */
  }
}
```

### 主题配置
```typescript
// theme.ts
export const theme = {
  colors: {
    primary: '#1890ff',
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
};
```
```

### 5. 性能优化规范

```markdown
## 性能优化规范

### 渲染优化
1. 使用React.memo避免不必要的渲染
2. 使用useMemo缓存计算结果
3. 使用useCallback缓存函数引用
4. 虚拟滚动处理长列表

### 代码分割
```tsx
// 路由级代码分割
const UserPage = React.lazy(() => import('./pages/User'));

// 组件级代码分割
const HeavyComponent = React.lazy(() => import('./components/Heavy'));
```

### 图片优化
1. 使用懒加载
2. 使用WebP格式
3. 响应式图片
4. CDN加速

### 网络优化
1. 请求合并
2. 数据缓存
3. 预加载
4. 懒加载
```

### 6. 测试规范

```markdown
## 测试规范

### 测试分类
| 类型 | 说明 | 工具 |
|------|------|------|
| 单元测试 | 组件/函数测试 | Jest, React Testing Library |
| 集成测试 | 组件交互测试 | Cypress, Playwright |
| E2E测试 | 端到端测试 | Cypress, Playwright |

### 测试命名
- 测试文件：[组件名].test.tsx
- 测试描述：describe('[组件名]')
- 测试用例：it('[场景] [预期结果]')

### 测试示例
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import Button from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```
```

## 输出格式

生成的前端规范应包含：

1. 目录结构规范
2. 组件规范（含模板）
3. 状态管理规范
4. 样式规范
5. 性能优化规范
6. 测试规范

## 验证清单

生成后验证：

- [ ] 目录结构清晰
- [ ] 组件规范有模板代码
- [ ] 状态管理有分类说明
- [ ] 样式规范有命名规则
- [ ] 性能优化有具体措施
- [ ] 测试规范有示例代码
