#!/usr/bin/env python3
"""
backfill.py
Generate weekly data files for every Friday between from_date and to_date.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_papers
import build_data as build_data_module
import fetch_papers


def fridays_between(from_date: datetime, to_date: datetime) -> list[datetime]:
    """Return every Friday on or after from_date and on or before to_date."""
    dates = []
    # Find the next Friday on/after from_date (4 = Friday).
    days_ahead = (4 - from_date.weekday()) % 7
    first_friday = from_date + timedelta(days=days_ahead)
    d = first_friday
    while d <= to_date:
        dates.append(d)
        d += timedelta(days=7)
    return dates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to-date", default="", help="End date YYYY-MM-DD (defaults to today)")
    args = parser.parse_args()

    from_date = datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc)
    to_date = (
        datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc)
        if args.to_date
        else datetime.now(timezone.utc)
    )

    dates = fridays_between(from_date, to_date)
    print(f"[backfill] Processing {len(dates)} weeks (Fridays):")
    for d in dates:
        print(f"  {d.strftime('%Y-%m-%d (%a)')}")

    for i, date in enumerate(dates, 1):
        date_str = date.strftime("%Y-%m-%d")
        date_key = date.strftime("%Y-%m%d")
        weekly_path = ROOT / "data" / "weekly" / f"{date_key}.json"

        print(f"\n[backfill] === ({i}/{len(dates)}) {date_str} ===")

        if weekly_path.exists():
            print(f"[backfill] {weekly_path.name} already exists. Skipping.")
            continue

        # Fetch papers.
        fetch_papers.main(date_str=date_str)

        raw_path = ROOT / "data" / "raw_papers.json"
        if not raw_path.exists():
            print("[backfill] No papers fetched. Skipping.")
            continue

        papers = json.loads(raw_path.read_text())
        if not papers:
            print("[backfill] No matching papers. Skipping.")
            raw_path.unlink(missing_ok=True)
            continue

        # Analyze.
        analyze_papers.main()

        # Build.
        build_data_module.main(date_str=date_str)

        # Rate-limit pacing between weeks.
        if i < len(dates):
            print("[backfill] Waiting 90 seconds before the next week ...")
            time.sleep(90)

    print("\n[backfill] Done.")


if __name__ == "__main__":
    main()
