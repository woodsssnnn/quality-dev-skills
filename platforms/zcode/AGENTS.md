# ZCode 平台适配

## 安装（推荐：构建自包含插件）

ZCode 安装插件时会把插件目录拷贝进缓存，插件内引用外部相对路径的声明在
缓存副本中会失效——所以先构建自包含插件：

```bash
cd <本仓库根目录>
python scripts/build-zcode-plugin.py
```

产出 `dist/`（已 gitignore）：

```
dist/
├── marketplace.json          ← 市场清单（含下面两个插件）
├── zcode-quality-skills/     ← 技能插件（skills 自包含副本）
└── zcode-governance/         ← 代码级门禁运行时插件（hooks/agents）
```

然后在 ZCode 里添加本地市场并安装：

```
/plugin marketplace add <仓库根目录的绝对路径>/dist
```

装完后技能由模型按 description 触发；governance 的 PostToolUse 门禁即时生效
（规则三层发现：项目 `.qgw/` > 领域包 > 内置中立规则）。

## 更新 / 卸载

```bash
git pull && python scripts/build-zcode-plugin.py   # 重新构建后按上面再装
# 卸载走 ZCode 插件管理界面（/plugin）
```

## 仓库内直连（实验性）

仓库根 `marketplace.json` 也包含本适配器条目（source: `./platforms/zcode`，
skills 以相对路径指向仓库 `skills/`），供支持原地加载的场景试用；若安装后
技能未出现，说明宿主做了缓存拷贝——请改用上面的 dist 构建方式。

## 相关

- 治理运行时细节：[governance/README.md](../../governance/README.md)
- 领域包机制：[shared/domain-pack-spec.md](../../shared/domain-pack-spec.md)
- 项目装配（hook 写入项目 `.zcode/settings.json`）：
  `node <仓库>/governance/scripts/install-hooks.js`（在目标项目根执行）
