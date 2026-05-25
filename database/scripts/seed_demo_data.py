"""Idempotent seed script for the M3 API testing demo.

Creates exactly:
  - 3 users:  admin@lostfound.local (admin), student@lostfound.local (student),
              student2@lostfound.local (student - used to demo the lost-report privacy filter)
  - 3 lost reports owned by `student`
  - 3 found items logged by `admin`
  - 1 confirmed match (Black Backpack lost <-> Black Backpack found)
  - 1 pending claim by `student` on that match
  - 1 unread notification to `student`

Run:  python scripts/seed_demo_data.py
Safe to re-run; every insert checks for an existing row first.
"""
import os
import sys
from datetime import date

# Make the project root importable when running this script directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    Claim, FoundItem, LostReport, Match, Notification, User,
)


def upsert_user(name, email, role, password):
    user = User.query.filter_by(email=email).first()
    if user:
        return user, False
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user, True


def upsert_lost_report(user_id, item_name, description, category, location, date_lost):
    existing = LostReport.query.filter_by(user_id=user_id, item_name=item_name).first()
    if existing:
        return existing, False
    row = LostReport(
        user_id=user_id, item_name=item_name, description=description,
        category=category, location=location, date_lost=date_lost,
    )
    db.session.add(row)
    db.session.flush()
    return row, True


def upsert_found_item(logged_by, item_name, description, category, location_found, date_found):
    existing = FoundItem.query.filter_by(logged_by=logged_by, item_name=item_name).first()
    if existing:
        return existing, False
    row = FoundItem(
        logged_by=logged_by, item_name=item_name, description=description,
        category=category, location_found=location_found, date_found=date_found,
    )
    db.session.add(row)
    db.session.flush()
    return row, True


def upsert_match(lost_report_id, found_item_id, confidence):
    existing = Match.query.filter_by(
        lost_report_id=lost_report_id, found_item_id=found_item_id
    ).first()
    if existing:
        return existing, False
    row = Match(
        lost_report_id=lost_report_id,
        found_item_id=found_item_id,
        confidence_score=confidence,
    )
    db.session.add(row)
    db.session.flush()
    LostReport.query.get(lost_report_id).status = "matched"
    FoundItem.query.get(found_item_id).status = "matched"
    return row, True


def upsert_claim(match_id, claimant_id, notes):
    existing = Claim.query.filter_by(match_id=match_id, claimant_id=claimant_id).first()
    if existing:
        return existing, False
    row = Claim(match_id=match_id, claimant_id=claimant_id, notes=notes, status="pending")
    db.session.add(row)
    db.session.flush()
    return row, True


def upsert_notification(user_id, title, body, link=None):
    existing = Notification.query.filter_by(user_id=user_id, title=title).first()
    if existing:
        return existing, False
    row = Notification(user_id=user_id, title=title, body=body, link=link, is_read=False)
    db.session.add(row)
    db.session.flush()
    return row, True


def main():
    app = create_app()
    counts = {k: 0 for k in (
        "users", "lost_reports", "found_items", "matches", "claims", "notifications",
    )}

    with app.app_context():
        admin, c = upsert_user("Admin User", "admin@lostfound.local",
                               "admin", "Admin123!")
        counts["users"] += int(c)
        student, c = upsert_user("Test Student", "student@lostfound.local",
                                 "student", "Student123!")
        counts["users"] += int(c)
        student2, c = upsert_user("Other Student", "student2@lostfound.local",
                                  "student", "Student123!")
        counts["users"] += int(c)

        r1, c = upsert_lost_report(
            student.user_id, "Black Backpack",
            "Has my laptop and notebooks inside. Black with a red zipper.",
            "bag", "Library 2F", date(2026, 5, 16),
        )
        counts["lost_reports"] += int(c)
        r2, c = upsert_lost_report(
            student.user_id, "Silver Pen",
            "Fountain pen, my name engraved on the clip.",
            "stationery", "Cafeteria table 4", date(2026, 5, 17),
        )
        counts["lost_reports"] += int(c)
        r3, c = upsert_lost_report(
            student.user_id, "Blue Student ID Card",
            "Inside a clear plastic sleeve with a CSU lanyard.",
            "id", "Gym lobby", date(2026, 5, 17),
        )
        counts["lost_reports"] += int(c)

        f1, c = upsert_found_item(
            admin.user_id, "Black Backpack (Library 2F)",
            "Black bag with a red zipper, found on a reading desk.",
            "bag", "Library 2F", date(2026, 5, 16),
        )
        counts["found_items"] += int(c)
        f2, c = upsert_found_item(
            admin.user_id, "Silver Pen (Cafeteria)",
            "Silver fountain pen, small engraving on the clip.",
            "stationery", "Cafeteria table 6", date(2026, 5, 17),
        )
        counts["found_items"] += int(c)
        f3, c = upsert_found_item(
            admin.user_id, "Black Jacket (Gym)",
            "Black hoodie left on a bench.",
            "clothing", "Gym lobby", date(2026, 5, 18),
        )
        counts["found_items"] += int(c)

        m1, c = upsert_match(r1.report_id, f1.item_id, 0.85)
        counts["matches"] += int(c)

        c1, c = upsert_claim(
            m1.match_id, student.user_id,
            "This is my backpack - laptop is a Dell with a CSU sticker on the lid.",
        )
        counts["claims"] += int(c)

        n1, c = upsert_notification(
            student.user_id,
            "Possible match for your lost item",
            "A found item matches your 'Black Backpack' report. Open the lost-report "
            "page to review and claim.",
            link="/reports/{0}".format(r1.report_id),
        )
        counts["notifications"] += int(c)

        db.session.commit()

    total = sum(counts.values())
    print("Seeded:")
    for k, v in counts.items():
        print(f"  - {k:14} {v} created")
    if total == 0:
        print("Already seeded -- nothing to do.")
    else:
        print(f"Total new rows: {total}")
    print("Done.")


if __name__ == "__main__":
    main()
