#Class to store and manage a dictionary of option objects and a dictionary to map instrument IDs to symbols
class OptionManager:
    def __init__(self):
        self._options = {}
        self._instrument_id_to_symbol = {}

    def add_option(self, option):
        self._options[option.symbol] = option
        self._instrument_id_to_symbol[option.instrument_id] = option.symbol

    def get_option(self, symbol):
        return self._options.get(symbol)

    def get_option_by_instrument_id(self, instrument_id):
        symbol = self._instrument_id_to_symbol.get(instrument_id)
        return self._options.get(symbol)

    def update_option_price(self, symbol, price):
        option = self.get_option(symbol)
        if option:
            option.price = price

    def update_option_greeks(self, symbol, iv, delta, gamma, vega, theta, dte):
        option = self.get_option(symbol)
        if option:
            option.update_greeks(iv, delta, gamma, vega, theta, dte)

    #Returns a dictionary_values object, which is iterable. Its a view, so not mutable
    def get_all_options(self):
        return self._options.values()