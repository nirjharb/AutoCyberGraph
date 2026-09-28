# Contributing to AutoCyberGraph

Thanks for your interest in connecting automotive cybersecurity risk to reality!

## Ground rules

1. **No compliance claims.** AutoCyberGraph is an engineering and evidence-management
   platform. PRs that position it as a certification tool, legal advice, or official
   implementation of ISO/SAE 21434, UNECE R155/R156, NIST SP 800-53 or AUTOSAR will be rejected.
   Reference standards — never reproduce their text.
2. **No placeholder work.** No fake dashboards, fake AI responses, or dead buttons.
3. **Honest documentation.** If a feature is a prototype or simplified, say so.

## Development setup

```bash
git clone https://github.com/autocybergraph/autocybergraph
cd autocybergraph
bash scripts/seed.sh        # create + seed the local database
bash scripts/dev.sh         # API + frontend at http://localhost:8000
```

Frontend dev server with hot reload:

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173 (proxies /api)
```

## Workflow

1. Fork and create a feature branch (`feat/short-description`)
2. Follow `PLAN → BUILD → RUN → TEST → FIX → DOCUMENT`
3. Run `bash scripts/test-all.sh` before pushing
4. Open a PR using the template; link related issues
5. Record notable engineering decisions in `DECISIONS.md`

## Code style

- **Backend:** Python 3.11+, type hints, Pydantic v2, SQLAlchemy 2.0 typing; `ruff check` clean
- **Frontend:** TypeScript strict-ish, function components, TanStack Query for server state
- **Tests:** every new domain behavior needs a test; bug fixes need a regression test

## Commit messages

Conventional-ish: `feat: …`, `fix: …`, `docs: …`, `test: …`, `refactor: …`, `ci: …`

## Reporting bugs

Use the bug report issue template. For security issues, see `SECURITY.md` — do not file public issues.

## License

By contributing you agree that your contributions are licensed under the Apache-2.0 License.
