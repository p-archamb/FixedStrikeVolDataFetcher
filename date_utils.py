import pandas_market_calendars as mcal
from datetime import date, timedelta, datetime, time
import pytz


#Gets the next four trading fridays in the future of todays current date. Returns a list of 4 dates representing the
#next 4 fridays
def get_next_four_fridays():
    today = date.today()
    nyse = mcal.get_calendar('NYSE')
    fridays = []
    current_date = today
    while len(fridays) < 2:
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
def get_week_of_month(expiration_date):
    first_day_of_month = expiration_date.replace(day = 1)
    week_count = 0
    for day in range(1, expiration_date.day +1):
        current_day = first_day_of_month.replace(day = day)
        if current_day.weekday() == expiration_date.weekday():
            week_count += 1
    return week_count

#compares the param date of the last trading day of the month
def is_end_of_month(expiration_date):
    return expiration_date == get_last_trading_day_of_month(expiration_date)

#Returns the last trading day of the month by using the nyse trading days calendar, and taking the range from last calendar
#day to the first calendar day of the given date month. returns the last trading day
def get_last_trading_day_of_month(expiration_date):
    nyse = mcal.get_calendar("NYSE")
    year = expiration_date.year
    month = expiration_date.month
    if month == 12:
        first_day_of_next_month = date(year + 1, 1, 1)
    else:
        first_day_of_next_month = date(year, month + 1, 1)

    last_day_of_month = first_day_of_next_month - timedelta(days=1)
    trading_days = nyse.valid_days(start_date = date(year, month, 1), end_date = last_day_of_month)
    return trading_days[-1].date()

#This parses the entire options symbol to get the actual expiration calendar date. This only works with friday
#expiration dates, but that is the only expirations we are working with for this project.
def parse_friday_expiration_date(symbol):
    month_to_number = {
        'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6,
        'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12
    }
    option_symbol = symbol.split()[0] #Example symbol format: "EW1V4 C5000"
    month_letter = option_symbol[3]
    year_digit = int(option_symbol[4])
    current_year = datetime.now().year
    if year_digit >= int(str(current_year)[-1]):
        symbol_year = current_year
    else:
        symbol_year = current_year + 1
    month_number = month_to_number.get(month_letter)
    first_of_month = date(symbol_year, month_number, 1)
    #3rd Friday of month is The biggest options expiration day of the month, so it has a unique symbol.
    if option_symbol.startswith('ES'):
        third_friday = first_of_month + timedelta(days = (4 - first_of_month.weekday() + 7) % 7 + 14)
        return third_friday
    elif option_symbol.startswith('EW'):
        week_number = int(option_symbol[2])
        first_friday = first_of_month + timedelta(days = (4 - first_of_month.weekday() + 7) % 7)
        return first_friday + timedelta(weeks = week_number - 1)
    else:
        raise ValueError(f"Unknown symbol: {option_symbol}")

#Calculates the time in years(where a year is 252 trading days), from the current timedate to the expiration timedate
def calculate_time_to_expiration(expiration_date):
    current_datetime = datetime.now(pytz.timezone('America/New_York'))
    if isinstance(expiration_date, datetime):
        expiration_datetime = expiration_date.replace(hour = 16, minute = 0, second = 0, microsecond = 0)
    else:
        expiration_datetime = datetime.combine(expiration_date, time(16, 0))
    expiration_datetime = pytz.timezone('America/New_York').localize(expiration_datetime)
    nyse = mcal.get_calendar('NYSE')
    trading_days = nyse.valid_days(start_date = current_datetime.date(), end_date = expiration_datetime.date())

    schedule = nyse.schedule(start_date = current_datetime.date(), end_date = current_datetime.date())
    market_open, market_close = schedule.iloc[0]
    if current_datetime.time() < market_open.time(): #market not open yet, full day
        current_day_trading_time = (market_close - market_open).total_seconds()
    elif current_datetime.time() < market_close.time(): #market is currently open, calculate fraction of day
        current_day_trading_time = (market_close - current_datetime).total_seconds()
    else:
        current_day_trading_time = 0
    full_trading_day_seconds = (market_close - market_open).total_seconds()
    total_trading_time = current_day_trading_time + full_trading_day_seconds * (len(trading_days) - 1) #-1 because we calculate the current day seperately

    #Implied volatility uses time in years, so need to convert
    trading_hours_per_day = 6.5
    trading_days_per_year = 252
    trading_seconds_per_year = trading_days_per_year * trading_hours_per_day * 3600
    time_to_expiration = (total_trading_time / trading_seconds_per_year)
    return time_to_expiration

#Calculate the number of calendar days from today to the expiration date
def calculate_dte(expiration_date):
    current_date = datetime.now(pytz.timezone('America/New_York')).date()
    if isinstance(expiration_date, datetime):
        expiration_date = expiration_date.date()
    dte = (expiration_date - current_date).days
    return dte