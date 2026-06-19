# Changelog

All notable changes to quality-gate-workflow will be documented in this file.

## [0.8.0.1] - 2026-06-19

### Fixed
- **health-check.sh**：`grep -oP` (PCRE) 改为 `grep -oE` (POSIX ERE)，兼容 macOS BSD grep
- **CI/CD**：shell-check job 移除 `|| true`，失败真正阻断；新增 powershell-check job；smoke-tests 增加 status 验证

### Changed
- SKILL.md 补齐 `category` / `triggers` / `integration` frontmatter
- 测试总数：103 → 115（新增 test_self_check.py 8 例 + CLI 集成测试 4 例）

---

## [0.8.0.0] - 2026-06-18

### Added - 生态升级（PRD 正向触发 + SKILL.md 拆分路由 + qgw-init + 测试框架 + 技能清单 + CI/CD + 垂直技能包）
- **PRD 正向触发**：`prd-changed` 子命令检测 PRD 变更并自动触发下游 Plan/Code 重验
- **Plan 微调**：`plan-tweak` 子命令支持 Gate 2 执行中轻量调整 Plan，无需全量重验 Gate 1
- **SKILL.md 拆分路由**：将 gate1/gate2/analyze/self-check 工作流拆分为独立 references，SKILL.md 只做路由入口
- **qgw-init 初始化技能**：7 步交互式引导 + 非交互脚本，支持平台选择、模式选择、.qgw/ 目录创建、health-check 验证
- **pytest 测试框架**：103 用例覆盖 gate-enforcer.py 全子命令和 Guard 转换规则
- **技能清单 manifest**：skill-manifest.json + generate-manifest.py 自动扫描生成
- **垂直技能包**：api-design-review（REST API 设计审查）、db-migration-gate（数据库迁移安全门禁）
- **CI/CD 增强**：quality-check.yml 8 个 job + release.yml 发布自动化 + qgw-pr-check.yml 可复用 PR 检查
- **技能间通信协议**：shared/skill-protocol.md + shared/vertical-skill-guide.md

### Fixed
- **hook-install.sh**：修复 heredoc 多行 JSON 嵌入 Python 单引号字符串导致的 SyntaxError，改为 Python 内部构建 dict
- **hook-install.sh**：修复 `hook_cmd` 与 entry.command 格式不一致导致 duplicate 检测永远失效的 bug
- **health-check.sh**：constitution 检查增加 `.qgw/constitution.md` 文件识别（v6.5 推荐方式），优先于 CLAUDE.md 内联声明

---

## [0.7.1.0] - 2026-06-18

### Added - Prompt 瘦身 + Phase 2/3 深度集成
- **Prompt 瘦身**（-312 行）：删除三处重复日志格式、抽离通用工作协议到 `general-protocols.md`、精简 --lite/P1-check/P4/S4/S5 章节
- **Gate 1 Guard 补全**：P2 `plan_scope_declared`、P3 `plan_coverage`、P4 `verifier_report_written`
- **Gate 2 Guard 补全**：S2.5 `boundary_valid`（git diff vs Plan Scope）、S3 `self_verify_documented`、S3.5 `db_schema_verified`、S5 增强 `plan_updated`
- **Resume 完善**：5 问题重启测试 + artifact 重验证 + RUNNING 步骤自动恢复 + 状态修复建议
- **Skip 矩阵完善**：--bug（`bug_clarity`→SKIP P1.7、`fix_lines`≤10→SKIP P2.5）、--opt（`no_prd_change`→SKIP P1.7）、S3 `has_sql`→SKIP S3.5
- **Checkpoint 格式统一**：新增 `gate`/`mode`/`step_order`/`feedback_rounds`/`meta` 字段
- **反馈回路硬执行**：`complete()` 也检查 feedback_rounds、CODE 根因独立计数（≤2 轮约束）
- **Boundary Check 集成**：`check_boundary_valid()` 读 git diff vs Plan Scope glob + forbidden 检测
- **Schema 验证**：`check_schema_valid()` 有 jsonschema 时完整验证，无时降级基本校验
- **self-check 子命令**：从引擎状态构建步骤覆盖矩阵、checkpoint 完整性、toolCallId 存在性
- **verify-checkpoint.sh Check 8**：引擎状态与验收数据一致性（S5/P5↔item、S4/P4↔verifierReports、feedback_rounds）
- **Debug/Audit Guard**：D1 `fix_criteria_documented`、D3 `self_verify_pass`、Audit D `audit_report_generated`
- **health-check.sh 完善**：Checkpoint 完整性检查 + gate-enforcer.py 语法检查
- **Debug/Audit .gate-state 多模式支持**

### Changed
- 反模式规则 58 → 58 条（无变化）
- gate1-workflow.md: 1146 → 939 行（-18%）
- gate2-workflow.md: 757 → 677 行（-11%）
- 新建 general-protocols.md（通用工作协议）

---

## [0.7.0.0] - 2026-06-18

### Added - 确定性执行引擎（Gate Enforcer）
- `gate-enforcer.py`：Python 状态机 + Guard 检查，将步骤顺序/产出物检查/toolCallId 验证从 prompt 指令提升为 if-else 机械强制
- 三层架构：LLM 语义层 + Gate Enforcer 状态机层 + 基础设施层（现有 hook/schema）
- 6 个命令接口：`init` / `enter` / `complete` / `fail` / `status` / `resume`
- Guard 转换规则：每步骤前置条件 if-else 硬检查，LLM 无法绕过
- toolCallId 格式强制验证：`Agent|<step>|ISO-timestamp`，禁止 `main|` 前缀
- Skip 矩阵：`--lite` 跳过 P1.5/P1.6/P1.7 由引擎 init 时确定，持久化后不可更改
- 内容驱动 skip：P1 complete 时 `has_backend=false` → 自动 SKIP P1.5
- P1-check 虚拟步骤：不做语义工作，只做 P1.5/P1.6/P1.7 决策状态聚合检查
- Checkpoint 文件写入：每步骤完成时写入 `docs/.qgw-checkpoints/<step>.json`
- 状态持久化：`docs/.qgw-engine-state.json`，可被 `--self` 和 `health-check.sh` 读取
- `.gate-state` 兼容写入：与现有 `verify-checkpoint.sh` 共存
- `health-check.sh` 第 13 项检查：引擎状态文件存在性和进度一致性
- `project-config.md` 新增 `engine` 配置节：`enabled` / `strict_mode` / `state_file` / `checkpoint_dir`
- 反模式 #58：gate-enforcer BLOCK 时禁止继续执行
- SKILL.md 新增红线 + 合理化借口表条目

### Changed
- 反模式规则 57 → 58 条（新增 #58）
- Gate 1/Gate 2 每个步骤追加引擎交互指令（`enter` / `complete`）
- Debug 模式 D1-D4 追加引擎交互指令

---

## [0.6.0.0] - 2026-06-18

### Added - 文档全生命周期管理系统
- PRD 目录化规范：PRD 必须是目录，支持 images/tables/attachments/proposals 子目录
- 全内容解析规则：Gate 1 P1 必须处理文字+图片+表格+附件，输出交叉验证矩阵
- PRD 修订工作流 RV1-RV5：提案→影响分析→人工审批（强制）→执行→下游同步
- 变更传播规则 CP-1~CP-5：PRD/Plan/Code/Report/ErrorPattern 变更强制下游同步
- Plan 结构重设计：按 PRD §X.X 章节分组（`ch-{X.X}-{name}/`），共享基础设施分离到 `03-shared-infra.md`
- Report 生命周期集成：8 种报告嵌入工作流节点（completeness/gate1-verifier/audit/debug/analyze/self-check/prd-impact/regression）
- 报告强制注册：每个报告必须注册到 `reports/INDEX.md` 和 `QGW-INDEX.md`
- acceptance-criteria-schema.json 增强：新增 `chapter`、`prdSection`、`prdAssets` 字段

### Changed
- 反模式规则 48 → 57 条（新增 #49-#57）
- Plan 强制迁移：发现旧格式直接重构为章节式，不向后兼容
- 反模式 #9 升级：PRD 全内容解析强制要求，PRD 必须目录格式

---

## [0.5.0.0] - 2026-06-18

> **版本号说明**：从 v1.1.0 降级至 v0.5.0.0。采用 4 级版本号（Major.Minor.Patch.Iteration），
> Major=0 表示项目仍在活跃开发期，架构尚未冻结。

### Added - 开箱即用改造
- `--auto` 智能推断模式：零参数触发，自动识别意图并建议参数
- Preset 预设包：quickfix / feature / hotfix / review / audit / minimal 6 个场景化快捷入口
- first-run-guide.md：首次使用引导 + 智能推断规则详解
- 渐进式披露重构 SKILL.md：快速开始 → 常用参数 → 全部参数 → 深度参考
- 安装脚本 `--init` 一键安装 + `--dry-run` 预览模式
- 错误输出人性化：反模式检测改为人类可读格式（描述+原因+建议）
- skill-optimizer 新增 `--optimize` 参数式触发
- 支持自定义 Preset（`.qgw/config.json` presets 字段）

### Added - 初始发布
- 质量门禁工作流：Gate 1（需求→Plan）+ Gate 2（Plan→代码）全链路验证
- 五层防线：验收标准提取 → PM 顾问评议 → Plan 撰写 → 架构师顾问评议 → 独立 verifier 验证
- 参数式触发：`--gate1` / `--gate2` / `--all` / `--self` / `--analyze`
- 模式支持：PRD / Bug / Optimization / Implementation / Audit / Debug
- 修饰参数：`--strict` / `--lite` / `--incremental` / `--e2e` / `--fix`
- 结构化需求澄清（多选题模式）
- Boundary Enforcement（变更范围检查）
- 增量验证（`--incremental`）
- Git Trailer 可追溯性
- Cross-Artifact 一致性分析（`--analyze`）
- E2E 行为验证（`--e2e`）
- CROSS-CUTTING 横切检查清单（6 项）
- 文档生命周期：Master Index + Session Summary + Plan 版本化
- Knowledge Compounding 自进化机制
- 结构化日志格式
- 多平台支持：Claude Code / Codex / OpenCode / MiMoCode / 通用
- 48 条反模式规则 + 合理化借口反驳清单
- 评估框架（5 个场景 + 5 个指标）
- 回归测试用例集（10 个 RC）

### Changed
- 版本号方案变更：SemVer 3 级 → 4 级（Major.Minor.Patch.Iteration）
- 版本降级：1.1.0 → 0.5.0.0（明确传达活跃开发状态）

---

## [1.0.0] - 2026-06-18 *(已合并至 0.5.0.0)*

### Added
- 初始开源发布
- 质量门禁工作流：Gate 1（需求→Plan）+ Gate 2（Plan→代码）全链路验证
- 五层防线：验收标准提取 → PM 顾问评议 → Plan 撰写 → 架构师顾问评议 → 独立 verifier 验证
- 参数式触发：`--gate1` / `--gate2` / `--all` / `--self` / `--analyze`
- 模式支持：PRD / Bug / Optimization / Implementation / Audit / Debug
- 修饰参数：`--strict` / `--lite` / `--incremental` / `--e2e` / `--fix`
- 结构化需求澄清（多选题模式）
- Boundary Enforcement（变更范围检查）
- 增量验证（`--incremental`）
- Git Trailer 可追溯性
- Cross-Artifact 一致性分析（`--analyze`）
- E2E 行为验证（`--e2e`）
- CROSS-CUTTING 横切检查清单（6 项）
- 文档生命周期：Master Index + Session Summary + Plan 版本化
- Knowledge Compounding 自进化机制
- 结构化日志格式
- 多平台支持：Claude Code / Codex / OpenCode / MiMoCode / 通用
- 46 条反模式规则 + 合理化借口反驳清单
- 评估框架（5 个场景 + 5 个指标）
- 回归测试用例集（10 个 RC）
