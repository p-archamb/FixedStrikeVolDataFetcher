import pytz
from datetime import datetime
from py_vollib.black_scholes_merton.implied_volatility import implied_volatility as bsm_iv
from py_vollib.black_scholes_merton.greeks.analytical import delta, gamma, vega, theta

from date_utils import parse_friday_expiration_date, calculate_time_to_expiration, calculate_dte


class OptionsAnalytics:
    def __init__(self, risk_free_rate, dividend_yield):
        self.risk_free_rate = risk_free_rate
        self.dividend_yield = dividend_yield

    def calculate_iv_and_greeks(self, options_data, underlying_price, insert_data_to_postgres_function):
        iv_greeks = {}
        #For each symbol, get the expiration date and time to expiration
        for symbol, strikes in options_data.items():
            iv_greeks[symbol] = {}
            try:
                expiration_date = parse_friday_expiration_date(symbol)
                time_to_expiration = calculate_time_to_expiration(expiration_date)
                dte = calculate_dte(expiration_date)
                #For each strike, calculate the implied volatility and greeks
                #Good place to use parallel processing
                for strike, options in strikes.items():
                    iv_greeks[symbol][strike] = {}
                    for option_type, price in options.items():
                        try:
                            call_or_put = option_type.lower()
                            iv = bsm_iv(price, underlying_price, strike, time_to_expiration, self.risk_free_rate, self.dividend_yield, call_or_put)
                            delta_value = delta(call_or_put, underlying_price, strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                            gamma_value = gamma(call_or_put, underlying_price, strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                            vega_value = vega(call_or_put, underlying_price, strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                            theta_value = theta(call_or_put, underlying_price, strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                            iv_greeks[symbol][strike][option_type] = {'iv': iv, 'delta': delta_value, 'gamma': gamma_value, 'vega': vega_value, 'theta': theta_value, 'dte': dte}

                            insert_data_to_postgres_function(symbol, strike, option_type, price, underlying_price, expiration_date, iv, delta_value, gamma_value, vega_value, theta_value, dte)
                        except Exception as e:
                            print(f"Error calculating Greeks for {symbol} {strike} {option_type}: {e}")
            except Exception as e:
                print(f"Error with symbol {symbol}: {e}")
        return iv_greeks



