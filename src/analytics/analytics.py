from py_vollib.black_scholes_merton.implied_volatility import implied_volatility as bsm_iv
from py_vollib.black_scholes_merton.greeks.analytical import delta, gamma, vega, theta

from src.utils.date_utils import calculate_time_to_expiration, calculate_dte


class OptionsAnalytics:
    def __init__(self, risk_free_rate, dividend_yield):
        self.risk_free_rate = risk_free_rate
        self.dividend_yield = dividend_yield

    def calculate_iv_and_greeks(self, options, underlying_price):
        for option in options:
            try:
                time_to_expiration = calculate_time_to_expiration(option.expiration_date)
                iv = bsm_iv(option.price, underlying_price, option.strike, time_to_expiration, self.risk_free_rate, self.dividend_yield, option.option_type.lower())
                delta_value = delta(option.option_type.lower(), underlying_price, option.strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                gamma_value = gamma(option.option_type.lower(), underlying_price, option.strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                vega_value = vega(option.option_type.lower(), underlying_price, option.strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                theta_value = theta(option.option_type.lower(), underlying_price, option.strike, time_to_expiration, self.risk_free_rate, iv, self.dividend_yield)
                dte = calculate_dte(option.expiration_date)
                option.update_greeks(iv, delta_value, gamma_value, vega_value, theta_value, dte)
            except Exception as e:
                print(f"Error calculating greeks for symbol {option.symbol}: {e}")