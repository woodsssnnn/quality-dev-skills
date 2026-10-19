# Security Policy / 安全策略

## Supported Versions / 支持的版本

| Version | Supported |
|---------|-----------|
| 0.9.x | ✅ |
| < 0.9 | ❌ |

## Reporting a Vulnerability / 报告漏洞

**Do not open a public issue for security vulnerabilities.**
**请不要用公开 Issue 报告安全漏洞。**

Please report privately via:

- GitHub: use **Report a vulnerability** (Security → Advisories) on the repository
- Or contact the maintainer directly through the hosting platform

You should receive a response within 72 hours. Please include:

- The affected file(s) and reproduction steps
- Impact assessment (what an attacker could achieve)
- A suggested fix if you have one

We credit reporters in release notes unless anonymity is requested.

## Scope Notes / 范围说明

- The governance runtime is designed with **tamper-evidence, not tamper-proofing**:
  the event stream uses a SHA-256 hash chain and the runtime verifies itself against
  an install-time snapshot (`integrity-check.js --self-test`). An attacker with write
  access to both can theoretically recompute them — treat host-level compromise as
  out of scope.
- The repository enforces a **no-credentials policy**: secrets must never be committed
  (CI-level banned-terms scan + `secret-leaks` runtime rule). Leaked credentials in
  history should be rotated immediately, not merely deleted.
- Domain packs are community-contributed and execute rules you configure — review a
  pack's rule sets before enabling it (`python scripts/validate-domain-pack.py`).

## Disclosure Policy / 披露策略

Once a fix is released, the vulnerability will be disclosed in the changelog with
credit to the reporter. We ask for a 90-day coordinated-disclosure window.
