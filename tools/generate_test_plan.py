"""Builds docs/05_Test_Plan.md + docs/test_cases.csv.

Automated cases (UT/IT) are linked to pytest tests; their Actual Result / Test Result are filled
from a real pytest run (junit xml). System tests (ST) and UI renderer cases need a human with a
browser: they are emitted with 'Pending manual execution' - run them and update the table.

Usage:  python tools/generate_test_plan.py      (from repo root)
"""
import csv
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

# (id, module, description, pre-conditions, steps, test data, expected, pytest-name-substring or None)
CASES = [
    # ---- UT-01 chat_api ----
    ("UT-01-01", "Chat (chat_api.py)", "Unauthenticated request is refused", "No token", "POST /api/chat/ask without Authorization header", "question='How to file an FIR?'", "HTTP 401", "test_requires_authentication"),
    ("UT-01-02", "Chat (chat_api.py)", "In-scope question returns answer, source and disclaimer", "Logged in; KB seeded", "POST /api/chat/ask", "My landlord will not return my security deposit...", "in_scope=true, domain=tenancy, sources non-empty, disclaimer present", "test_in_scope_answer_has_source_and_disclaimer"),
    ("UT-01-03", "Chat (chat_api.py)", "Out-of-scope question gets fixed message", "Logged in", "POST /api/chat/ask", "What is the best recipe for chocolate cake?", "in_scope=false, out-of-scope message, no sources, disclaimer present", "test_out_of_scope_message"),
    ("UT-01-04", "Chat (chat_api.py)", "Too-short query rejected (invalid input)", "Logged in", "POST /api/chat/ask", "'hi'", "HTTP 422 with length message", "test_too_short_query_rejected"),
    ("UT-01-05", "Chat (chat_api.py)", "Too-long query rejected (invalid input)", "Logged in", "POST /api/chat/ask", "1600-character string", "HTTP 422", "test_too_long_query_rejected"),
    ("UT-01-06", "Chat (chat_api.py)", "Symbol-only query rejected (invalid input)", "Logged in", "POST /api/chat/ask", "'?????!!!!!'", "HTTP 422 'enter your question in words'", "test_symbol_only_query_rejected"),
    ("UT-01-07", "Chat (chat_api.py)", "Conversation history stored and listed", "Logged in", "Ask a question; GET /chat/conversations; GET /chat/conversations/{id}", "refund question", "1 conversation with user + assistant messages", "test_conversation_history_listed_and_loaded"),
    ("UT-01-08", "Chat (chat_api.py)", "Conversation can be deleted by owner", "Existing conversation", "DELETE /chat/conversations/{id}; GET it again", "-", "204 then 404", "test_delete_conversation"),
    # ---- UT-02 classifier ----
    ("UT-02-01", "Classifier (classifier.py)", "Tenancy query classified", "-", "classify(query)", "landlord / security deposit", "'tenancy'", "test_supported_domains[My landlord"),
    ("UT-02-02", "Classifier (classifier.py)", "Consumer query classified", "-", "classify(query)", "seller refused refund defective phone", "'consumer'", "test_supported_domains[The seller"),
    ("UT-02-03", "Classifier (classifier.py)", "Family query classified", "-", "classify(query)", "divorce by mutual consent", "'family'", "test_supported_domains[How can I get a divorce"),
    ("UT-02-04", "Classifier (classifier.py)", "Employment query classified", "-", "classify(query)", "employer has not paid salary", "'employment'", "test_supported_domains[My employer"),
    ("UT-02-05", "Classifier (classifier.py)", "Cyber query classified", "-", "classify(query)", "UPI scam", "'cyber'", "test_supported_domains[I lost money"),
    ("UT-02-06", "Classifier (classifier.py)", "Criminal-procedure query classified", "-", "classify(query)", "FIR when police refuse", "'criminal_procedure'", "test_supported_domains[How do I file an FIR"),
    ("UT-02-07", "Classifier (classifier.py)", "Unsupported query returns None", "-", "classify(query)", "What is the best pizza in town", "None", "test_out_of_scope_returns_none[What is the best pizza"),
    ("UT-02-08", "Classifier (classifier.py)", "Whole-word matching (no false positive on 'pfizer')", "-", "domain_scores('the pfizer vaccine')", "pfizer", "employment score = 0", "test_word_boundary_matching"),
    # ---- UT-03 retrieval ----
    ("UT-03-01", "Retrieval (retrieval.py)", "Stop-words removed in tokenisation", "-", "tokenize('How do I file the FIR?')", "-", "['file','fir']", "test_tokenize_removes_stopwords"),
    ("UT-03-02", "Retrieval (retrieval.py)", "Relevant entry retrieved", "KB seeded", "retrieve(q, 'criminal_procedure')", "file FIR with police", "FIR entry returned", "test_retrieves_relevant_entry"),
    ("UT-03-03", "Retrieval (retrieval.py)", "Retrieval limited to the classified domain", "KB seeded", "retrieve('file FIR police','consumer')", "-", "all results have domain=consumer", "test_retrieval_is_domain_scoped"),
    ("UT-03-04", "Retrieval (retrieval.py)", "No match returns empty list", "KB seeded", "retrieve('zzzz qqqq','tenancy')", "gibberish", "[]", "test_no_match_returns_empty"),
    ("UT-03-05", "Retrieval (retrieval.py)", "Stop-word-only query returns empty list", "-", "retrieve('the and of', ...)", "-", "[]", "test_empty_query_returns_empty"),
    ("UT-03-06", "Retrieval (retrieval.py)", "Result limit respected", "KB seeded", "retrieve(..., limit=2)", "arrest police custody bail fir", "<= 2 results", "test_limit_respected"),
    ("UT-03-07", "Retrieval (retrieval.py)", "Case-insensitive matching", "KB seeded", "retrieve(uppercase query)", "FILE AN FIR AT THE POLICE STATION", "results returned", "test_matching_is_case_insensitive"),
    ("UT-03-08", "Retrieval (retrieval.py)", "Best match ranked first", "KB seeded", "retrieve(q)", "how to file fir police station zero fir", "procedure entry first", "test_best_match_ranked_first"),
    # ---- UT-04 llm_service ----
    ("UT-04-01", "Generation (llm_service.py)", "Safety filter removes guarantee / lawyer claims", "-", "enforce_safety(text)", "'You will definitely win. I guarantee it, as your lawyer.'", "phrases removed", "test_safety_filter_removes_guarantees"),
    ("UT-04-02", "Generation (llm_service.py)", "Clean text is unchanged", "-", "enforce_safety(text)", "neutral sentence", "identical text", "test_clean_text_unchanged_by_safety_filter"),
    ("UT-04-03", "Generation (llm_service.py)", "Fallback answer built only from retrieved entries", "KB seeded", "fallback_answer([entry])", "-", "entry title in answer", "test_fallback_uses_only_retrieved_entries"),
    ("UT-04-04", "Generation (llm_service.py)", "Provider failure degrades gracefully", "LLM key set; provider raises", "generate_answer(...)", "-", "fallback answer returned", "test_llm_failure_falls_back"),
    ("UT-04-05", "Generation (llm_service.py)", "LLM output is sanitised", "LLM returns unsafe text", "generate_answer(...)", "'I guarantee you will win'", "no 'guarantee' in output", "test_llm_answer_is_sanitised"),
    ("UT-04-06", "Generation (llm_service.py)", "Prompt contains reference material, history and question", "-", "build_prompt(...)", "-", "all three present", "test_build_prompt_contains_material_and_question"),
    ("UT-04-07", "Generation (llm_service.py)", "Provider response parsed", "httpx mocked", "_call_llm(...)", "two text blocks", "'hello world'", "test_call_llm_parses_provider_response"),
    ("UT-04-08", "Generation (llm_service.py)", "Bad LLM JSON in document analysis falls back to heuristic", "LLM returns non-JSON", "analyze_document(text)", "-", "heuristic summary returned", "test_document_analysis_bad_llm_json_falls_back"),
    # ---- UT-05 response_view.jsx (UI, manual) ----
    ("UT-05-01", "UI Renderer (response_view.jsx)", "Answer text displayed", "App running, logged in", "Ask a question", "any in-scope question", "Answer bubble visible", None),
    ("UT-05-02", "UI Renderer (response_view.jsx)", "Disclaimer shown under every answer", "App running", "Ask in-scope and out-of-scope questions", "-", "Disclaimer visible in both", None),
    ("UT-05-03", "UI Renderer (response_view.jsx)", "Numbered steps shown for procedure answers", "App running", "Ask 'How do I file an FIR?'", "-", "Ordered list of steps", None),
    ("UT-05-04", "UI Renderer (response_view.jsx)", "Sources list shown", "App running", "Ask a tenancy question", "-", "Sources list visible", None),
    # ---- UT-06 case_law_api ----
    ("UT-06-01", "Case law (case_law_api.py)", "Search by keyword", "Logged in", "GET /case-law?q=privacy", "privacy", "Puttaswamy case listed", "test_search_by_keyword"),
    ("UT-06-02", "Case law (case_law_api.py)", "Search by citation", "Logged in", "GET /case-law?citation=(2015) 5 SCC 1", "(2015) 5 SCC 1", "Shreya Singhal only", "test_search_by_citation"),
    ("UT-06-03", "Case law (case_law_api.py)", "Search by jurisdiction", "Logged in", "GET /case-law?jurisdiction=india", "india", "> 5 results", "test_search_by_jurisdiction"),
    ("UT-06-04", "Case law (case_law_api.py)", "Unknown jurisdiction returns empty", "Logged in", "GET /case-law?jurisdiction=Atlantis", "Atlantis", "[]", "test_unknown_jurisdiction_empty"),
    ("UT-06-05", "Case law (case_law_api.py)", "Only case entries returned (not procedures)", "Logged in", "GET /case-law", "-", "every row has a citation", "test_only_cases_not_procedures"),
    ("UT-06-06", "Case law (case_law_api.py)", "SQL wildcard characters escaped", "Logged in", "GET /case-law?q=%", "%", "[]", "test_wildcard_characters_are_escaped"),
    ("UT-06-07", "Case law (case_law_api.py)", "Authentication required", "No token", "GET /case-law", "-", "HTTP 401", "test_requires_auth"),
    ("UT-06-08", "Case law (case_law_api.py)", "Invalid limit rejected", "Logged in", "GET /case-law?limit=0", "0", "HTTP 422", "test_limit_validation"),
    # ---- UT-07 template_api ----
    ("UT-07-01", "Templates (template_api.py)", "Placeholders extracted in order, no duplicates", "-", "placeholders(text)", "'Hi {{a}} and {{ b }} and {{a}}'", "['a','b']", "test_placeholders_extracted_in_order_without_duplicates"),
    ("UT-07-02", "Templates (template_api.py)", "Placeholders substituted", "-", "fill_template", "name=' Ravi '", "'Dear Ravi'", "test_fill_template_substitutes"),
    ("UT-07-03", "Templates (template_api.py)", "Missing value raises error naming the field", "-", "fill_template", "city missing", "ValueError mentions 'city'", "test_fill_template_missing_value_raises"),
    ("UT-07-04", "Templates (template_api.py)", "List and search templates", "Logged in", "GET /templates, GET /templates?q=salary", "salary", ">=5 templates; 1 match", "test_list_and_search"),
    ("UT-07-05", "Templates (template_api.py)", "Download filled template as .txt", "Logged in", "POST /templates/{id}/fill", "all RTI fields", "200, attachment, no '{{' left", "test_fill_and_download_txt"),
    ("UT-07-06", "Templates (template_api.py)", "Download filled template as .docx", "Logged in", "POST /templates/{id}/fill?fmt=docx", "all RTI fields", "valid .docx with paragraphs", "test_fill_and_download_docx"),
    ("UT-07-07", "Templates (template_api.py)", "Incomplete form rejected", "Logged in", "POST fill with only 'date'", "partial values", "HTTP 422", "test_fill_missing_field_422"),
    ("UT-07-08", "Templates (template_api.py)", "Unsupported download format rejected", "Logged in", "POST fill?fmt=exe", "fmt=exe", "HTTP 422", "test_bad_format_rejected"),
    ("UT-07-09", "Templates (template_api.py)", "Unknown template id", "Logged in", "GET /templates/9999", "9999", "HTTP 404", "test_unknown_template_404"),
    # ---- UT-08 doc_analysis ----
    ("UT-08-01", "Documents (doc_analysis.py)", "Upload TXT -> summary + clauses", "Logged in", "POST /documents", "contract.txt", "201, summary and key clauses", "test_upload_txt_returns_summary_and_clauses"),
    ("UT-08-02", "Documents (doc_analysis.py)", "Upload PDF", "Logged in", "POST /documents", "a.pdf", "201, file_type PDF", "test_upload_pdf"),
    ("UT-08-03", "Documents (doc_analysis.py)", "Upload DOCX", "Logged in", "POST /documents", "a.docx", "201, file_type DOCX", "test_upload_docx"),
    ("UT-08-04", "Documents (doc_analysis.py)", "Unsupported extension rejected", "Logged in", "POST /documents", "evil.exe", "HTTP 422", "test_rejects_unsupported_extension"),
    ("UT-08-05", "Documents (doc_analysis.py)", "Empty file rejected", "Logged in", "POST /documents", "0-byte txt", "HTTP 422", "test_rejects_empty_file"),
    ("UT-08-06", "Documents (doc_analysis.py)", "Oversize file rejected", "Limit lowered to 100 B", "POST /documents", "500-byte file", "HTTP 422", "test_rejects_oversize"),
    ("UT-08-07", "Documents (doc_analysis.py)", "Extension/content mismatch rejected", "Logged in", "POST /documents", "fake.pdf with text content", "HTTP 422", "test_rejects_extension_content_mismatch"),
    ("UT-08-08", "Documents (doc_analysis.py)", "Corrupt PDF handled", "Logged in", "POST /documents", "'%PDF-1.4 garbage'", "HTTP 422, no crash", "test_corrupt_pdf_handled"),
    ("UT-08-09", "Documents (doc_analysis.py)", "Path-traversal filename is harmless", "Logged in", "POST /documents", "../../etc/passwd.txt", "stored under server-chosen name", "test_path_traversal_filename_is_harmless"),
    ("UT-08-10", "Documents (doc_analysis.py)", "Documents private to owner", "Two users", "User B GET/DELETE user A's doc", "-", "404; B's list empty", "test_documents_are_private_to_owner"),
    # ---- UT-09 feedback_api ----
    ("UT-09-01", "Feedback (feedback_api.py)", "Rating + comment accepted", "Has response", "POST /feedback", "rating 4", "201", "test_submit_rating_and_comment"),
    ("UT-09-02", "Feedback (feedback_api.py)", "Error report accepted", "Has response", "POST /feedback", "is_error_report=true", "201", "test_error_report_only"),
    ("UT-09-03", "Feedback (feedback_api.py)", "Empty feedback rejected", "Has response", "POST /feedback", "no rating/comment", "422", "test_empty_feedback_rejected"),
    ("UT-09-04", "Feedback (feedback_api.py)", "Rating out of range rejected", "Has response", "POST /feedback", "rating 9", "422", "test_rating_out_of_range_rejected"),
    ("UT-09-05", "Feedback (feedback_api.py)", "Duplicate feedback refused", "Feedback exists", "POST /feedback again", "-", "409", "test_duplicate_feedback_conflict"),
    ("UT-09-06", "Feedback (feedback_api.py)", "Cannot rate another user's response", "Two users", "User B posts feedback for A's message", "-", "404", "test_cannot_rate_other_users_response"),
    ("UT-09-07", "Feedback (feedback_api.py)", "Unknown message id", "Logged in", "POST /feedback", "message_id 99999", "404", "test_unknown_message_404"),
    ("UT-09-08", "Feedback (feedback_api.py)", "Authentication required", "No token", "POST /feedback", "-", "401", "test_requires_auth"),
    # ---- UT-10 admin_kb ----
    ("UT-10-01", "Admin (admin_kb.py)", "Create/update/delete knowledge entry", "Admin logged in", "POST, PUT, DELETE /admin/references", "sample entry", "201/200/204; 404 on re-delete; change visible in search", "test_reference_crud"),
    ("UT-10-02", "Admin (admin_kb.py)", "New entry used by chat", "Admin adds procedure", "Ask related question as user", "widget refund", "Entry cited as source", "test_new_reference_is_used_by_chat"),
    ("UT-10-03", "Admin (admin_kb.py)", "Invalid domain/type rejected", "Admin", "POST /admin/references", "domain=astrology", "422", "test_invalid_domain_and_type_rejected"),
    ("UT-10-04", "Admin (admin_kb.py)", "Standard user blocked from admin API", "User logged in", "POST /admin/references and /admin/templates", "-", "403", "test_user_cannot_modify_knowledge_base"),
    ("UT-10-05", "Admin (admin_kb.py)", "Template CRUD", "Admin", "POST, PUT, DELETE /admin/templates", "sample template", "create/edit/delete work", "test_template_crud"),
    ("UT-10-06", "Admin (admin_kb.py)", "Review and resolve feedback", "Error report exists", "GET /admin/feedback; PUT resolve", "-", "listed then resolved", "test_feedback_review_and_resolve"),
    ("UT-10-07", "Admin (admin_kb.py)", "User management (role change, delete)", "Admin", "PUT role, DELETE user", "role=admin / wizard", "200 / 422 / 204", "test_user_management"),
    ("UT-10-08", "Admin (admin_kb.py)", "Admin cannot demote/delete self", "Admin", "PUT own role=user; DELETE self", "-", "400", "test_admin_cannot_demote_or_delete_self"),
    # ---- UT-11 auth ----
    ("UT-11-01", "Auth (auth_api.py)", "Register then login", "-", "POST /auth/register, /auth/login", "carol / Passw0rd1", "201 role=user; 200 token", "test_register_and_login"),
    ("UT-11-02", "Auth (security.py)", "Password stored hashed", "User registered", "Inspect DB row", "-", "bcrypt hash, not plaintext", "test_password_is_hashed_not_plaintext"),
    ("UT-11-03", "Auth (auth_api.py)", "Weak passwords rejected", "-", "POST /auth/register", "short1, allletters, 12345678", "422", "test_weak_password_rejected"),
    ("UT-11-04", "Auth (auth_api.py)", "Invalid username rejected", "-", "POST /auth/register", "'a b'", "422", "test_bad_username_rejected"),
    ("UT-11-05", "Auth (auth_api.py)", "Duplicate username rejected", "alice exists", "POST /auth/register", "alice", "409", "test_duplicate_username_rejected"),
    ("UT-11-06", "Auth (auth_api.py)", "Wrong password rejected", "alice exists", "POST /auth/login", "wrong password", "401", "test_wrong_password_unauthorized"),
    ("UT-11-07", "Auth (security.py)", "Account locks after 5 failures", "alice exists", "5 bad logins then good login", "-", "429", "test_lockout_after_repeated_failures"),
    ("UT-11-08", "Auth (deps.py)", "Expired token rejected (session timeout)", "-", "GET /auth/me with expired JWT", "-", "401", "test_expired_token_rejected"),
    ("UT-11-09", "Auth (deps.py)", "RBAC: user blocked from admin API", "User logged in", "GET /admin/users", "-", "403", "test_standard_user_cannot_use_admin_api"),
    ("UT-11-10", "Auth (auth_api.py)", "Right to erasure", "User has chats", "DELETE /auth/me/data", "-", "204; no conversations", "test_delete_my_data"),
    # ---- Integration ----
    ("IT-01", "Chat + Retrieval + Classifier", "Follow-up inherits previous domain (FR-10)", "Logged in", "Ask tenancy question, then 'How many days do I get?' in same conversation", "-", "second answer domain = tenancy", "test_follow_up_inherits_domain"),
    ("IT-02", "Chat + Retrieval", "Procedure guidance returns ordered steps (FR-08)", "Logged in", "Ask how to file an FIR", "-", ">= 3 steps", "test_procedure_guidance_returns_steps"),
    ("IT-03", "Admin + Retrieval + Chat", "Admin-added entry is used in answers (FR-16)", "Admin + user", "Admin adds entry; user asks", "-", "entry cited", "test_new_reference_is_used_by_chat"),
    ("IT-04", "Auth + Chat", "Deleting own data clears conversations", "User has chats", "DELETE /auth/me/data; list conversations", "-", "[]", "test_delete_my_data"),
    ("IT-05", "Documents + Auth", "Cross-user document isolation", "Two users", "B reads/deletes A's document", "-", "404", "test_documents_are_private_to_owner"),
    ("IT-06", "Feedback + Admin", "Error report visible to admin and resolvable", "User reports", "Admin lists and resolves", "-", "report shown then resolved", "test_feedback_review_and_resolve"),
    ("IT-07", "Chat + Auth", "Users cannot read or continue each other's conversations", "Two users", "B opens A's conversation", "-", "404", "test_cannot_read_other_users_conversation"),
    ("IT-08", "Chat + Generation", "Unavailable LLM does not break the answer pipeline", "LLM key set; provider down", "Ask a question", "-", "fallback answer returned", "test_llm_failure_falls_back"),
    # ---- System (manual) ----
    ("ST-01", "System", "End-to-end: register, login, ask, see sourced answer + disclaimer", "Stack running via docker compose", "Open UI; register; login; ask a tenancy question", "-", "Answer, sources and disclaimer displayed", None),
    ("ST-02", "System", "Out-of-scope handling in UI", "Logged in", "Ask about cooking", "-", "Out-of-scope message, no invented answer", None),
    ("ST-03", "System", "Procedure guidance in UI", "Logged in", "Ask 'How do I file an FIR?'", "-", "Step list displayed", None),
    ("ST-04", "System", "Case law search in UI", "Logged in", "Open Case law tab; search 'privacy'", "-", "Puttaswamy listed", None),
    ("ST-05", "System", "Template fill and download", "Logged in", "Templates tab; open RTI; fill; download .docx", "-", "File downloads with values substituted", None),
    ("ST-06", "System", "Upload and analyse a document", "Logged in", "My documents tab; upload sample PDF", "-", "Summary and key clauses shown", None),
    ("ST-07", "System", "Feedback from UI reaches admin", "User + admin", "Click Report error; admin opens Feedback tab", "-", "Report visible", None),
    ("ST-08", "System", "Admin KB edit reflected in answers", "Admin", "Add procedure in Admin tab; ask related question", "-", "New entry cited", None),
    ("ST-09", "System", "Performance: 90% of queries answered within 5 s (NFR 6.1)", "Stack running", "Send 20 questions; time them", "-", ">= 18 within 5 s", None),
    ("ST-10", "System", "Session expires after timeout (NFR 6.3)", "Logged in", "Wait > 30 min; use app", "-", "Redirected to login", None),
]


def run_pytest():
    xml_path = BACKEND / "junit.xml"
    proc = subprocess.run([sys.executable, "-m", "pytest", f"--junitxml={xml_path}", "-q"],
                          cwd=BACKEND, capture_output=True, text=True)
    results = []  # (classname.name, outcome) - list, so same-named tests in different files stay distinct
    for tc in ET.parse(xml_path).getroot().iter("testcase"):
        failed = tc.find("failure") is not None or tc.find("error") is not None
        results.append((f"{tc.get('classname')}::{tc.get('name')}", "Fail" if failed else "Pass"))
    xml_path.unlink(missing_ok=True)
    bad = sum(1 for _, v in results if v == "Fail")
    return results, f"{len(results)} pytest tests executed, {bad} failed"


def main():
    results, summary = run_pytest()
    rows, missing = [], []
    for cid, module, desc, pre, steps, data, expected, key in CASES:
        if key is None:
            actual, res = "Pending manual execution", "Not run"
        else:
            hits = [v for n, v in results if key in n.split("::")[-1]]
            if not hits:
                missing.append((cid, key))
                actual, res = "Test not found", "Not run"
            else:
                res = "Fail" if "Fail" in hits else "Pass"
                actual = "Behaved as expected (automated run)" if res == "Pass" else "Deviated from expected"
        rows.append((cid, module, desc, pre, steps, data, expected, actual, res))
    if missing:
        raise SystemExit(f"Unmapped test cases: {missing}")

    docs = ROOT / "docs"
    with open(docs / "test_cases.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Test Case ID", "Name of Module", "Test case description", "Pre-conditions", "Test Steps",
                    "Test data", "Expected Results", "Actual Result", "Test Result"])
        w.writerows(rows)

    esc = lambda s: str(s).replace("|", "\\|")  # noqa: E731
    total = len(rows)
    passed = sum(1 for r in rows if r[-1] == "Pass")
    pending = sum(1 for r in rows if r[-1] == "Not run")
    out = ["# Jackfruit Phase-3: Test Plan Document", "",
           "Project 28 - AI-Based Legal Assistant | Team ZENITH404", "",
           "## Scope and approach", "",
           "- **Unit (UT)** and **Integration (IT)** cases are automated with pytest (`backend/tests`). "
           "Their *Actual Result* and *Test Result* below come from a real run of the suite "
           f"(`{summary}`).",
           "- **System (ST)** and **UI renderer (UT-05)** cases need a browser and are marked "
           "*Pending manual execution*; execute them against the docker-compose stack and record the outcome.",
           "- Case IDs follow the SRS traceability matrix: UT-01 chat, UT-02 classifier, UT-03 retrieval, "
           "UT-04 generation, UT-05 UI renderer, UT-06 case law, UT-07 templates, UT-08 document analysis, "
           "UT-09 feedback, UT-10 admin, UT-11 authentication/security (added), IT-xx integration, ST-xx system.",
           "- Both valid and invalid inputs are covered (e.g. empty/oversize/mismatched uploads, weak passwords).",
           "", f"**Totals:** {total} cases | {passed} passed (automated) | {pending} pending manual execution.", "",
           "| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |",
           "|---|---|---|---|---|---|---|---|---|"]
    out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
    (docs / "05_Test_Plan.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {total} cases ({passed} passed, {pending} pending). {summary}")


if __name__ == "__main__":
    main()
