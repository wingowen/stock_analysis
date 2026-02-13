# SQLite 股票数据管理使用指南

## 简介

现在股票数据默认存储在 SQLite 数据库中，提供更好的查询性能和增量更新能力。

## 数据库结构

数据库文件: `data/stock_data.db`

### 表结构

#### 1. stock_history（股票历史数据表）
```sql
CREATE TABLE stock_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,           -- 股票代码
    date TEXT NOT NULL,                 -- 日期 (YYYY-MM-DD)
    open REAL,                          -- 开盘价
    close REAL,                         -- 收盘价
    high REAL,                          -- 最高价
    low REAL,                           -- 最低价
    volume INTEGER,                     -- 成交量
    amount REAL,                        -- 成交额
    amplitude REAL,                     -- 振幅
    pct_change REAL,                    -- 涨跌幅
    change_amount REAL,                 -- 涨跌额
    turnover REAL,                      -- 换手率
    UNIQUE(stock_code, date)            -- 唯一索引，防止重复数据
);
```

索引:
- `idx_stock_code` - 按股票代码查询
- `idx_stock_date` - 按日期查询
- `idx_stock_code_date` - 按股票代码+日期查询（最快）

#### 2. index_constituents（指数成分股表）
```sql
CREATE TABLE index_constituents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code TEXT NOT NULL,           -- 指数代码
    index_name TEXT,                    -- 指数名称
    stock_code TEXT NOT NULL,           -- 成分股代码
    stock_name TEXT,                    -- 成分股名称
    weight REAL,                        -- 权重
    update_date TEXT                    -- 更新日期
);
```

## 使用方法

### 1. 获取数据（命令行）

```bash
# 获取沪深300数据（保存到 SQLite）
python scripts/fetch_hs300_data.py

# 同时导出 CSV
python scripts/fetch_hs300_data.py --csv

# 获取前10只股票（测试用）
python scripts/fetch_hs300_data.py --limit 10

# 获取上证50数据
python scripts/fetch_hs300_data.py --index 000016

# 指定时间范围
python scripts/fetch_hs300_data.py --start 20230101 --end 20231231
```

### 2. 查询数据（Python）

```python
import sys
sys.path.insert(0, 'src')

from data.stock_manager import StockManager

# 创建管理器
manager = StockManager()

# 查询单只股票历史数据
df = manager.query_stock_history('000001')
print(df)

# 查询指定时间范围
df = manager.query_stock_history(
    '000001',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# 查询所有股票代码
stocks = manager.query_all_stocks()
print(stocks)

# 获取统计信息
print(f"股票数量: {manager.get_stock_count()}")
print(f"总记录数: {manager.get_record_count()}")
```

### 3. 导出 CSV

```python
# 从 SQLite 读取并导出
import pandas as pd
import sqlite3

conn = sqlite3.connect('data/stock_data.db')
df = pd.read_sql_query("SELECT * FROM stock_history WHERE stock_code='000001'", conn)
df.to_csv('000001_history.csv', index=False)
conn.close()
```

## 优势

### vs CSV 单文件
- ✅ 查询更快：毫秒级响应（索引优化）
- ✅ 增量更新：只插入新数据，不用重写整个文件
- ✅ 空间更小：比 CSV 节省 30-50% 空间
- ✅ SQL 查询：支持复杂条件筛选

### vs CSV 分文件
- ✅ 文件数量少：只有一个文件
- ✅ 批量查询快：不需要遍历多个文件
- ✅ 跨股票分析方便：一条 SQL 搞定

## 注意事项

1. **增量更新**: 重复运行脚本会自动跳过已存在的数据（使用 `INSERT OR REPLACE`）
2. **备份**: 定期备份 `data/stock_data.db` 文件
3. **体积**: 沪深300一年数据约 5-10MB，全A股约 200-500MB

## 故障排查

### 数据库被锁定
如果提示数据库被锁定，可能是其他程序正在使用。关闭所有使用该数据库的程序后重试。

### 数据重复
使用 `query_stock_history` 会自动去重，或通过 SQL 查询时使用 `DISTINCT`。

### 查询慢
确保索引已创建：
```sql
SELECT * FROM sqlite_master WHERE type='index';
```
