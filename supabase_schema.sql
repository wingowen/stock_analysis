-- Create the signals table in Supabase
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    signal_date DATE NOT NULL,
    volume_ratio FLOAT NOT NULL,
    price_change FLOAT NOT NULL,
    max_volume_recent BIGINT NOT NULL,
    current_volume BIGINT NOT NULL,
    current_price FLOAT NOT NULL,
    source VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for better query performance
CREATE INDEX idx_signals_stock_code ON signals(stock_code);
CREATE INDEX idx_signals_signal_date ON signals(signal_date);