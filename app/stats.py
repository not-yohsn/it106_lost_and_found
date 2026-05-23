"""Aggregate counts for the dashboard."""
from .models import LostReport, FoundItem, Match, Claim, User


def system_stats():
    lost_total = LostReport.query.count()
    matches_total = Match.query.count()
    return {
        "lost_total": lost_total,
        "lost_active": LostReport.query.filter_by(status="reported").count(),
        "lost_matched": LostReport.query.filter_by(status="matched").count(),
        "lost_closed": LostReport.query.filter_by(status="closed").count(),
        "found_total": FoundItem.query.count(),
        "found_logged": FoundItem.query.filter_by(status="logged").count(),
        "found_matched": FoundItem.query.filter_by(status="matched").count(),
        "found_released": FoundItem.query.filter_by(status="released").count(),
        "matches_total": matches_total,
        "claims_pending": Claim.query.filter_by(status="pending").count(),
        "claims_approved": Claim.query.filter_by(status="approved").count(),
        "claims_released": Claim.query.filter_by(status="released").count(),
        "users_total": User.query.count(),
        "match_rate": round(matches_total / lost_total * 100) if lost_total else 0,
    }


def my_stats(user_id):
    return {
        "my_lost": LostReport.query.filter_by(user_id=user_id).count(),
        "my_lost_active": LostReport.query.filter_by(user_id=user_id, status="reported").count(),
        "my_lost_matched": LostReport.query.filter_by(user_id=user_id, status="matched").count(),
        "my_lost_closed": LostReport.query.filter_by(user_id=user_id, status="closed").count(),
        "my_claims_pending": Claim.query.filter_by(claimant_id=user_id, status="pending").count(),
        "my_claims_approved": Claim.query.filter_by(claimant_id=user_id, status="approved").count(),
        "my_claims_released": Claim.query.filter_by(claimant_id=user_id, status="released").count(),
    }
