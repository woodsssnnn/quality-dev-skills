# Changelog

All notable changes to quality-gate-workflow will be documented in this file.

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
