from src.utils.date_utils import get_week_of_month, is_end_of_month


#Generate the option contracts based on the days we want and the current futures price
def generate_contracts(futures_price, days):
    contracts = []
    for i, day in enumerate(days):
        week_of_month = get_week_of_month(day)
        day_of_week = day.strftime("%A") #Format code for the full name of the weekday
        es_options_symbol = get_contract_symbol('ES', int(week_of_month), day_of_week, day)

        if i == 0: #Next expiring Friday
            num_contracts = 25
            step = 10
            extra_contracts = 0
            extra_step = 0
            include_extra = False
        elif i == 1: #2nd Friday expiring
            num_contracts = 50
            step = 10
            extra_contracts = 0
            extra_step = 0
            include_extra = False
        elif i == 2:
            num_contracts = 30
            step = 10
            extra_contracts = 5
            extra_step = 25
            include_extra = True
        else:
            num_contracts = 30
            step = 10
            extra_contracts = 5
            extra_step = 25
            include_extra = True

        strikes = generate_strikes(futures_price, num_contracts, step, extra_contracts, extra_step, include_extra)

        for strike in strikes:
            es_call = f"{es_options_symbol} C{strike}"
            es_put = f"{es_options_symbol} P{strike}"
            contracts.extend([es_call, es_put])

    return contracts


def get_contract_symbol(ticker, week_of_month, day_of_week, date):
    month_to_letter = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M', 7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    contract_mapping = {
        'ES': {
            1: {"Monday": "E1A", "Tuesday": "E1B", "Wednesday": "E1C", "Thursday": "E1D", "Friday": "EW1"},
            2: {"Monday": "E2A", "Tuesday": "E2B", "Wednesday": "E2C", "Thursday": "E2D", "Friday": "EW2"},
            3: {"Monday": "E3A", "Tuesday": "E3B", "Wednesday": "E3C", "Thursday": "E3D", "Friday": "EW3"},
            4: {"Monday": "E4A", "Tuesday": "E4B", "Wednesday": "E4C", "Thursday": "E4D", "Friday": "EW4"},
            5: {"Monday": "E5A", "Tuesday": "E5B", "Wednesday": "E5C", "Thursday": "E5D", "Friday": "EW5"},
            "EndOfMonth": "EW"
        }
    }

    month_letter = month_to_letter[date.month]
    year_digit = str(date.year)[-1]
    if is_end_of_month(date):
        return contract_mapping.get(ticker).get("EndOfMonth") + month_letter + year_digit
    else:
        day_symbol = contract_mapping.get(ticker).get(week_of_month).get(day_of_week)
        return day_symbol + month_letter + year_digit


#Generates a range of tradable strikes around the current futures price
def generate_strikes(center_price, num_contracts, step, extra_contracts, extra_step, include_extra):
    rounded_center_price = round(center_price / 10) * 10
    half_range = (num_contracts // 2) * step
    start_price = rounded_center_price - half_range
    end_price = rounded_center_price + half_range
    strikes = list(range(int(start_price), int(end_price) + step, step)) #add step to include final strike

    if not include_extra:
        return strikes

    lower_strike_rounded = (strikes[0] // extra_step) * extra_step
    lower_strikes_extra = list(range(lower_strike_rounded - (extra_contracts * extra_step * 2), lower_strike_rounded, extra_step)) # *2 because I want more lower strikes compared to upper
    upper_strike_rounded = (strikes[-1] // extra_step) * extra_step
    upper_strikes_extra = list(range(upper_strike_rounded + extra_step, upper_strike_rounded + (extra_contracts * extra_step) + extra_step, extra_step))

    return lower_strikes_extra + strikes + upper_strikes_extra