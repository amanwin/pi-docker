import requests
from bs4 import BeautifulSoup
import csv
import schedule
import time
from datetime import datetime, timedelta

# Constants
CHECK_INTERVAL_SECONDS = 60  # Frequency to check the schedule (in seconds)
DUE_DATE_THRESHOLD_DAYS = 10  # Number of days to check ahead for due records
SCHEDULE_TIME = "08:00"  # Time to run the check for reminders (08:00 AM)

output = ''

# Function to parse dates for due reminders
def parse_date(date_str, ignore_month):
    today = datetime.today()
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
        for idx, record in enumerate(due_soon_records):
            output += f"{idx} Date: {record['Date']}, Name: {record['Name']}, Amount: {record['Amount']} \n"
    else:
        output += "No reminder due within 10 days."

    # Send reminder notification
    resp = requests.post('http://192.168.1.23:8010/message?token=AoT-QLFs2C7FXfm', json={
        "message": output,
        "priority": 8,
        "title": "Reminder"
    })
    print("Reminder notification sent")

# Function to check stock prices
def get_float_from_string(val):
    numeric_value = float(val.strip('%'))
    return numeric_value

def check_stock_prices():
    global output
    output = ''  # Reset output for each job execution
    with open('Ticker.csv', mode='r') as file:    
        csvFile = csv.DictReader(file)
        for lines in csvFile:
            if lines['Ticker'] == 'INDEXNSE':
                url_nse = f"https://www.google.com/finance/quote/{lines['Ticker']}:{lines['Exchange']}"
                response = requests.get(url_nse, verify=False)
                soup = BeautifulSoup(response.text, 'html.parser')
                price_up_down_percent = soup.find(class_=lines['Class_Up_Down_Per']).text
                html_class = lines['Class_Price']
                price = soup.find(class_=html_class).text
                if price[0] == '₹':
                    price = price[1:].replace(",", "")
                else:
                    price = price.replace(",", "")
                output += lines['Exchange'] + " : " + str(price) + " UP or Down % : " + price_up_down_percent + "\n"
    
    # Send stock notification
    resp = requests.post('http://192.168.1.23:8010/message?token=Aqp14Y-hXp4_W06', json={
        "message": output,
        "priority": 8,
        "title": "NIFTY 50"
    })
    print('Stock price notification sent')

# Schedule stock price check between 9:15 AM and 3:30 PM, Monday to Friday, every 15 minutes
def schedule_stock_prices():
    now = datetime.now()
    if now.weekday() < 5:  # Monday=0, Friday=4
        if now.time() >= datetime.strptime('09:15', '%H:%M').time() and now.time() <= datetime.strptime('15:30', '%H:%M').time():
            check_stock_prices()

# Schedule the reminder due record check at 08:00 AM every day
schedule.every().day.at(SCHEDULE_TIME).do(check_due_records)

# Schedule the stock price checks every 15 minutes
schedule.every(15).minutes.do(schedule_stock_prices)

# Continuously run the scheduler
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(CHECK_INTERVAL_SECONDS)
