"""UT-03: keyword retrieval (FR-05)."""
from app import retrieval


def test_tokenize_removes_stopwords():
    assert retrieval.tokenize("How do I file the FIR?") == ["file", "fir"]


def test_retrieves_relevant_entry(db):
    res = retrieval.retrieve(db, "How to file an FIR with police", "criminal_procedure")
    assert res and "FIR" in res[0].title


def test_retrieval_is_domain_scoped(db):
    res = retrieval.retrieve(db, "file FIR police", "consumer")
    assert all(e.domain == "consumer" for e in res)


def test_no_match_returns_empty(db):
    assert retrieval.retrieve(db, "zzzz qqqq", "tenancy") == []


def test_empty_query_returns_empty(db):
    assert retrieval.retrieve(db, "the and of", "tenancy") == []


def test_limit_respected(db):
    assert len(retrieval.retrieve(db, "arrest police custody bail fir", "criminal_procedure", limit=2)) <= 2


def test_matching_is_case_insensitive(db):
    assert retrieval.retrieve(db, "FILE AN FIR AT THE POLICE STATION", "criminal_procedure")


def test_best_match_ranked_first(db):
    res = retrieval.retrieve(db, "how to file fir police station zero fir", "criminal_procedure")
    assert res[0].entry_type == "procedure"
