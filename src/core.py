"""Business logic of the online-education platform (shared by Design A and Design B).

The same functions run (a) inside an AWS Lambda handler (Design B, serverless)
and (b) inside a small WSGI app on always-on VMs (Design A, traditional), so the
two designs execute identical application code and differ only in deployment.
"""
import hashlib
import json
import difflib

# ---- small in-memory "database" (stands in for DynamoDB / RDS in the prototype)
COURSES = [
    {"id": i, "title": f"Course {i}", "teacher": f"Teacher {i % 17}",
     "credits": 1 + i % 4, "tags": ["cloud", "network", "ai", "db"][: 1 + i % 4]}
    for i in range(60)
]
ANSWER_KEY = ["B", "D", "A", "C", "A", "B", "C", "D", "A", "B"]
REFERENCE_ESSAY = (
    "Cloud computing delivers on-demand computing resources over the network. "
    "Its key characteristics are elasticity, resource pooling, measured service "
    "and broad network access, offered as IaaS, PaaS and SaaS."
) * 3


def login(username: str, password: str) -> dict:
    """Password check with PBKDF2 (a deliberately CPU-bound step)."""
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), username.encode(), 20_000)
    return {"user": username, "token": digest.hex()[:32]}


def list_courses(page: int = 0, size: int = 20) -> str:
    """Serialise one page of the course catalogue (light, I/O-style endpoint)."""
    return json.dumps(COURSES[page * size:(page + 1) * size])


def grade_quiz(answers: list, essay: str = "") -> dict:
    """Auto-grade 10 multiple-choice answers and score a short free-text answer
    by similarity to a reference answer (CPU-bound)."""
    mc = sum(1 for a, k in zip(answers, ANSWER_KEY) if a == k)
    sim = difflib.SequenceMatcher(None, essay.lower(), REFERENCE_ESSAY.lower()).ratio() if essay else 0.0
    return {"mc_score": mc, "essay_score": round(sim * 10, 2), "total": round(mc + sim * 10, 2)}


def batch_grade(submissions: list) -> dict:
    """Nightly batch: re-grade a list of submissions and build a summary report."""
    totals = [grade_quiz(s["answers"], s.get("essay", ""))["total"] for s in submissions]
    n = len(totals)
    return {"n": n, "mean": round(sum(totals) / n, 3) if n else 0.0,
            "max": max(totals) if totals else 0.0}
