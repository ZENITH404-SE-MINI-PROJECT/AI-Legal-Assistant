# Requirements Traceability Matrix (Appendix C of the SRS, updated to the implementation)

| Req ID | Description | Design ref | Code file | Unit/Integration tests | System test |
|---|---|---|---|---|---|
| FR-01 | Accept natural-language queries from authenticated users | Chat module | `backend/app/chat_api.py`, `deps.py` | UT-01-01, UT-01-02 | ST-01 |
| FR-02 | Validate query length/content | Chat module | `chat_api.py::validate_query` | UT-01-04, UT-01-05, UT-01-06 | ST-02 |
| FR-03 | Classify into supported domain | Domain classifier | `classifier.py` | UT-02-01..08 | ST-01 |
| FR-04 | Out-of-scope message | Domain classifier / Chat | `classifier.py`, `chat_api.py` | UT-01-03, UT-02-07 | ST-02 |
| FR-05 | Keyword retrieval from DB | Retrieval module | `retrieval.py` | UT-03-01..08 | ST-01 |
| FR-06 | Domain-constrained response | Generation module | `llm_service.py` | UT-04-01..08, IT-08 | ST-01 |
| FR-07 | Disclaimer and source on every response | UI renderer + API | `chat_api.py`, `config.py`, `frontend/src/response_view.jsx` | UT-01-02, UT-01-03, UT-05-01..04 | ST-01 |
| FR-08 | Step-by-step procedure guidance | Chat module | `chat_api.py`, `seed.py` | IT-02 | ST-03 |
| FR-09 | Case-law search | Case law module | `case_law_api.py` | UT-06-01..08 | ST-04 |
| FR-10 | Use history for follow-ups | Chat module | `chat_api.py` | UT-01-07, IT-01 | ST-01 |
| FR-11 | Searchable template repository | Template module | `template_api.py` | UT-07-04 | ST-05 |
| FR-12 | Fill and download templates | Template module | `template_api.py` | UT-07-01..09 | ST-05 |
| FR-13 | Upload with size/format checks | Analysis module | `doc_analysis.py` | UT-08-02..09 | ST-06 |
| FR-14 | Summary and key clauses | Analysis module | `doc_analysis.py`, `llm_service.py` | UT-08-01, UT-04-08 | ST-06 |
| FR-15 | Ratings / error reports | Feedback module | `feedback_api.py` | UT-09-01..08 | ST-07 |
| FR-16 | Admin edits case/procedure entries | Admin module | `admin_kb.py` | UT-10-01..04, IT-03 | ST-08 |
| FR-17 | Admin edits templates | Admin module | `admin_kb.py` | UT-10-05 | ST-08 |
| FR-18 | Admin reviews feedback | Admin module | `admin_kb.py` | UT-10-06, IT-06 | ST-07 |
| FR-19 | Admin user management | Admin module | `admin_kb.py` | UT-10-07, UT-10-08 | - |
| NFR 6.1 | 90% queries <= 5 s; case search <= 3 s | Whole system | - | - | ST-09 |
| NFR 6.2/6.5 | Never imply guaranteed outcomes / claim to be a lawyer | Generation module | `llm_service.py::enforce_safety` | UT-04-01, UT-04-05 | ST-01 |
| NFR 6.3 | Hashed passwords, RBAC, token timeout, owner-only docs, erasure | Security | `security.py`, `deps.py`, `auth_api.py`, `doc_analysis.py` | UT-11-01..10, IT-04, IT-05, IT-07 | ST-10 |
