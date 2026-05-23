"""Lightweight text-based matching between LostReport and FoundItem.

Scoring rules (max 1.0):
  + 0.4 if categories match
  + 0.1 per shared keyword (item_name + description), capped at 0.4
  + 0.2 if any shared location keyword

A found item must have been found on or after (lost_date - 1 day) to be a
candidate, when both dates are present.

Each candidate is returned together with a list of human-readable reasons
explaining which rules contributed to the score.
"""
import re
from datetime import timedelta

from .models import FoundItem, LostReport

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "with",
    "my", "is", "for", "from", "by", "this", "that", "it", "be", "was",
}
MIN_TOKEN_LEN = 3
DEFAULT_LIMIT = 5
DEFAULT_MIN_SCORE = 0.2


def _tokenize(text):
    if not text:
        return set()
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) >= MIN_TOKEN_LEN}


def _evaluate(lost_report, found_item):
    """Return (score, reasons) — score in [0, 1], reasons is a list of strings."""
    score = 0.0
    reasons = []

    if lost_report.category and lost_report.category == found_item.category:
        score += 0.4
        reasons.append("same category")

    lost_kw = _tokenize(f"{lost_report.item_name} {lost_report.description or ''}")
    found_kw = _tokenize(f"{found_item.item_name} {found_item.description or ''}")
    shared = lost_kw & found_kw
    if shared:
        score += min(0.4, len(shared) * 0.1)
        sample = ", ".join(sorted(shared)[:4])
        plural = "s" if len(shared) != 1 else ""
        reasons.append(f"{len(shared)} shared word{plural} ({sample})")

    shared_loc = _tokenize(lost_report.location or "") & _tokenize(found_item.location_found or "")
    if shared_loc:
        score += 0.2
        reasons.append(f"location overlap ({', '.join(sorted(shared_loc)[:2])})")

    return round(min(1.0, score), 2), reasons


def score(lost_report, found_item):
    s, _ = _evaluate(lost_report, found_item)
    return s


def _date_compatible(lost_date, found_date):
    if not lost_date or not found_date:
        return True
    return found_date >= lost_date - timedelta(days=1)


def find_matches_for_lost(lost_report, limit=DEFAULT_LIMIT, min_score=DEFAULT_MIN_SCORE):
    """Return [(found_item, score, reasons), ...] sorted by score desc."""
    out = []
    for item in FoundItem.query.filter(FoundItem.status == "logged").all():
        if not _date_compatible(lost_report.date_lost, item.date_found):
            continue
        s, reasons = _evaluate(lost_report, item)
        if s >= min_score:
            out.append((item, s, reasons))
    return sorted(out, key=lambda row: row[1], reverse=True)[:limit]


def find_matches_for_found(found_item, limit=DEFAULT_LIMIT, min_score=DEFAULT_MIN_SCORE):
    """Return [(lost_report, score, reasons), ...] sorted by score desc."""
    out = []
    for report in LostReport.query.filter(LostReport.status == "reported").all():
        if not _date_compatible(report.date_lost, found_item.date_found):
            continue
        s, reasons = _evaluate(report, found_item)
        if s >= min_score:
            out.append((report, s, reasons))
    return sorted(out, key=lambda row: row[1], reverse=True)[:limit]
