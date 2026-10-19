# quality-dev-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/woodsssnnn/quality-dev-skills/actions/workflows/quality-check.yml/badge.svg)](https://github.com/woodsssnnn/quality-dev-skills/actions/workflows/quality-check.yml)
[![version](https://img.shields.io/badge/version-0.9.0.x-1f6feb)](version.json)
[![skills](https://img.shields.io/badge/skills-6-238636)](skills/)
[![platforms](https://img.shields.io/badge/platforms-6-8957e5)](platforms/)

English | [中文](README.md)

Universal AI skills repository — a **code-governance runtime**, process-level quality gate workflow, skill optimization framework, and an open domain-pack mechanism, reusable by any project. The repo stays neutral: zero domain-specific content.

![Three-layer governance architecture](docs/figures/architecture.svg)

[Contributing](CONTRIBUTING.md) | [Code of Conduct](CODE_OF_CONDUCT.md) | [Security](SECURITY.md) | [Changelog](CHANGELOG.md) | [MIT License](LICENSE)

## Why

The biggest trust problem in AI pair programming: **the agent claims it did the job right — how do you prove it?** This repo answers with two layers:

- **governance runtime (invisible layer)** — active the moment it's installed, never invoked by hand. Every file write is checked against red-line rules (hardcoded secrets get blocked until fixed), local verification runs leave machine receipts, and repeatedly-made mistakes trigger real-time reminders. All you see is "the agent fixed itself".
- **Skills (process layer)** — semi-automatic, triggered by natural intent ("run the quality gate"). Full requirements-to-code traceability: 1:1 PRD parsing → acceptance-criteria extraction → plan gate → independent verification → reports.

| Without it | With it |
|------------|---------|
| Agent says "verified" (but never ran it) | Machine receipts cross-checking conclusion vs exit code — `--verify-last` exposes the lie |
| Hardcoded passwords/keys land in the repo | Blocked at write time |
| Editing a contract field silently breaks consumers | Auto-hint to grep all consumers first |
| The same mistake repeats across sessions | Event stream tracks frequency; repeat violations get flagged live |
| PRD details get lost in translation to code | Acceptance-criteria extraction + dual gates + independent verifier |
| Team conventions live in a wiki nobody reads | Rules are data files; violations are blocked |

In one sentence: **turn "the AI says it's done right" into "the machine proves it".**

## Included Skills

| Skill | Description |
|-------|-------------|
| `quality-gate-workflow` | Quality gate workflow (requirements → plan → code, process level) |
| `skill-optimizer` | Automated skill optimization framework |
| `prd-parse` | Lossless 1:1 parsing of raw requirement docs (pdf/doc/docx/xlsx/xls/html → Markdown) |
| `api-design-review` / `db-migration-gate` | Vertical skill packs (API design review / DB migration gate) |

## Governance Runtime (`governance/`)

The code-level gate complementing skills (which load at the model's discretion): PostToolUse
declarative rule checking (block violations exit 2, forcing the agent to fix and continue),
machine receipts for local verification (DoD audit chain), a SHA-256 hash-chained event
stream, SessionStart integrity self-check, and knowledge distillation (incremental
watermark + human review gate). All rules and config are declarative with three-layer
discovery — see [governance/README.md](governance/README.md).

## Domain Packs (`domains/`)

The open mechanism for a stack/team to plug its own gating rules into the governance
runtime — this repo ships only the contract, template, scaffolding and validator;
domain content is community-contributed. See
[shared/domain-pack-spec.md](shared/domain-pack-spec.md) and
[domains/_template/](domains/_template/).

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

See [INSTALL.md](INSTALL.md) for the detailed guide.

## Project Integration

This repository is the **Base Layer** — fully independent, no project dependencies.

### Three-Layer Architecture

```
Project    target project: .qgw/ overrides (highest priority) + AGENTS.md + project-dev-rule (AI-generated)
Domain     domains/<pack>/ (community) or .qgw/packs/<pack>/ (private) — declarative rules/hints/verify conventions
Base       quality-dev-skills:
           ├── governance/            code-level governance runtime (hooks + rule engine + event stream)
           ├── skills/                process-level quality gates + skill optimizer + prd-parse
           └── shared/                skill templates + domain-pack contract + protocols
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

| Platform | Adapter | Installation |
|----------|---------|-------------|
| **Claude Code** | `platforms/claude-code/` | Plugin install |
| **Codex** | `platforms/codex/` | Plugin install |
| **OpenCode** | `platforms/opencode/` | Server plugin |
| **MiMoCode** | `platforms/minicode/` | Plugin install |
| **ZCode** | `platforms/zcode/` | Plugin marketplace (`python scripts/build-zcode-plugin.py`, then `/plugin marketplace add <repo>/dist`) |
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

- **[Claude Code](https://claude.ai/)** (Anthropic) — Hooks mechanism, SKILL.md specification
- **[Codex](https://openai.com/)** (OpenAI) — Server plugin architecture
- **[OpenCode](https://github.com/opencode)** — Server plugin interface
- **[MiMoCode](https://mimo.org/)** — Plugin installation specification

> Core philosophy: distill community best practices into reusable AI skills, so every developer can stand on the shoulders of giants.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — including the [domain-pack contribution](CONTRIBUTING.md#贡献领域包domain-pack) guide.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
