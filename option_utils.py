import pandas_market_calendars as mcal
from datetime import date, timedelta

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