import datetime
import os
import subprocess

# Determine dates based on today
today = datetime.date.today()
weekday = today.weekday() # 0 = Monday, 3 = Thursday, 5 = Saturday

start_date = None
end_date = None
subject_date_str = today.strftime("%Y%m")

if weekday == 3: # Thursday
    # From previous Saturday (5 days ago) to Wednesday (yesterday)
    start_date = today - datetime.timedelta(days=5)
    end_date = today - datetime.timedelta(days=1)
elif weekday == 5: # Saturday
    # From previous Saturday (7 days ago) to Friday (yesterday)
    start_date = today - datetime.timedelta(days=7)
    end_date = today - datetime.timedelta(days=1)
else:
    print("Not Thursday or Saturday, exiting weekly schedule.")
    exit(0)

# Modify the send_report_revenue.py script to use these dates dynamically or just run a parameterized version.
# Actually, let's just create a wrapper that patches the script or we rewrite the script to accept args.
