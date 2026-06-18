# 后端规范生成指南

## 目的

指导AI根据项目技术栈生成后端开发规范。

## 输入要求

AI需要收集以下信息：

### 1. 技术栈

- 编程语言：Java / Kotlin / Go / Node.js / Python 等
- 框架：Spring Boot / Django / Express / Gin 等
- 数据库：MySQL / PostgreSQL / MongoDB / Redis 等
- ORM：MyBatis / JPA / SQLAlchemy / GORM 等

### 2. 架构模式

- DDD（领域驱动设计）
- CQRS（命令查询职责分离）
- MVC（模型-视图-控制器）
- Clean Architecture（整洁架构）
- 其他：[项目特定]

### 3. 基线仓库

- 是否有基线仓库：是 / 否
- 基线仓库路径：[如有]
- 基线技术栈：[如有]

## 生成内容

### 1. 目录结构规范

```markdown
## 目录结构

[项目名称]后端采用[架构模式]，目录结构如下：

```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── company/
│   │   │           └── project/
│   │   │               ├── controller/    # 控制器层
│   │   │               ├── service/       # 服务层
│   │   │               ├── repository/    # 仓库层
│   │   │               ├── domain/        # 领域层
│   │   │               ├── dto/           # 数据传输对象
│   │   │               ├── entity/        # 实体
│   │   │               ├── config/        # 配置
│   │   │               ├── exception/     # 异常
│   │   │               └── util/          # 工具类
│   │   └── resources/
│   │       ├── application.yml
│   │       └── mapper/                    # MyBatis映射文件
│   └── test/
└── pom.xml
```
```

### 2. 分层规范

```markdown
## 分层规范

### Controller层
- 职责：接收HTTP请求，参数校验，调用Service
- 命名：[Name]Controller
- 示例：
  ```java
  @RestController
  @RequestMapping("/api/users")
  public class UserController {
      @Autowired
      private UserService userService;
      
      @GetMapping("/{id}")
      public Result<UserDTO> getUser(@PathVariable Long id) {
          return Result.success(userService.getUser(id));
      }
  }
  ```

### Service层
- 职责：业务逻辑处理，事务管理
- 命名：[Name]Service / [Name]ServiceImpl
- 示例：
  ```java
  @Service
  @Transactional
  public class UserServiceImpl implements UserService {
      @Autowired
      private UserRepository userRepository;
      
      @Override
      public UserDTO getUser(Long id) {
          User user = userRepository.findById(id)
              .orElseThrow(() -> new BusinessException("用户不存在"));
          return convertToDTO(user);
      }
  }
  ```

### Repository层
- 职责：数据访问，SQL映射
- 命名：[Name]Repository / [Name]Mapper
- 示例：
  ```java
  @Repository
  public interface UserRepository extends JpaRepository<User, Long> {
      Optional<User> findByUsername(String username);
  }
  ```
```

### 3. 命名规范

```markdown
## 命名规范

### 类命名
| 类型 | 命名规则 | 示例 |
|------|----------|------|
| Controller | [实体]Controller | UserController |
| Service | [实体]Service | UserService |
| Repository | [实体]Repository | UserRepository |
| Entity | [实体] | User |
| DTO | [实体]DTO | UserDTO |
| Exception | [描述]Exception | BusinessException |

### 方法命名
| 操作 | 命名规则 | 示例 |
|------|----------|------|
| 查询单个 | get[实体] | getUser |
| 查询列表 | list[实体] | listUsers |
| 创建 | create[实体] | createUser |
| 更新 | update[实体] | updateUser |
| 删除 | delete[实体] | deleteUser |

### 变量命名
| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 控制器 | [实体]Controller | userController |
| 服务 | [实体]Service | userService |
| 仓库 | [实体]Repository | userRepository |
| 实体 | [实体] | user |
| DTO | [实体]DTO | userDTO |
```

### 4. 异常处理规范

```markdown
## 异常处理规范

### 异常分类
| 类型 | 说明 | 示例 |
|------|------|------|
| BusinessException | 业务异常 | 用户不存在 |
| SystemException | 系统异常 | 数据库连接失败 |
| ValidationException | 参数校验异常 | 参数格式错误 |

### 异常处理原则
1. Controller层捕获所有异常，统一返回Result
2. Service层只抛出业务异常
3. Repository层不捕获异常，直接向上抛出

### 示例
```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BusinessException.class)
    public Result<?> handleBusinessException(BusinessException e) {
        return Result.fail(e.getCode(), e.getMessage());
    }
    
    @ExceptionHandler(Exception.class)
    public Result<?> handleException(Exception e) {
        log.error("系统异常", e);
        return Result.fail(500, "系统异常");
    }
}
```
```

### 5. 日志规范

```markdown
## 日志规范

### 日志级别
| 级别 | 使用场景 |
|------|----------|
| ERROR | 系统错误、异常 |
| WARN | 警告信息 |
| INFO | 关键业务流程 |
| DEBUG | 调试信息 |

### 日志格式
```
[时间] [级别] [类名] [方法名] - 日志内容
```

### 日志规范
1. Controller层记录请求入口
2. Service层记录关键业务操作
3. 异常必须记录完整堆栈
4. 敏感信息（密码、token）不记录
```

### 6. 测试规范

```markdown
## 测试规范

### 测试分类
| 类型 | 说明 | 工具 |
|------|------|------|
| 单元测试 | 方法级别测试 | JUnit, Mockito |
| 集成测试 | 模块间交互测试 | Spring Boot Test |
| API测试 | 接口级别测试 | MockMvc |

### 测试命名
- 测试类：[被测类]Test
- 测试方法：test[方法名]_[场景]_[预期结果]

### 测试覆盖率
- 核心业务逻辑：≥80%
- 工具类：≥90%
- 控制器：≥70%
```

## 输出格式

生成的后端规范应包含：

1. 目录结构规范
2. 分层规范（含代码示例）
3. 命名规范（含表格）
4. 异常处理规范（含代码示例）
5. 日志规范
6. 测试规范

## 验证清单

生成后验证：

- [ ] 所有规范都有代码示例
- [ ] 命名规范有表格说明
- [ ] 异常处理有完整示例
- [ ] 测试规范有覆盖率要求
