import sys
import datetime
import subprocess

mode = sys.argv[1] # 'monthly', 'thursday', 'friday'
today = datetime.date.today()

if mode == 'monthly':
    # 3rd working day logic. Let's do a simple check.
    # working days: mon-fri
    # count working days in this month up to today
    first_day = today.replace(day=1)
    working_days = 0
    curr = first_day
    while curr <= today:
        if curr.weekday() < 5:
            working_days += 1
        curr += datetime.timedelta(days=1)
    
    if working_days != 3:
        print(f"Today is working day {working_days}, not the 3rd. Skipping.")
        sys.exit(0)
    
    # previous month
    last_day_prev = first_day - datetime.timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    
    start_date = first_day_prev.strftime("%Y-%m-%d")
    end_date = last_day_prev.strftime("%Y-%m-%d")
    print(f"Running monthly for {start_date} to {end_date}")
    subprocess.run(["python3", "/root/.openclaw/workspace-shared/openclaw-scripts/finance/send_report_revenue.py", "--start_date", start_date, "--end_date", end_date])

elif mode == 'thursday':
    if today.weekday() != 3:
        print("Today is not Thursday. Skipping.")
        sys.exit(0)
    # week until wednesday (yesterday)
    # from previous saturday
    start_week = today - datetime.timedelta(days=5)
    end_week = today - datetime.timedelta(days=1)
    # accumulato da inizio mese
    first_of_month = today.replace(day=1)
    
    start_date = first_of_month.strftime("%Y-%m-%d")
    end_date = end_week.strftime("%Y-%m-%d")
    print(f"Running thursday for {start_date} to {end_date}")
    subprocess.run(["python3", "/root/.openclaw/workspace-shared/openclaw-scripts/finance/send_report_revenue.py", "--start_date", start_date, "--end_date", end_date])

elif mode == 'friday':
    if today.weekday() != 4:
        print("Today is not Friday. Skipping.")
        sys.exit(0)
    # week until friday (today)
    start_week = today - datetime.timedelta(days=6) # from saturday
    end_week = today
    # accumulato da inizio mese
    first_of_month = today.replace(day=1)
    
    start_date = first_of_month.strftime("%Y-%m-%d")
    end_date = end_week.strftime("%Y-%m-%d")
    print(f"Running friday for {start_date} to {end_date}")
    subprocess.run(["python3", "/root/.openclaw/workspace-shared/openclaw-scripts/finance/send_report_revenue.py", "--start_date", start_date, "--end_date", end_date])
else:
    print("Invalid mode")
    sys.exit(1)
