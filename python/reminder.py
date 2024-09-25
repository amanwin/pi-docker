import time
import csv
import requests
from datetime import datetime, timedelta
import schedule

# Constants
CHECK_INTERVAL_SECONDS = 60  # Frequency to check the schedule (in seconds)
DUE_DATE_THRESHOLD_DAYS = 10  # Number of days to check ahead for due records
SCHEDULE_TIME = "07:00"  # Time to run the check (07:00 AM)

# Define today's date
today = datetime.today()

# Function to parse dates
def parse_date(date_str, ignore_month):
    try:
        if ignore_month == 'Y':
            parsed_date = datetime.strptime(date_str, '%d-%b').replace(month=today.month).replace(year=today.year)
        else:
            parsed_date = datetime.strptime(date_str, '%d-%b').replace(year=today.year)
    except ValueError:
        if ignore_month == 'Y':
            parsed_date = datetime.strptime(date_str, '%d-%b-%y').replace(month=today.month).replace(year=today.year)
        else:
            parsed_date = datetime.strptime(date_str, '%d-%b-%y').replace(year=today.year)
    return parsed_date

# Function to identify records due within 10 days
def check_due_records():
    today = datetime.today()

    # Identify records due within the defined threshold days
    due_soon_records = []
    output = ''
    with open('Reminder.csv', mode='r') as file:
        csvFile = csv.DictReader(file)
        for record in csvFile:
            record_date = parse_date(record["Date"], record['Ignore_Month'])
            record['Date'] = record_date.strftime('%d-%b-%Y')  # Add/Update parsed date column in each record
            if today <= record_date <= today + timedelta(days=DUE_DATE_THRESHOLD_DAYS):
                due_soon_records.append(record)

    # Display the results
    if due_soon_records:
        output += "Reminder due within 10 days: \n"
        for idx,record in enumerate(due_soon_records):
            #output += lines['Ticker'] +" : "+ str(price) + "\n"
            output += f"{idx} Date: {record['Date']}, Name: {record['Name']}, Amount: {record['Amount']} \n"
    else:
        output += "No reminder due within 10 days."

    resp = requests.post('http://localhost:8010/message?token=AoT-QLFs2C7FXfm', json={
    "message": output,
    "priority": 8,
    "title": "Reminder"})

print("Done notifying")

# Schedule the task to run at 12:01 AM every day
schedule.every().day.at(SCHEDULE_TIME).do(check_due_records)

# Continuously run the scheduler
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(CHECK_INTERVAL_SECONDS)
