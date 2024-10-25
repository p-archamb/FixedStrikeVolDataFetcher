
import databento as db
import asyncio
from datetime import datetime

import pytz

from src.analytics.analytics import OptionsAnalytics
from config import DATABENTO_KEY, ES_FUTURES_SYMBOL
from src.models.option import Option
from src.models.option_manager import OptionManager
from src.utils import parse_friday_expiration_date
from src.utils.contract_generation import generate_contracts
from src.utils.date_utils import get_next_four_fridays
from src.database.database_manager import DatabaseManager

class DataFetcher:
    def __init__(self):
        self.option_manager = OptionManager()
        self.es_options = []
        self.client = None
        self.es_futures_symbol = ES_FUTURES_SYMBOL
        self.es_futures_price = None
        self.futures_prices_received = False
        self.options_prices_received = False
        self.futures_symbol_to_instrument_id = {}
        self.organized_options_prices_es = {}
        self.option_analytics = OptionsAnalytics(0.05, 0)
        self.db_manager = DatabaseManager()


    async def setup_connection(self, schema, symbol_subscription):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.client = db.Live(key = DATABENTO_KEY)
                self.client.subscribe(
                    dataset="GLBX.MDP3",
                    schema= schema,
                    stype_in="raw_symbol",
                    symbols=[symbol_subscription]
                )
                break #break out of attempt loop
            except Exception as e:
                if attempt < max_attempts - 1:
                    print (f"Connection attempt {attempt + 1} failed: {e}. Retrying")
                    await asyncio.sleep(3)
                else:
                    print(f"Failed to connect after {max_attempts} attemps: {e}")


    #Function will fetch data from databento. Needs to first get current futures price to
    #determine which options strikes to get. Once options are received will call py_vollib library
    # to calculate iv, delta, gamma since databento does not provide this info.
    #Postgres database will open connection before any connection to databento is opened, and will close
    #after all data/analytics has been written to the database
    async def fetch_data(self):
        self.futures_prices_received = False
        self.options_prices_received = False
        self.es_futures_price = None
        self.futures_symbol_to_instrument_id = {}
        self.organized_options_prices_es = {}

        start_time = datetime.now()
        print(f"Starting data fetch at {start_time}")
        self.db_manager.connect()

        await self.setup_connection("trades", self.es_futures_symbol)
        try:
            await self.process_futures()
            if self.futures_prices_received:
                await self.process_options()
                if self.options_prices_received:
                    self.process_analytics()

        except Exception as e:
            print(f"Error during data fetch: {e}")
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        print(f"Execution time: {execution_time} seconds")
        self.db_manager.close()

    async def process_futures(self):
        self.futures_prices_received = False

        async for record in self.client:
            #Databento first sends symbol mapping messages when subscription start. Create mapping for reference to trade data
            if isinstance(record, db.SymbolMappingMsg):
                await self.futures_contracts_callback(record)
            else: #not symbol mapping message, actual trade data
                await self.futures_callback(record)
            if self.futures_prices_received:
                await self.close_connection()
                break

    #map instrument id to symbol in self.futures_symbol_to_instrument_id dictionary
    async def futures_contracts_callback(self, record):
        if isinstance(record, db.SymbolMappingMsg):
            instrument_id = record.hd.instrument_id
            symbol = record.stype_in_symbol
            print(f"Current Contract - {symbol} has an Instrument ID of {instrument_id}")
            self.futures_symbol_to_instrument_id[instrument_id] = symbol

    #get actual futures trading data. If the trade record instrument id matches the one in our dictionary
    # and is mapped to the futures symbol we are subscribed to, then save the futures price to self.es_futures_price
    # set futures_prices_received to True to continue options retrieval
    async def futures_callback(self, record):
        instrument_id = getattr(record, 'instrument_id', None)
        price = getattr(record, 'price', None)
        symbol = self.futures_symbol_to_instrument_id.get(instrument_id)
        if price is not None:
            converted_price = price / 1_000_000_000
            if symbol == self.es_futures_symbol:
                self.es_futures_price = converted_price
                db_instrument_id = self.db_manager.insert_instrument(symbol, 'FUTURE')
                if db_instrument_id is None:
                    print(f"Failed to insert futures instrument id to table for {symbol}")
                self.db_manager.insert_futures_price(db_instrument_id, converted_price, datetime.now(pytz.timezone('US/Eastern')))
                print(f"Received futures price: {self.es_futures_price}")
                self.futures_prices_received = True

    async def process_options(self):
        self.options_prices_received = False
        fridays = get_next_four_fridays()
        self.es_options = generate_contracts(self.es_futures_price, fridays)
        await self.setup_connection("mbp-1", self.es_options) #Need to reestablish because we close after futures, and need to subscribe to new symbols

        async for record in self.client:
            if isinstance(record, db.SymbolMappingMsg):
                await self.options_contracts_callback(record)
            else:
                await self.options_callback_es(record)
            if self.options_prices_received:
                await self.close_connection()
                break

    #Complete the options symbol to instrument id mapping from DataBentos symbol mapping messages based on our
    #subscribed options symbols
    async def options_contracts_callback(self, record):
        if isinstance(record, db.SymbolMappingMsg):
            instrument_id = record.hd.instrument_id
            symbol = record.stype_in_symbol
            print(f"Options Contract - {symbol} has an Instrument ID of {instrument_id}")

            base_symbol, option_info = symbol.rsplit(' ', 1)
            option_type = option_info[0]
            strike = float(option_info[1:])
            expiration_date = parse_friday_expiration_date(symbol)
            option = Option(symbol, base_symbol, strike, option_type, expiration_date, instrument_id)
            self.option_manager.add_option(option)

    #Get price data for each option we are subscribed to. Store the prices in the options_symbol_prices dictionary
    async def options_callback_es(self, data):
        try:
            instrument_id = getattr(data, 'instrument_id', None)
            if hasattr(data, 'levels') and len(data.levels) > 0:
                level = data.levels[0]
                raw_bid = getattr(level, 'bid_px', None)
                raw_ask = getattr(level, 'ask_px', None)
                if raw_bid is None or raw_ask is None:
                    print(f"Incomplete price data for instrument ID {instrument_id} not using this data.")
                    return
                option_price = (raw_bid + raw_ask) / 2
                price = option_price / 1_000_000_000

                option = self.option_manager.get_option_by_instrument_id(instrument_id)
                if option:
                    option.price = price
                    print(f"Updated price for {option.symbol}: {price}")

                #Once received price for option, will put it into a new nested dictionary
                if all(option.price is not None for option in self.option_manager.get_all_options()):
                    self.options_prices_received = True
                    print("All options prices received.")

        except Exception as e:
            print(f"Failed to process options data: {e}")

    #Function to restructure incoming data into nested dictionary organized by base symbol, strike price and option type
    def restructure_options_data(self, symbol, price):
        base_symbol = symbol[:symbol.rindex(' ')]
        option_parts = symbol.split()[-1]
        option_type = option_parts[0]
        strike = float(option_parts[1:])

        if base_symbol not in self.organized_options_prices_es:
            self.organized_options_prices_es[base_symbol] = {}
        if strike not in self.organized_options_prices_es[base_symbol]:
            self.organized_options_prices_es[base_symbol][strike] = {}
        self.organized_options_prices_es[base_symbol][strike][option_type] = price

    #Function to call the option_analytics class function to calculate iv and greeks. Will also pass in the function to
    #write the data for all options into the postgres database.
    def process_analytics(self):
        options = self.option_manager.get_all_options()
        self.option_analytics.calculate_iv_and_greeks(options, self.es_futures_price)
        self.insert_option_data_to_postgres(options)

    #Function to insert all option data into the 3 option tables. Can only be called once all options data is available.
    def insert_option_data_to_postgres(self, options):
        try:
            timestamp = datetime.now(pytz.timezone('US/Eastern'))
            for option in options:

                db_instrument_id = self.db_manager.insert_instrument(option.symbol, 'OPTION', option.base_symbol, option.strike, option.option_type, option.expiration_date)
                if db_instrument_id is None:
                    print(f"Failed to insert options instrument id into table for {option.symbol}")
                    return
                self.db_manager.insert_option_price(db_instrument_id, self.es_futures_price, option.price, timestamp)
                self.db_manager.insert_option_analytics(db_instrument_id, option.iv, option.delta, option.gamma, option.vega, option.theta, option.dte, timestamp)
                print(f"Successfully inserted data into table for {option.symbol}")
        except Exception as e:
            print(f"Failed to insert options data: {e}")

    async def close_connection(self):
        if self.client:
            self.client.terminate()

