#!/usr/bin/env python3
"""
增强版数据获取 - 使用超长时间延迟和多次重试
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import sqlite3
import pandas as pd
import requests

print("="*70)
print("增强版数据获取")
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# 配置 - 超保守策略
BATCH_SIZE = 5          # 每批5只
BATCH_DELAY = 30        # 批次间等待30秒
REQUEST_DELAY = 5       # 每次请求等待5秒
MAX_RETRIES = 5         # 最多重试5次

start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
end_date = datetime.now().strftime('%Y%m%d')

print(f"\n配置:")
print(f"  时间范围: {start_date} 至 {end_date}")
print(f"  批次大小: {BATCH_SIZE} 只")
print(f"  批次延迟: {BATCH_DELAY} 秒")
print(f"  请求延迟: {REQUEST_DELAY} 秒")
print(f"  最大重试: {MAX_RETRIES} 次")

# 从数据库读取成分股
conn = sqlite3.connect('data/stock_data.db')
constituents = pd.read_sql_query(
    "SELECT DISTINCT stock_code, stock_name FROM index_constituents WHERE index_code='000300'",
    conn
)
conn.close()

if constituents.empty:
    print("[ERROR] 没有找到成分股列表")
    sys.exit(1)

stock_codes = constituents['stock_code'].tolist()
print(f"\n[OK] 从数据库读取 {len(stock_codes)} 只成分股")

# 检查已存在的股票
conn = sqlite3.connect('data/stock_data.db')
try:
    existing = pd.read_sql_query("SELECT DISTINCT stock_code FROM stock_history", conn)
    existing_codes = set(existing['stock_code'].tolist())
    print(f"[INFO] 已存在 {len(existing_codes)} 只股票的历史数据")
except:
    existing_codes = set()
    print(f"[INFO] 历史数据表为空")
conn.close()

# 过滤已存在的
codes_to_fetch = [c for c in stock_codes if c not in existing_codes]
total = len(codes_to_fetch)

if not codes_to_fetch:
    print("\n[OK] 所有数据已获取完成！")
    sys.exit(0)

print(f"[INFO] 待获取: {total} 只股票")
print(f"\n等待 10 秒后开始...")
time.sleep(10)

# 数据源函数
def fetch_from_eastmoney(code, attempt=0):
    """从东方财富获取数据"""
    try:
        secid = f"{('1' if code.startswith('6') else '0')}.{code}"
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',
            'fqt': '0',
            'beg': start_date,
            'end': end_date,
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # 增加延迟
        time.sleep(REQUEST_DELAY + random.uniform(0, 3))
        
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and data['data'].get('klines'):
                records = []
                for line in data['data']['klines']:
                    parts = line.split(',')
                    if len(parts) >= 11:
                        records.append({
                            'stock_code': code,
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'low': float(parts[3]),
                            'high': float(parts[4]),
                            'volume': int(float(parts[5])),
                            'amount': float(parts[6]),
                            'amplitude': float(parts[7]),
                            'pct_change': float(parts[8]),
                            'change_amount': float(parts[9]),
                            'turnover': float(parts[10]) if parts[10] else None,
                            'source': 'eastmoney'
                        })
                return pd.DataFrame(records)
        return pd.DataFrame()
    except Exception as e:
        if attempt < MAX_RETRIES - 1:
            wait_time = (2 ** attempt) + random.uniform(1, 3)
            print(f"\n    第 {attempt + 1} 次失败，等待 {wait_time:.1f} 秒后重试...")
            time.sleep(wait_time)
            return fetch_from_eastmoney(code, attempt + 1)
        raise

# 分批获取
successful = 0
failed = []

print("\n" + "="*70)
print("开始获取数据...")
print("="*70)

for batch_start in range(0, min(total, 20), BATCH_SIZE):  # 先获取前20只测试
    batch_end = min(batch_start + BATCH_SIZE, total)
    batch_codes = codes_to_fetch[batch_start:batch_end]
    
    print(f"\n批次 {(batch_start//BATCH_SIZE)+1} ({batch_start+1}-{batch_end}/{total}):")
    
    batch_data = []
    for code in batch_codes:
        print(f"  获取 {code}...", end=" ", flush=True)
        
        try:
            df = fetch_from_eastmoney(code)
            if not df.empty:
                batch_data.append(df)
                successful += 1
                print(f"[OK] {len(df)}条")
            else:
                failed.append(code)
                print("[空数据]")
        except Exception as e:
            failed.append(code)
            print(f"[失败] {str(e)[:40]}")
    
    # 保存批次数据
    if batch_data:
        try:
            combined = pd.concat(batch_data, ignore_index=True)
            conn = sqlite3.connect('data/stock_data.db')
            combined.to_sql('stock_history', conn, if_exists='append', index=False)
            conn.close()
            print(f"  [OK] 已保存 {len(combined)} 条记录到数据库")
        except Exception as e:
            print(f"  [ERROR] 保存失败: {e}")
    
    # 批次延迟
    if batch_end < total and batch_end < 20:
        print(f"\n等待 {BATCH_DELAY} 秒后继续...")
        time.sleep(BATCH_DELAY)

# 最终统计
print("\n" + "="*70)
print("获取完成!")
print("="*70)
print(f"\n统计:")
print(f"  成功: {successful} 只")
print(f"  失败: {len(failed)} 只")

if failed:
    print(f"\n失败列表: {', '.join(failed[:10])}")
    # 保存失败列表
    with open('data/failed_stocks.txt', 'w') as f:
        f.write('\n'.join(failed))
    print(f"已保存到 data/failed_stocks.txt")

# 显示数据库状态
conn = sqlite3.connect('data/stock_data.db')
count = pd.read_sql_query("SELECT COUNT(*) as cnt FROM stock_history", conn).iloc[0]['cnt']
stocks = pd.read_sql_query("SELECT COUNT(DISTINCT stock_code) as cnt FROM stock_history", conn).iloc[0]['cnt']
conn.close()

print(f"\n数据库状态:")
print(f"  总记录数: {count}")
print(f"  股票数量: {stocks}")
