# quality-dev-skills

[English](#) | [中文](README.md)

Universal AI skills repository. Provides quality gate workflow, skill optimization framework, and project skill templates — reusable by any project.

## Included Skills

| Skill | Description |
|-------|-------------|
| `quality-gate-workflow` | Quality gate workflow (Requirements → Plan → Code full-chain verification) |
| `skill-optimizer` | Automated skill optimization framework |

## Templates

| Template | Description |
|----------|-------------|
| `project-dev-rule-template` | Project development rules skill template (AI-generated in session) |

## Installation

### Linux / macOS / Git Bash

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
bash scripts/install.sh
```

### Windows PowerShell

```powershell
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
.\scripts\install.ps1
```

See [INSTALL.md](INSTALL.md) for detailed installation guide.

## Project Integration

This repository is the **Base Layer** — fully independent, no project dependencies.

### Dual-Layer Architecture

```
Base Layer (quality-dev-skills)        Project Layer (project-dev-skills)
├── quality-gate-workflow              ├── project-dev-rule (AI-generated)
├── skill-optimizer                    └── project-deploy
└── project-dev-rule-template/
```

### Project Skill Generation

1. Start an AI session in your project workspace
2. Read `shared/project-dev-rule-template/INDEX.md`
3. AI generates `project-dev-rule` based on template + project context
4. Update `CLAUDE.md` / `AGENTS.md` constraints

### Project Overrides

Projects customize via `.qgw/` override directory — no base layer files modified.

## Version Management

```bash
# Check current version
cat version.json | grep version

# Check compatibility
bash scripts/check-compatibility.sh -t 1.0.0 -p 1.0.0

# Update project skill
bash scripts/update-project-skill.sh /path/to/project
```

## Multi-Platform Support

Supports multiple AI coding assistant platforms:

| Platform | Adapter | Installation |
|----------|---------|-------------|
| **Claude Code** | `platforms/claude-code/` | Plugin install |
| **Codex** | `platforms/codex/` | Plugin install |
| **OpenCode** | `platforms/opencode/` | Server plugin |
| **MiMoCode** | `platforms/minocode/` | Plugin install |
| **Universal** | `platforms/general/AGENTS.md` | Copy AGENTS.md |

## Update

```bash
cd ~/quality-dev-skills
git pull
bash scripts/install.sh --update
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
