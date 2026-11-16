# Synopsis / Project Proposal

**Project title:** AI-Based Legal Assistant, e-Lawyer and Case Guidance System (Project ID 28)
**Group:** ZENITH404

| Member | SRN |
|---|---|
| P Mahema Sai | PES2UG24AM107 |
| Nihira Hassan | PES2UG24AM106 |
| Nanditha A | PES2UG24AM100 |
| Namitha N Reddy | PES2UG24AM098 |

## Proposed project description
A web application that gives plain-language legal *information* for common Indian legal issues. Each question is
validated, classified into one of seven supported domains (consumer, tenancy, family, employment, cyber law,
criminal procedure, RTI), matched against a curated knowledge base of procedures and case law, and answered by an
LLM that is constrained to the retrieved material. Every answer carries sources and a "not a lawyer" disclaimer.
Anything outside the supported domains gets an out-of-scope message rather than a guess.

**Users:** students and members of the public (Standard User); administrators who curate the knowledge base.
**Novelty / differentiation:** retrieval-constrained generation with an out-of-scope fallback, a safety filter that
strips guarantee/"as your lawyer" phrasing, graceful degradation when the LLM is unavailable, and separate
classify -> retrieve -> generate stages so each can be swapped independently.

## Functional features (what the user can do)
1. Register/login; sessions time out automatically.
2. Ask legal questions and follow-ups; get answers with cited sources and a disclaimer.
3. Get step-by-step guidance for common procedures (FIR, consumer complaint, RTI, divorce, ...).
4. Search case law by keyword, jurisdiction or citation.
5. Browse legal templates, fill placeholders, download as TXT/DOCX.
6. Upload PDF/TXT/DOCX and receive a summary and key clauses.
7. Rate responses or report errors.
8. (Admin) manage knowledge entries, templates, feedback and users.
9. Delete own conversations and documents.

## Plan of work and product ownership (suggested - confirm in your team meeting)
| Member | Owned functionality (one full feature each) | Qualitative property |
|---|---|---|
| P Mahema Sai | **Conversational assistant:** FR-01..FR-10 (`chat_api`, `classifier`, `retrieval`, `llm_service`) | 90% of queries answered in <= 5 s; never claims guaranteed outcomes |
| Nihira Hassan | **Admin tools + user management:** FR-16..FR-19, RBAC (`admin_kb`, `auth_api`, `security`) | Passwords hashed, role separation enforced |
| Nanditha A | **Templates + case law search:** FR-09, FR-11, FR-12 (`template_api`, `case_law_api`) | Case search < 3 s; usable without legal background |
| Namitha N Reddy | **Document upload/analysis + feedback:** FR-13..FR-15 (`doc_analysis`, `feedback_api`) | Uploads private to owner; strict file validation |

Short-term plan: see `03_Project_Plan.md` (sprints 1-4).
