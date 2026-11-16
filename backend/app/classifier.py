"""Domain classifier (stage 1 of the query pipeline, FR-03/FR-04).

A transparent weighted-keyword classifier: deterministic, fast, unit-testable.
Returns None when no supported domain scores above the threshold, which makes
the caller return the out-of-scope message instead of guessing.
"""
import re
from typing import Optional

DOMAIN_KEYWORDS = {
    "consumer": {
        "consumer": 3, "refund": 3, "defective": 3, "warranty": 2, "seller": 2, "e-commerce": 2,
        "product": 1, "deficiency": 3, "overcharged": 3, "mrp": 2, "replacement": 2,
        "consumer court": 4, "consumer forum": 4, "order": 1, "delivery": 1, "service": 1,
    },
    "tenancy": {
        "tenant": 3, "landlord": 3, "rent": 3, "lease": 3, "eviction": 3, "evict": 3, "tenancy": 3,
        "security deposit": 4, "rental": 3, "deposit": 1, "flat": 1, "house owner": 3, "landlady": 3,
        "rent agreement": 4, "leave and license": 4,
    },
    "family": {
        "divorce": 4, "marriage": 2, "maintenance": 3, "alimony": 3, "custody": 3, "husband": 2,
        "wife": 2, "domestic violence": 4, "dowry": 3, "adoption": 3, "mutual consent": 3,
        "separation": 2, "spouse": 2, "inheritance": 2, "succession": 2, "will": 1,
    },
    "employment": {
        "employer": 3, "employee": 3, "salary": 3, "wages": 3, "gratuity": 4, "termination": 3,
        "fired": 3, "resignation": 2, "notice period": 3, "workplace": 2, "harassment": 2,
        "posh": 4, "provident fund": 3, "pf": 1, "layoff": 3, "job": 1, "appointment letter": 3,
        "unpaid": 2, "overtime": 2, "labour": 3, "labor": 3,
    },
    "cyber": {
        "cyber": 4, "online fraud": 4, "hacked": 3, "hacking": 3, "phishing": 4, "upi": 3,
        "identity theft": 4, "data breach": 3, "privacy": 2, "morphed": 3, "cyberbullying": 4,
        "online": 1, "sextortion": 4, "scam": 3, "otp": 3, "it act": 4, "social media": 2,
        "account hacked": 4, "fraud": 2, "66a": 3,
    },
    "criminal_procedure": {
        "fir": 4, "arrest": 3, "police": 3, "bail": 4, "complaint": 1, "magistrate": 3,
        "cognizable": 4, "chargesheet": 4, "custody": 1, "zero fir": 4, "bnss": 4, "crpc": 4,
        "detained": 3, "remand": 3, "police station": 3, "anticipatory bail": 5, "warrant": 3,
    },
    "rti": {
        "rti": 5, "right to information": 5, "pio": 4, "public information officer": 5,
        "information commission": 4, "first appeal": 2, "government records": 2,
    },
}

DOMAIN_LABELS = {
    "consumer": "Consumer protection", "tenancy": "Tenancy and rent", "family": "Family law",
    "employment": "Employment and labour", "cyber": "Cyber law and online fraud",
    "criminal_procedure": "Criminal procedure", "rti": "Right to Information",
}

THRESHOLD = 3


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s\-]", " ", text.lower())


def domain_scores(query: str) -> dict:
    text = f" {_normalize(query)} "
    scores = {}
    for domain, words in DOMAIN_KEYWORDS.items():
        total = 0
        for word, weight in words.items():
            if re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", text):
                total += weight
        scores[domain] = total
    return scores


def classify(query: str) -> Optional[str]:
    """Return the best supported domain, or None when out of scope."""
    scores = domain_scores(query)
    best = max(scores, key=lambda d: scores[d])
    if scores[best] < THRESHOLD:
        return None
    return best


def supported_domains() -> list:
    return list(DOMAIN_KEYWORDS.keys())
