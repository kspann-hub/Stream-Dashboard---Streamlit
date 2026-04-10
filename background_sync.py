"""
background_sync.py — Starts a background thread that syncs CxAlloy data.
Called from app.py on startup. Works on both local and Streamlit Cloud.
"""

import threading
import time

_sync_started = False


def start_background_sync(interval_hours: int = 12):
    global _sync_started
    if _sync_started:
        return
    _sync_started = True

    def sync_loop():
        from sync_logic import init_db, sync_all

        init_db()
        while True:
            try:
                sync_all()
            except Exception as e:
                print(f"Background sync error: {e}")
            time.sleep(interval_hours * 60 * 60)

    t = threading.Thread(target=sync_loop, daemon=True)
    t.start()
    print("Background sync thread started.")