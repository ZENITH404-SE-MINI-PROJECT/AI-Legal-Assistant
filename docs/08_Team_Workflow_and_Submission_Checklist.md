# Team workflow and submission checklist

## Git workflow (every member must commit - commits are checked)
1. `main` is protected; work on `feature/<short-name>` branches (one owner per feature, see `02_Synopsis.md`).
2. Open a PR using `.github/pull_request_template.md`; at least one teammate reviews; CI must pass.
3. Link PRs to GitHub Issues (user stories, template provided) and tag the FR IDs.
4. Create the first commits per member early, e.g. each person commits their own module and its tests.

Suggested first issues (user stories): FR-01..FR-19 each as a story; add story points and a sprint label.

## Deliverables mapped to the guidelines
| Stage | Deliverable | File |
|---|---|---|
| Requirements | SRS (+ validation spec) | `docs/01_SRS_AI_Legal_Assistant.docx`, `docs/07_...` |
| Synopsis | Proposal | `docs/02_Synopsis.md` |
| Planning | Project plan (PDF named `28.pdf`) | `docs/03_Project_Plan.md` |
| Design | Architecture + design | `docs/04_Architecture_and_Design.md` |
| Implementation | Code, PRs, unit tests, coverage | `backend/`, `frontend/` |
| Testing | Test plan | `docs/05_Test_Plan.md`, `docs/test_cases.csv` |
| Traceability | RTM | `docs/06_...` |
| System validation | Report + maintenance plan | `docs/07_...` |
| Final | Report (cover, TOC, proposal, SRS, plan, design, test cases, screenshots) + 15-min demo | assemble from the above |

## Before you submit - things only your team can do
- [ ] Verify every seeded legal entry against primary sources (and fix dates/sections).
- [ ] Run the manual system tests (ST-01..10) and record results; take screenshots for the report.
- [ ] Convert the plan/design docs to PDF (the guidelines require PDF; the plan PDF must be named with the project ID, `28.pdf`). Render the Mermaid diagrams (GitHub renders them, or use mermaid.live) and generate a real Gantt chart.
- [ ] Update the cover page dates (the guideline template says 2022; use the current term).
- [ ] Set up GitHub Projects/Jira board and Jenkins/SonarQube so screenshots/logs exist.
- [ ] Make sure each member can explain the code of their module (graded in the demo).
