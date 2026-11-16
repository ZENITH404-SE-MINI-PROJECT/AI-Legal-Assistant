"""UT-02: domain classifier (FR-03, FR-04)."""
import pytest

from app import classifier


@pytest.mark.parametrize("q,expected", [
    ("My landlord is not returning my security deposit", "tenancy"),
    ("The seller refused a refund for a defective phone", "consumer"),
    ("How can I get a divorce by mutual consent?", "family"),
    ("My employer has not paid my salary for two months", "employment"),
    ("I lost money in a UPI scam, what should I do", "cyber"),
    ("How do I file an FIR when police refuse?", "criminal_procedure"),
    ("How to file an RTI application with the PIO", "rti"),
])
def test_supported_domains(q, expected):
    assert classifier.classify(q) == expected


@pytest.mark.parametrize("q", ["What is the best pizza in town", "Tell me a joke", "How do I bake a cake?", "xyz"])
def test_out_of_scope_returns_none(q):
    assert classifier.classify(q) is None


def test_word_boundary_matching():
    assert classifier.domain_scores("the pfizer vaccine")["employment"] == 0


def test_supported_domains_listed():
    assert "tenancy" in classifier.supported_domains()
