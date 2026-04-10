"""
sync_job.py — Local runner. Run in a separate terminal: python sync_job.py
Uses shared logic from sync_logic.py.
"""

from sync_logic import init_db, sync_all
from apscheduler.schedulers.blocking import BlockingScheduler

SYNC_INTERVAL_MINUTES = 60 * 12  # 12 hours

if __name__ == "__main__":
    print("Starting sync job...")
    init_db()

    # Run once immediately
    sync_all()

    # Then repeat on schedule
    scheduler = BlockingScheduler()
    scheduler.add_job(sync_all, "interval", minutes=SYNC_INTERVAL_MINUTES)
    print(f"\nScheduler running — will re-sync every {SYNC_INTERVAL_MINUTES} minutes. Ctrl+C to stop.")
    scheduler.start()