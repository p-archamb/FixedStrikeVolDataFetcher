import pandas_market_calendars as mcal
from datetime import date, timedelta

#Gets the next four trading fridays in the future of todays current date. Returns a list of 4 dates representing the
#next 4 fridays
def get_next_four_fridays():
    today = date.today()
    nyse = mcal.get_calendar('NYSE')
    fridays = []
    current_date = today
    while len(fridays) < 4:
        days_until_friday = (4 - current_date.weekday() + 7) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        next_friday = current_date + timedelta(days = days_until_friday)
        valid_trading_days = nyse.valid_days(start_date = next_friday, end_date = next_friday + timedelta(days = 6))
        if valid_trading_days.empty:
            current_date = next_friday + timedelta(days = 1)
            continue
        next_trading_friday = valid_trading_days[0].date()
        fridays.append(next_trading_friday)
        current_date = next_trading_friday + timedelta(days = 1)
    return fridays

#This function gets how many times in a month a certain day type has happened. Ex: Is the param date is a Thursday, it will return
# which Thursday in the month? The 1-5 occuring Thursday in the month? It loops through the first day of the month to the given
#date. If during the loop, a certain day type( Monday-Sunday) is the same the day type of the given date, we increment
#week_count by 1.
def get_week_of_month(date):
    first_day_of_month = date.replace(day = 1)
    week_count = 0
    for day in range(1, date.day +1):
        current_day = first_day_of_month.replace(day = day)
        if current_day.weekday() == date.weekday():
            week_count += 1
    return week_count

#compares the param date of the last trading day of the month
def is_end_of_month(date):
    return date == get_last_trading_day_of_month(date)

#Returns the last trading day of the month by using the nyse trading days calendar, and taking the range from last calendar
#day to the first calendar day of the given date month. returns the last trading day
def get_last_trading_day_of_month(date):
    nyse = mcal.get_calendar("NYSE")
    year = date.year
    month = date.month
    if month == 12:
        first_day_of_next_month = date(year + 1, 1, 1)
    else:
        first_day_of_next_month = date(year, month + 1, 1)

    last_day_of_month = first_day_of_next_month - timedelta(days=1)
    trading_days = nyse.valid_days(start_date = date(year, month, 1), end_date = last_day_of_month)
    return trading_days[-1].date()