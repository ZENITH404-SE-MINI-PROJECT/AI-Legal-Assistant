# AI-Based Legal Assistant (Project 28) - Team ZENITH404

Web app giving plain-language **legal information** for common Indian legal issues. Flow:
validate -> classify domain -> keyword retrieval from the knowledge base -> LLM answer constrained to that material -> sources + disclaimer.
Anything out of scope gets a fixed out-of-scope message. **Informational only - not a lawyer.**

Stack: FastAPI, SQLAlchemy, PostgreSQL (SQLite for dev/tests), React + Vite, Docker, Jenkins / GitHub Actions.

## Quick start

### Option A - Docker (full stack)
```bash
cp .env.example .env        # set SECRET_KEY and ADMIN_PASSWORD (LLM_API_KEY optional)
docker compose up --build
# UI: http://localhost:8080      API docs: via backend container port 8000 (add a ports mapping to expose)
```
Log in as the admin using `ADMIN_USERNAME` (default `admin`) and your `ADMIN_PASSWORD`.

### Option B - local dev
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_USERNAME=admin ADMIN_PASSWORD=ChangeMe123
uvicorn app.main:app --reload            # http://localhost:8000/docs  (SQLite file by default)

# frontend (new terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173 (proxies /api to :8000)
```

### Without an LLM key
With `LLM_API_KEY` empty the app uses a deterministic fallback that assembles the answer from the retrieved entries,
so everything works offline. Set `LLM_API_KEY` (and optionally `LLM_MODEL`, `LLM_API_URL`) to use a real model
(Anthropic Messages API format).

## Tests, coverage, quality
```bash
cd backend
pytest --cov=app --cov-branch --cov-report=term-missing   # 104 tests, ~95% coverage
bandit -r app -ll                                          # security scan
flake8 app tests --max-line-length=120                     # lint
cd .. && python tools/generate_test_plan.py                # refresh docs/05_Test_Plan.md from a real test run
```

## Project layout
```
backend/app/        FastAPI app (one module per SRS design reference: chat_api, classifier, retrieval,
                    llm_service, case_law_api, template_api, doc_analysis, feedback_api, admin_kb, ...)
backend/tests/      pytest suites (unit + integration)
frontend/src/       React UI (Chat, CaseLaw, Templates, Documents, Admin, response_view.jsx)
docs/               SRS, synopsis, project plan, design, test plan, RTM, validation + maintenance plan
Jenkinsfile, .github/workflows/ci.yml, sonar-project.properties, docker-compose.yml
```

## Configuration (environment variables)
| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./legal_assistant.db` | Compose uses PostgreSQL |
| `SECRET_KEY` | dev value | **Must** be set in production |
| `ACCESS_TOKEN_MINUTES` | 30 | Session timeout |
| `LLM_API_KEY`, `LLM_MODEL`, `LLM_API_URL` | empty / `claude-sonnet-4-6` / Anthropic | Optional LLM |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | - | Seeds an admin on first start |
| `MAX_UPLOAD_BYTES`, `UPLOAD_DIR`, `CORS_ORIGINS` | 5 MB, `./uploads`, localhost | |

## Important notes
- The seeded legal knowledge is a **starter set**. Verify it against primary sources before relying on or demoing it, and extend it via the Admin tab.
- Documentation checklist and what's left for the team: `docs/08_Team_Workflow_and_Submission_Checklist.md`.
