import databento as db
import asyncio
from datetime import datetime, timedelta
from config import DATABENTO_KEY, ES_FUTRUES_SYMBOL

class DataFetcher:
    def __init__(self):
        self.client = None
        #self.client2 = None
        self.es_futures_symbol = ES_FUTRUES_SYMBOL
        self.es_futures_price = None
        self.futures_prices_received = False
        self.options_prices_received = False
        self.futures_symbol_to_instrument_id = {}

    async def setup_connection(self):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.client = db.Live(key = DATABENTO_KEY)
                #self.client2 = db.Live(key = DATABENTO_KEY)
                #Start receiving data at this point
                self.client.subscribe(
                    dataset="GLBX.MDP3",
                    schema="trades",
                    stype_in="raw_symbol",
                    symbols=[self.es_futures_symbol]
                )
                break #break out of attempt loop
            except Exception as e:
                if attempt < max_attempts - 1:
                    print (f"Connection attempt {attempt + 1} failed: {e}. Retrying")
                    await asyncio.sleep(3)
                else:
                    print(f"Failed to connect after {max_attempts} attemps: {e}")

        #connect to my database

    #Function will fetch data from databento. Needs to first get current futures price to
    #determine which options strikes to get. Once options are received will call py_vollib library
    # to calculate iv, delta, gamma since databento does not provide this info.
    async def fetch_data(self):
        start_time = datetime.now()
        print(f"Starting data fetch at {start_time}")

        try:
            await self.process_futures()
            if self.futures_prices_received:
                await self.process_options()

            self.process_analytics()

        except Exception as e:
            print(f"Error during data fetch: {e}")
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        print(f"Execution time: {execution_time} seconds")

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
                #insert into postgres db
                print(f"Received futures price: {self.es_futures_price}")
                self.futures_prices_received = True

    async def close_connection(self):
        if self.client:
            self.client.terminate()

