"""
Loads data/sample_meter.csv into the database as a "demo" Dataset and
runs the analysis pipeline on it, so the dashboard has something to show
immediately after setup (or after a Render free-tier restart wipes SQLite).

Run:  python -m backend.seed
Safe to run repeatedly — skips creating a duplicate demo dataset if one
with the same name already exists.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from backend.database import SessionLocal, init_db
from backend.models import Dataset, Reading
from backend.services.pipeline_service import run_pipeline

DEMO_CSV = Path(__file__).parent.parent / "data" / "sample_meter.csv"
DEMO_NAME = "Demo household (30 days)"


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Dataset).filter(Dataset.name == DEMO_NAME).first()
        if existing:
            print(f"Demo dataset already exists (id={existing.id}) — skipping.")
            return

        if not DEMO_CSV.exists():
            print(f"No demo CSV found at {DEMO_CSV}. Run "
                  f"'python -m data.generate_demo_data' first.")
            return

        dataset = Dataset(name=DEMO_NAME, source="demo")
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        # Read the whole file into memory first, then close it immediately,
        # rather than keeping a file handle open while we parse. This avoids
        # intermittent "I/O operation on closed file" errors on Windows when
        # the project folder is inside OneDrive/Dropbox and the sync client
        # briefly locks or touches the file mid-read.
        with open(DEMO_CSV, newline="", encoding="utf-8") as f:
            content = f.read()

        reader = csv.DictReader(content.splitlines())
        rows = [
            Reading(
                dataset_id=dataset.id,
                timestamp=datetime.fromisoformat(row["timestamp"]),
                kwh=float(row["kwh"]),
            )
            for row in reader
        ]
        db.bulk_save_objects(rows)
        db.commit()

        print(f"Seeded demo dataset (id={dataset.id}) with {len(rows)} readings. Running analysis...")
        run_pipeline(db, dataset.id)
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
