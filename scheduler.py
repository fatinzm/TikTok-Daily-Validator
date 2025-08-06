import schedule
import time
import subprocess
from datetime import datetime

def run_validator():
    print(f"Running daily_validator.py at {datetime.now().isoformat()}")
    try:
        subprocess.run(["python", "daily_validator.py"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error running validator:", e)

# Schedule once per day at 12:00 AM
schedule.every().day.at("12:00").do(run_validator)

print("Scheduler started. Waiting for 12:00 daily trigger...")

while True:
    schedule.run_pending()
    time.sleep(60)