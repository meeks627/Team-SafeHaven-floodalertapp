import os
import sys
import time
import schedule
from datetime import datetime

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from data.retrain import run_retrain


def job():
    print(f"[{datetime.now().isoformat()}] Scheduled retrain triggered")
    run_retrain()


schedule.every().day.at("02:00").do(job)

print("Scheduler started. Will retrain daily at 02:00.")
print("Keep this process running (or use Windows Task Scheduler).")

while True:
    schedule.run_pending()
    time.sleep(60)
