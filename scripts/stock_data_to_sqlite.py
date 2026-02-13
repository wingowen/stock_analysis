import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak
from typing import List
import time

def get_month_ago_date():
    """获取一个月前的日期"""
    return (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

def get_now_date():
    """获取当前日期"""
    return datetime.now().strftime('%Y%m%d')

def create_stock_table(conn: sqlite3.Connection):
    """创建股票历史数据表"""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        日期 TEXT NOT NULL,
        股票代码 TEXT NOT NULL,
        开盘 REAL,
        收盘 REAL,
        最高 REAL,
        最低 REAL,
        成交量 INTEGER,
        成交额 REAL,
        振幅 REAL,
        涨跌幅 REAL,
        涨跌额 REAL,
        换手率 REAL,
        UNIQUE(日期, 股票代码)
    )
    ''')
    conn.commit()

def insert_stock_data(conn: sqlite3.Connection, df: pd.DataFrame):
    """插入股票数据到数据库"""
    cursor = conn.cursor()
    # 转换数据类型
    df['成交量'] = df['成交量'].astype(int)
    
    # 插入数据，使用replace忽略重复的(日期, 股票代码)组合
    for _, row in df.iterrows():
        cursor.execute('''
        INSERT OR REPLACE INTO stock_history 
        (日期, 股票代码, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['日期'],
            row['股票代码'],
            row['开盘'],
            row['收盘'],
            row['最高'],
            row['最低'],
            row['成交量'],
            row['成交额'],
            row['振幅'],
            row['涨跌幅'],
            row['涨跌额'],
            row['换手率']
        ))
    conn.commit()

def fetch_stock_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """从AKShare获取股票历史数据"""
    print(f"正在获取股票 {stock_code} 从 {start_date} 到 {end_date} 的数据...")
    try:
        # 转换股票代码格式，添加交易所前缀
        if stock_code.startswith('00') or stock_code.startswith('30'):
            symbol = f"sz{stock_code}"
        elif stock_code.startswith('60'):
            symbol = f"sh{stock_code}"
        else:
            symbol = stock_code
        
        df = ak.stock_zh_a_hist_tx(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        
        # 重命名列名以匹配数据库结构
        if not df.empty:
            df.rename(columns={
                'date': '日期',
                'open': '开盘',
                'close': '收盘',
                'high': '最高',
                'low': '最低',
                'amount': '成交额',
                'volume': '成交量'
            }, inplace=True)
            
            # 确保成交量列存在
            if '成交量' not in df.columns:
                df['成交量'] = 0
            
            # 计算缺失的列
            df['振幅'] = ((df['最高'] - df['最低']) / df['开盘'] * 100).round(2)
            df['涨跌幅'] = ((df['收盘'] - df['开盘']) / df['开盘'] * 100).round(2)
            df['涨跌额'] = (df['收盘'] - df['开盘']).round(2)
            df['换手率'] = 0.0  # 腾讯接口可能没有换手率数据，设为0
            
            # 确保股票代码列存在
            df['股票代码'] = stock_code
            
            # 调整列顺序以匹配数据库结构
            required_columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            df = df[required_columns]
        
        return df
    except Exception as e:
        print(f"获取股票 {stock_code} 数据失败: {e}")
        return pd.DataFrame()

def main():
    """主函数"""
    # 获取日期
    month_ago_date = get_month_ago_date()
    now_date = get_now_date()

    df = pd.read_csv("filter_stock_result.csv", dtype={"代码": str})
    code_list = df['代码'].tolist()
    
    # 连接SQLite数据库
    conn = sqlite3.connect('stock_history.db')
    
    # 创建表
    create_stock_table(conn)
    
    # 处理每个股票代码
    for stock_code in code_list:
        time.sleep(1)
        # 检查数据库中该股票的最新日期
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(日期) FROM stock_history WHERE 股票代码 = ?", (stock_code,))
        result = cursor.fetchone()
        latest_date = result[0] if result and result[0] else None
        
        if latest_date:
            # 处理不同的日期格式
            try:
                # 尝试解析带连字符的格式（如2026-01-23）
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
            except ValueError:
                # 尝试解析不带连字符的格式（如20260123）
                latest_dt = datetime.strptime(latest_date, '%Y%m%d')
            # 计算开始日期为最新日期的后一天
            start_date = (latest_dt + timedelta(days=1)).strftime('%Y%m%d')
            print(f"股票 {stock_code} 数据库中最新日期为 {latest_date}，开始获取 {start_date} 以后的数据...")
        else:
            start_date = month_ago_date
            print(f"股票 {stock_code} 数据库中无记录，开始获取 {start_date} 以后的数据...")
        
        # 获取数据
        df = fetch_stock_data(stock_code, start_date, now_date)
        
        if not df.empty:
            print(f"成功获取股票 {stock_code} 的 {len(df)} 条数据")
            
            # 确保列名匹配
            required_columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
            if all(col in df.columns for col in required_columns):
                # 插入数据到数据库
                insert_stock_data(conn, df)
                print(f"成功将股票 {stock_code} 的数据插入到数据库")
            else:
                print(f"股票 {stock_code} 的数据列名不匹配，跳过插入")
                print(f"期望列名: {required_columns}")
                print(f"实际列名: {list(df.columns)}")
        else:
            print(f"股票 {stock_code} 没有获取到数据")
    
    # 关闭数据库连接
    conn.close()
    print("所有股票数据导入完成")

if __name__ == "__main__":
    main()
