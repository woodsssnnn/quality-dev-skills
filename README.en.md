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

## Acknowledgments

This project's design and implementation draw from the ideas and practices of the following open source projects. We extend our sincere gratitude to all contributors:

| Project | Borrowed Concepts | Applied In |
|---------|------------------|------------|
| **[planning-with-files](https://github.com/nicepkg/planning-with-files)** | 5-Question Restart Test, 2-Action Rule, 3-Strike Error Protocol | General Protocols (`general-protocols.md`), session recovery |
| **[Spec Kit](https://github.com/nicepkg/spec-kit)** | `/speckit.clarify` structured clarification, `/speckit.analyze` cross-analysis | Requirements clarification (multi-choice mode), `--analyze` cross-artifact analysis |
| **[agent-spec](https://github.com/nicepkg/agent-spec)** | Boundary enforcement, `stamp` command | Gate 2 Step 2.5 scope checking, Git Trailer traceability |
| **[Autonoma](https://github.com/nicepkg/autonoma)** | Agentic testing (static + dynamic dual-layer verification) | Gate 2 S4 static verification + S4.5 E2E behavior verification |
| **[Ponytail](https://github.com/nicepkg/ponytail)** | YAGNI checklist | PM Advisor D6 dimension: feature necessity, stdlib alternatives, native feature alternatives |
| **[OpenSpec](https://github.com/nicepkg/openspec)** | Delta specs (describe only changes) | `--incremental` incremental verification mode |
| **[Python](https://www.python.org/)** | Python 3 standard library | gate-enforcer.py, evaluate.py, verify-checkpoint.sh JSON parsing & state machine |
| **[JSON Schema](https://json-schema.org/)** | JSON Schema Draft-07 | acceptance-criteria-schema.json acceptance criteria format |

### Platform Ecosystem Acknowledgments

Multi-platform support is made possible by the open ecosystems of:

- **[Claude Code](https://claude.ai/)** (Anthropic) — Hooks mechanism, SKILL.md specification
- **[Codex](https://openai.com/)** (OpenAI) — Server plugin architecture
- **[OpenCode](https://github.com/opencode)** — Server plugin interface
- **[MiMoCode](https://mimo.org/)** — Plugin installation specification

> Core philosophy: distill community best practices into reusable AI skills, so every developer can stand on the shoulders of giants.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
