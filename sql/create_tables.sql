-- Create the instruments table. This table will hold all futures and options symbols I use so that the other tables can reference
CREATE TABLE IF NOT EXISTS instruments (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    instrument_type VARCHAR(10) NOT NULL CHECK (instrument_type IN ('FUTURE', 'OPTION')),
    underlying_symbol VARCHAR(10),
    strike NUMERIC(10, 2),
    option_type CHAR(1),
    expiration_date DATE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'US/Eastern')
);

--Create the futures prices table
CREATE TABLE IF NOT EXISTS futures_prices (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    price NUMERIC(10, 2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create the options prices table
CREATE TABLE IF NOT EXISTS option_prices (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    underlying_price NUMERIC(10, 2) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create the option analytics table
CREATE TABLE IF NOT EXISTS option_analytics (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    implied_volatility NUMERIC(10, 4),
    delta NUMERIC(10, 4),
    gamma NUMERIC(10, 6),
    vega NUMERIC(10, 6),
    theta NUMERIC(10, 6),
    days_to_expiration INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create the daily summary table
CREATE TABLE IF NOT EXISTS daily_summary (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id),
    date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    days_to_expiration INTEGER,
    opening_price NUMERIC(10, 2),
    closing_price NUMERIC(10, 2),
    previous_closing_price NUMERIC(10, 2),
    high_price NUMERIC(10, 2),
    low_price NUMERIC(10, 2),
    opening_iv NUMERIC(10, 4),
    closing_iv NUMERIC(10, 4),
    previous_closing_iv NUMERIC(10, 4),
    high_iv NUMERIC(10, 4),
    low_iv NUMERIC(10, 4),
    UNIQUE (instrument_id, date)
);