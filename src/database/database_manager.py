import psycopg2
from psycopg2 import sql
from config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print("Connected to postgreSQl database")
        except Exception as e:
            print(f"Failed to connect to postgreSQl database: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Postgres database closed")

    def insert_instrument(self, symbol, instrument_type, underlying_symbol = None, strike = None, option_type = None, expiration_date = None):
        query = sql.SQL("""
            INSERT INTO instruments
            (symbol, instrument_type, underlying_symbol, strike, option_type, expiration_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) 
            DO UPDATE SET symbol = EXCLUDED.symbol --Symbol stays the same, but now will return the id of the existing record
            RETURNING id
        """)
        self.cursor.execute(query, (symbol, instrument_type, underlying_symbol, strike, option_type, expiration_date))
        result = self.cursor.fetchone()
        self.connection.commit()
        return result[0] if result else None

    def insert_futures_price(self, instrument_id, price, timestamp):
        query = sql.SQL("""
            INSERT INTO futures_prices (instrument_id, price, timestamp)
            VALUES (%s, %s, %s)
        """)
        self.cursor.execute(query, (instrument_id, price, timestamp))
        self.connection.commit()

    def insert_option_price(self, instrument_id, underlying_price, price, timestamp):
        query = sql.SQL("""
            INSERT INTO option_prices (instrument_id, underlying_price, price, timestamp)
            VALUES (%s, %s, %s, %s)
        """)
        try:
            self.cursor.execute(query, (instrument_id, underlying_price, price, timestamp))
            self.connection.commit()
        except psycopg2.Error as e:
            print(e)

    def insert_option_analytics(self, instrument_id, implied_volatility, delta, gamma, vega, theta, days_to_expiration, timestamp):
        query = sql.SQL("""
            INSERT INTO option_analytics (instrument_id, implied_volatility, delta, gamma, vega, theta, days_to_expiration, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """)
        self.cursor.execute(query, (instrument_id, implied_volatility, delta, gamma, vega, theta, days_to_expiration, timestamp))
        self.connection.commit()

