#!/usr/bin/env python3
"""
Nightly maintenance script: auto-close overdue attendance sessions with 0 hours.

Rule: if an attendance record is still active (ended_at is NULL) and its
work_date is earlier than today (Moscow time), close it with ended_at = started_at
and hours = 0.0. This prevents time accumulation when an employee forgot to press
"Я ушел" at the end of the day.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure we can import the app package when run from cron
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.database import SessionLocal  # type: ignore
from app.models import Attendance  # type: ignore


def get_moscow_time() -> datetime:
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)


def close_overdue_sessions() -> int:
    """Close all active sessions from previous days with 0 hours.

    Returns the number of records updated.
    """
    db = SessionLocal()
    updated = 0
    try:
        today = get_moscow_time().date()
        stale_records = (
            db.query(Attendance)
            .filter(
                Attendance.ended_at.is_(None),
                Attendance.work_date < today,
            )
            .all()
        )

        for rec in stale_records:
            rec.ended_at = rec.started_at
            rec.hours = 0.0
            db.add(rec)
            updated += 1

        if updated:
            db.commit()
        else:
            db.rollback()

        return updated
    finally:
        db.close()


def main() -> None:
    count = close_overdue_sessions()
    print(f"Auto-closed overdue attendance sessions: {count}")


if __name__ == "__main__":
    main()



