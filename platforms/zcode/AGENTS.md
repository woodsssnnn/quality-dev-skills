# ZCode 平台适配

## 安装

### 方式一：GitHub 一等公民（推荐，整仓即插件）

仓库根本身就是一个自包含插件（双清单 `.zcode-plugin/` + `.claude-plugin/`，
技能/hooks/agents 全部指向仓库内路径）。在 ZCode 插件市场的"添加插件市场"
输入 GitHub 地址即可：

```
woodsssnnn/quality-dev-skills
```

也可用 Git URL 形式（任一托管源均可）：

```
https://github.com/woodsssnnn/quality-dev-skills.git
https://gitcode.com/songnan/quality-dev-skills.git
```

装上即得全家桶：6 个技能 + governance 代码门禁运行时（hooks 即时生效）+
3 个 agent 模板。**Claude Code 用户同样适用**（同源市场机制）。

### 方式二：本地 dist 构建（拆分安装：仅技能 / 仅治理）

```bash
python scripts/build-zcode-plugin.py
```

产出 `dist/`（已 gitignore）含市场清单 + 两个**独立**插件
（zcode-quality-skills / zcode-governance），然后：

```
/plugin marketplace add <仓库根目录>/dist
```

> 同一环境不要同时装"全家桶"与独立的 governance 插件——hooks 会双跑。

## 已知边界

- **hooks 命令当前为 Windows 优先**（`.cmd` 包装）。mac/linux 下技能与
  agents 可用，hooks 跨平台适配是待办（坑：ZCode 下带引号的
  `${CLAUDE_PLUGIN_ROOT}` 不展开，需实验定稿）
- 根 `hooks/hooks.json` 是**适配层**（实现唯一原则）：只做注册转发，
  实现全部在 `governance/hooks/` 下

## 更新 / 卸载

```bash
# 更新：市场管理里更新插件，或删市场重加（GitHub 源拉取最新 main）
# 卸载：ZCode 插件管理界面移除
```

## 相关

- 治理运行时细节：[governance/README.md](../../governance/README.md)
- 领域包机制：[shared/domain-pack-spec.md](../../shared/domain-pack-spec.md)
- 项目装配（hook 写入项目 `.zcode/settings.json`，非全局插件方式）：
  `node <仓库>/governance/scripts/install-hooks.js`（在目标项目根执行）
