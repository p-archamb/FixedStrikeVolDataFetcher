#Class representing an option, to hold all necessary data of every option we are subscribed to
class Option:
    def __init__(self, symbol, base_symbol, strike, option_type, expiration_date, instrument_id=None):
        self._symbol = symbol
        self._base_symbol = base_symbol
        self._strike = strike
        self._option_type = option_type
        self._expiration_date = expiration_date
        self._instrument_id = instrument_id
        self._price = None
        self._iv = None
        self._delta = None
        self._gamma = None
        self._vega = None
        self._theta = None
        self._dte = None

    @property
    def symbol(self):
        return self._symbol

    @property
    def base_symbol(self):
        return self._base_symbol

    @property
    def strike(self):
        return self._strike

    @property
    def option_type(self):
        return self._option_type

    @property
    def expiration_date(self):
        return self._expiration_date

    @property
    def instrument_id(self):
        return self._instrument_id

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, price):
        self._price = price

    @property
    def iv(self):
        return self._iv

    @property
    def delta(self):
        return self._delta

    @property
    def gamma(self):
        return self._gamma

    @property
    def vega(self):
        return self._vega

    @property
    def theta(self):
        return self._theta

    @property
    def dte(self):
        return self._dte

    def update_greeks(self, iv, delta, gamma, vega, theta, dte):
        self._iv = iv
        self._delta = delta
        self._gamma = gamma
        self._vega = vega
        self._theta = theta
        self._dte = dte

