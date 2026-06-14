# Skill Registry — activia-trace

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

## Skills Installed (User-Level)

| Trigger | Skill | Path |
|---------|-------|------|
| Python/FastAPI SQLAlchemy async | `fastapi-python` | `~\.agents\skills\fastapi-python\SKILL.md` |
| FastAPI advanced patterns | `fastapi-pro` | `~\.agents\skills\fastapi-pro\SKILL.md` |
| FastAPI async perf | `fastapi-async-patterns` | `~\.claude\skills\fastapi-async-patterns\SKILL.md` |
| Python testing pytest | `python-testing-patterns` | `~\.agents\skills\python-testing-patterns\SKILL.md` |
| Python code quality linting | `python-code-quality` | `~\.agents\skills\python-code-quality\SKILL.md` |
| PostgreSQL optimization | `postgres` | `~\.agents\skills\postgres\SKILL.md` |
| Supabase PostgreSQL | `supabase-postgres-best-practices` | `~\.agents\skills\supabase-postgres-best-practices\SKILL.md` |
| Neon PostgreSQL serverless | `neon-postgres` | `~\.agents\skills\neon-postgres\SKILL.md` |
| Security best practices (OpenAI) | `security-best-practices` | `~\.agents\skills\security-best-practices\SKILL.md` |
| Code review adversarial | `judgment-day` | `~\.claude\skills\judgment-day\SKILL.md` |
| Code review excellence | `code-review-excellence` | `~\.agents\skills\code-review-excellence\SKILL.md` |
| Systematic debugging | `systematic-debugging` | `~\.agents\skills\systematic-debugging\SKILL.md` |
| TypeScript advanced types | `typescript-advanced-types` | `~\.agents\skills\typescript-advanced-types\SKILL.md` |
| React 18+ Vite | `react-vite` | `~\.config\opencode\skills\react-vite\SKILL.md` |
| Tailwind v4 theme | `tailwind-theme-builder` | `~\.config\opencode\skills\tailwind-theme-builder\SKILL.md` |
| shadcn/ui components | `shadcn-ui` | `~\.config\opencode\skills\shadcn-ui\SKILL.md` |
| Vercel React patterns | `vercel-react-best-practices` | `~\.agents\skills\vercel-react-best-practices\SKILL.md` |
| n8n workflows | `n8n-*` | `~\.agents\skills\n8n-*\SKILL.md` |
| Vite build tool | `vite` | `~\.agents\skills\vite\SKILL.md` |
| Conventional commits/GH | `gh-commit` | `~\.agents\skills\gh-commit\SKILL.md` |
| KB creator | `kb-creator` | `~\.claude\skills\kb-creator\SKILL.md` |
| Roadmap generator | `roadmap-generator` | `~\.claude\skills\roadmap-generator\SKILL.md` |
| Agent instructions | `agent-instruction` | `~\.claude\skills\agent-instruction\SKILL.md` |
| Find/install skills | `find-skill` | `~\.config\opencode\skills\find-skill\SKILL.md` |
| Skill registry | `skill-registry` | `~\.claude\skills\skill-registry\SKILL.md` |
| OPSX propose | `openspec-propose` | `~\.config\opencode\skills\openspec-propose\SKILL.md` |
| OPSX apply | `openspec-apply-change` | `~\.config\opencode\skills\openspec-apply-change\SKILL.md` |
| OPSX archive | `openspec-archive-change` | `~\.config\opencode\skills\openspec-archive-change\SKILL.md` |
| OPSX explore | `openspec-explore` | `~\.config\opencode\skills\openspec-explore\SKILL.md` |

## Compact Rules (Relevant to activia-trace)

### python-code-quality
- Ruff for linting: `ruff check .` and `ruff check --fix .` for auto-fixable (F401, F541)
- F401 (unused-import): remove imports not used in file
- F811 (redefined-while-unused): don't redefine fixtures already in conftest.py
- F841 (unused-variable): remove or use variables declared
- E402 (import-not-at-top): all imports must be at module level, top of file
- F541 (f-string-missing-placeholders): don't use f"string" without {variables}
- E712 (true-false-comparison): use `if cond:` not `if cond == True:`
- Always run `ruff check --fix` before archiving a change

### security-best-practices
- Never hardcode secrets, API keys, passwords — use environment variables / vault
- JWT: short-lived access tokens + refresh rotation; validate signature on every request
- PII (CBU, DNI, email): encrypt at rest with AES-256; never log plaintext
- Passwords: Argon2id, never plaintext, never MD5/SHA1
- RBAC: fail-closed (deny by default); validate permissions on every endpoint
- Input validation: use Pydantic with `extra='forbid'` — reject unknown fields
- SQL injection: use ORM parameterized queries (SQLAlchemy), never raw string interpolation
- Audit logs: never log secrets, tokens, or passwords; log access attempts (success/failure)

### fastapi-pro
- Use `Annotated[..., Depends()]` pattern for dependency injection (PEP 593)
- Router-Service-Repository layering: routers only handle HTTP, services = business logic, repos = DB
- Async endpoints: `async def` with `await` for all I/O; avoid `sync_to_async` where possible
- Pydantic v2: `model_validate()` not `parse_obj()`, `model_dump()` not `dict()`
- OpenAPI: use `response_model=`, `status_code=`, `description=` for self-documenting APIs
- Error handling: custom exception handlers with structured JSON responses, not generic 500s

### code-review-excellence
- Check for hardcoded values, magic numbers, TODOs left in code
- Verify error handling: every `except` should log and re-raise or return structured error
- Security: no SQL injection vectors, no hardcoded secrets, validate all inputs
- Architecture: verify layering (no service calling router, no repo calling service)
- Tests: verify edge cases, not just happy path; look for missing test coverage
- Performance: N+1 queries, missing indexes, loading entire tables unnecessarily

### python-testing-patterns
- Fixtures in conftest.py, not scattered across test files
- Use `pytest.mark.parametrize` for testing multiple inputs
- Real DB test containers, NOT mocks — mock invalida el test
- Arrange-Act-Assert structure in every test function
- Async tests: use `pytest.mark.asyncio` or `asyncio_mode = "auto"`
- Coverage target: ≥80% lines, ≥90% business rules

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | `AGENTS.md` | Index — project rules, skills, governance, workflow |
| CLAUDE.md | `CLAUDE.md` | Copy of AGENTS.md |
| CHANGES.md | `CHANGES.md` | Roadmap with 24 changes, dependency tree, gates |
| pyproject.toml | `backend/pyproject.toml` | Project config: ruff target py313, mypy strict |

Read AGENTS.md before any implementation — it contains project-specific rules, governance levels, and hard constraints.
