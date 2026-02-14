-- 股票历史数据表
CREATE TABLE IF NOT EXISTS stock_history (
    id SERIAL PRIMARY KEY,
    stock_code TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    close REAL,
    high REAL,
    low REAL,
    volume BIGINT,
    amount REAL,
    amplitude REAL,
    pct_change REAL,
    change_amount REAL,
    turnover REAL,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(stock_code, date)
);

-- 成分股表
CREATE TABLE IF NOT EXISTS index_constituents (
    id SERIAL PRIMARY KEY,
    index_code TEXT NOT NULL,
    index_name TEXT,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    weight REAL,
    update_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(index_code, stock_code)
);

-- 信号表
CREATE TABLE IF NOT EXISTS signals (
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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_stock_code ON stock_history(stock_code);
CREATE INDEX IF NOT EXISTS idx_date ON stock_history(date);
CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_history(stock_code, date);
CREATE INDEX IF NOT EXISTS idx_index_code ON index_constituents(index_code);
CREATE INDEX IF NOT EXISTS idx_signals_stock_code ON signals(stock_code);
CREATE INDEX IF NOT EXISTS idx_signals_signal_date ON signals(signal_date);

-- 启用 RLS (行级安全)
ALTER TABLE stock_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE index_constituents ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;

-- 允许匿名用户读取
CREATE POLICY "Allow anonymous read stock_history" ON stock_history
    FOR SELECT TO anon USING (true);
    
CREATE POLICY "Allow anonymous read constituents" ON index_constituents
    FOR SELECT TO anon USING (true);
    
CREATE POLICY "Allow anonymous read signals" ON signals
    FOR SELECT TO anon USING (true);

-- 允许认证用户所有操作
CREATE POLICY "Allow authenticated all stock_history" ON stock_history
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
    
CREATE POLICY "Allow authenticated all constituents" ON index_constituents
    FOR ALL TO authenticated USING (true) WITH CHECK (true);
    
CREATE POLICY "Allow authenticated all signals" ON signals
    FOR ALL TO authenticated USING (true) WITH CHECK (true);