import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak
from typing import List
import sys

def get_month_ago_date():
    """获取一个月前的日期"""
    return (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

def get_now_date():
    """获取当前日期"""
    return datetime.now().strftime('%Y%m%d')

def create_concept_table(conn: sqlite3.Connection):
    """创建概念指数历史数据表"""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS concept_index_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        日期 TEXT NOT NULL,
        概念名称 TEXT NOT NULL,
        开盘价 REAL,
        最高价 REAL,
        最低价 REAL,
        收盘价 REAL,
        成交量 INTEGER,
        成交额 REAL,
        UNIQUE(日期, 概念名称)
    )
    ''')
    conn.commit()

def insert_concept_data(conn: sqlite3.Connection, df: pd.DataFrame, concept_name: str):
    """插入概念指数数据到数据库"""
    cursor = conn.cursor()
    
    # 插入数据，使用replace忽略重复的(日期, 概念名称)组合
    for _, row in df.iterrows():
        cursor.execute('''
        INSERT OR REPLACE INTO concept_index_history 
        (日期, 概念名称, 开盘价, 最高价, 最低价, 收盘价, 成交量, 成交额)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['日期'],
            concept_name,
            row['开盘价'],
            row['最高价'],
            row['最低价'],
            row['收盘价'],
            row['成交量'],
            row['成交额']
        ))
    conn.commit()

def fetch_concept_data(concept_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """从AKShare获取概念指数历史数据"""
    print(f"正在获取概念指数 {concept_name} 从 {start_date} 到 {end_date} 的数据...")
    try:
        df = ak.stock_board_concept_index_ths(
            symbol=concept_name,
            start_date=start_date,
            end_date=end_date
        )
        return df
    except Exception as e:
        print(f"获取概念指数 {concept_name} 数据失败: {e}")
        return pd.DataFrame()

def main(concept_list: List[str]):
    """主函数"""
    # 获取日期
    month_ago_date = get_month_ago_date()
    now_date = get_now_date()
    
    # 连接SQLite数据库
    conn = sqlite3.connect('stock_history.db')
    
    # 创建表
    create_concept_table(conn)
    
    # 处理每个概念名称
    for concept_name in concept_list:
        # 获取数据
        df = fetch_concept_data(concept_name, month_ago_date, now_date)
        
        if not df.empty:
            print(f"成功获取概念指数 {concept_name} 的 {len(df)} 条数据")
            
            # 确保列名匹配
            required_columns = ['日期', '开盘价', '最高价', '最低价', '收盘价', '成交量', '成交额']
            if all(col in df.columns for col in required_columns):
                # 插入数据到数据库
                insert_concept_data(conn, df, concept_name)
                print(f"成功将概念指数 {concept_name} 的数据插入到数据库")
            else:
                print(f"概念指数 {concept_name} 的数据列名不匹配，跳过插入")
                print(f"期望列名: {required_columns}")
                print(f"实际列名: {list(df.columns)}")
        else:
            print(f"概念指数 {concept_name} 没有获取到数据")
    
    # 关闭数据库连接
    conn.close()
    print("所有概念指数数据导入完成")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("python concept_index_to_sqlite.py <概念名称1> <概念名称2> ...")
        print("例如:")
        print("python concept_index_to_sqlite.py 人工智能 新能源")
        sys.exit(1)
    
    # 获取命令行参数中的概念名称列表
    concept_list = sys.argv[1:]
    
    # 运行主函数
    main(concept_list)
