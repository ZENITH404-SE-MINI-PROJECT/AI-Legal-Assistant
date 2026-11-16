# Validation Spec, System Validation Report and Maintenance Plan

## 1. Validation approach
| Level | What | How | Evidence |
|---|---|---|---|
| Unit | Each module in isolation | pytest | `backend/tests`, coverage report |
| Integration | Pipeline and cross-module rules | pytest + TestClient | IT-01..08 |
| System (black box) | User journeys via UI | Manual on docker-compose stack | ST-01..10 (execute and record) |
| White box | Branch coverage | `pytest --cov --cov-branch` | CI artifact `coverage.xml` |
| Security | SAST, authz, input validation, upload abuse | bandit, authz tests, SonarQube | Jenkins/GH Actions logs |
| Non-functional | Latency, availability | Manual timing (ST-09) | record in test plan |

### Security validation checklist
- [x] Passwords hashed with bcrypt; never returned
- [x] JWT expiry (30 min), invalid/expired tokens rejected
- [x] Login lockout after 5 failures
- [x] RBAC on all `/admin` routes; self-registration cannot create admins
- [x] Object-level authorisation for conversations, documents, feedback
- [x] Upload checks: extension, magic bytes, size, server-generated filename
- [x] LIKE wildcard escaping; ORM parameterised queries
- [x] Security headers; restricted CORS methods/headers
- [x] Non-root container user
- [ ] **Before real deployment:** enforce HTTPS/TLS at the proxy, set a strong `SECRET_KEY`, move rate limiting to a shared store (Redis) if running multiple workers, add antivirus scanning for uploads, and run a pen test.

## 2. Automated results (latest run)
- 104 pytest tests, 0 failures (see `docs/05_Test_Plan.md` for case-level results).
- Statement + branch coverage about 95% (`pytest --cov=app --cov-branch`).
- `bandit -r app`: no issues identified.
- Frontend `npm run build`: succeeds.

## 3. Manual system test record
Fill in after running ST-01..ST-10 (the Actual Result and Test Result columns in `docs/05_Test_Plan.md`). Do not mark them passed until executed.

## 4. Known limitations
- Knowledge base is a small starter set; answer quality depends on its completeness (SRS section 7).
- Keyword retrieval can miss paraphrases; semantic search is future work.
- The classifier is keyword-based and can misroute unusual phrasing.
- Legal content changes (e.g. BNSS replaced the CrPC from 1 July 2024; labour codes are being brought in); admins must keep entries current. **All seeded entries should be verified by the team against primary sources before the demo.**
- Login throttling is in-memory (per process).
- Not legal advice; cannot file documents or represent anyone.

## 5. Maintenance plan
| Type | Activity | Frequency | Owner |
|---|---|---|---|
| Corrective | Triage GitHub issues labelled `bug`; add a regression test with each fix | Weekly | Rotating |
| Adaptive | Review KB entries against new statutes/judgments; upgrade LLM model name via `LLM_MODEL` | Monthly | Admin / content owner |
| Perfective | Review low-rated responses and error reports in the Admin tab; add/refine entries and keywords | Weekly | Admin |
| Preventive | Dependency updates, `bandit`/SonarQube, backups of PostgreSQL volume | Monthly | DevOps owner |
| Release | Tag release, CI must be green (>= 85% coverage gate), `docker compose up -d --build` | Per release | Team lead |

**Extension points:** replace `classifier.classify` with an ML model; replace `retrieval.retrieve` with embeddings; add a provider in `llm_service._call_llm`; add languages (future work in the SRS).
