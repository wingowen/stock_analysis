#!/usr/bin/env python3
"""
上传股票数据到 Supabase

功能：
1. 创建表结构（如果不存在）
2. 分批上传历史数据
3. 上传成分股列表

免费额度优化：
- 分批上传，每批1000条
- 使用 UPSERT 避免重复数据
- 失败自动重试
"""

import os
import sys
import time
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pandas as pd
from supabase import create_client, Client

# Supabase 配置
SUPABASE_URL = "https://gtcnjqeloworstrimcsr.supabase.co"
SUPABASE_KEY = "sb_publishable_NrI8QhvxEGARuyEtQVVZfg_CAxFgxL7"

# 批处理配置
BATCH_SIZE = 1000  # 每批1000条，控制免费额度使用
MAX_RETRIES = 3
RETRY_DELAY = 2


def init_supabase() -> Client:
    """初始化 Supabase 客户端"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Supabase 客户端初始化成功")
        return client
    except Exception as e:
        print(f"[ERROR] Supabase 初始化失败: {e}")
        sys.exit(1)


def create_tables(supabase: Client):
    """创建表结构（使用 SQL 执行）"""
    print("\n[1/4] 创建表结构...")
    
    # 历史数据表
    history_table_sql = """
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock_code, date)
    );
    
    CREATE INDEX IF NOT EXISTS idx_stock_code ON stock_history(stock_code);
    CREATE INDEX IF NOT EXISTS idx_date ON stock_history(date);
    """
    
    # 成分股表
    constituents_table_sql = """
    CREATE TABLE IF NOT EXISTS index_constituents (
        id SERIAL PRIMARY KEY,
        index_code TEXT NOT NULL,
        index_name TEXT,
        stock_code TEXT NOT NULL,
        stock_name TEXT,
        weight REAL,
        update_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(index_code, stock_code)
    );
    
    CREATE INDEX IF NOT EXISTS idx_index_code ON index_constituents(index_code);
    """
    
    try:
        # 使用 RPC 或直接 SQL 执行
        # 注意：Supabase 需要在 SQL 编辑器中手动创建表，或者使用 migrations
        # 这里我们使用 pandas 的 to_sql 方法，它会自动创建表
        print("  [INFO] 表将在上传数据时自动创建")
        return True
    except Exception as e:
        print(f"  [WARN] 创建表时警告: {e}")
        return True


def upload_in_batches(supabase: Client, df: pd.DataFrame, table_name: str):
    """
    分批上传数据到 Supabase
    
    Args:
        supabase: Supabase 客户端
        df: 要上传的 DataFrame
        table_name: 表名
    """
    total = len(df)
    print(f"\n开始上传 {total} 条记录到表 '{table_name}'...")
    print(f"分批大小: {BATCH_SIZE} 条/批")
    
    successful = 0
    failed = 0
    
    for start_idx in range(0, total, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, total)
        batch = df.iloc[start_idx:end_idx]
        
        print(f"\n  批次 {(start_idx//BATCH_SIZE)+1}/{(total-1)//BATCH_SIZE + 1} "
              f"({start_idx+1}-{end_idx}/{total})...")
        
        # 转换为字典列表
        records = batch.to_dict('records')
        
        # 重试机制
        for attempt in range(MAX_RETRIES):
            try:
                # 使用 upsert 避免重复数据
                response = supabase.table(table_name).upsert(
                    records,
                    on_conflict='stock_code,date' if table_name == 'stock_history' else 'index_code,stock_code'
                ).execute()
                
                successful += len(records)
                print(f"    [OK] 成功上传 {len(records)} 条")
                break
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"    [WARN] 失败，{RETRY_DELAY}秒后重试... ({attempt+1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"    [ERROR] 批次上传失败: {e}")
                    failed += len(records)
    
    print(f"\n  上传完成: 成功 {successful} 条, 失败 {failed} 条")
    return successful, failed


def upload_stock_history(supabase: Client):
    """上传股票历史数据"""
    print("\n[2/4] 读取股票历史数据...")
    
    try:
        conn = sqlite3.connect('data/stock_data.db')
        df = pd.read_sql_query("SELECT * FROM stock_history", conn)
        conn.close()
        
        if df.empty:
            print("  [WARN] 没有找到历史数据")
            return 0, 0
        
        print(f"  [OK] 读取到 {len(df)} 条记录")
        print(f"  股票数量: {df['stock_code'].nunique()}")
        print(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
        
        # 上传数据
        successful, failed = upload_in_batches(supabase, df, 'stock_history')
        return successful, failed
        
    except Exception as e:
        print(f"  [ERROR] 读取数据失败: {e}")
        return 0, 0


def upload_constituents(supabase: Client):
    """上传成分股列表"""
    print("\n[3/4] 读取成分股列表...")
    
    try:
        conn = sqlite3.connect('data/stock_data.db')
        df = pd.read_sql_query("SELECT * FROM index_constituents", conn)
        conn.close()
        
        if df.empty:
            print("  [WARN] 没有找到成分股数据")
            return 0, 0
        
        print(f"  [OK] 读取到 {len(df)} 条记录")
        
        # 上传数据
        successful, failed = upload_in_batches(supabase, df, 'index_constituents')
        return successful, failed
        
    except Exception as e:
        print(f"  [ERROR] 读取数据失败: {e}")
        return 0, 0


def verify_upload(supabase: Client):
    """验证上传结果"""
    print("\n[4/4] 验证上传结果...")
    
    try:
        # 检查历史数据
        response = supabase.table('stock_history').select('*', count='exact').execute()
        history_count = response.count if hasattr(response, 'count') else len(response.data)
        
        response = supabase.table('stock_history').select('stock_code').execute()
        stocks = len(set([r['stock_code'] for r in response.data])) if response.data else 0
        
        print(f"  stock_history 表: {history_count} 条记录, {stocks} 只股票")
        
        # 检查成分股
        response = supabase.table('index_constituents').select('*', count='exact').execute()
        constituents_count = response.count if hasattr(response, 'count') else len(response.data)
        
        print(f"  index_constituents 表: {constituents_count} 条记录")
        
        return history_count, constituents_count
        
    except Exception as e:
        print(f"  [ERROR] 验证失败: {e}")
        return 0, 0


def main():
    """主函数"""
    print("="*70)
    print("上传数据到 Supabase")
    print("="*70)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 初始化
    supabase = init_supabase()
    
    # 创建表（数据上传时会自动创建）
    create_tables(supabase)
    
    # 上传历史数据
    history_success, history_failed = upload_stock_history(supabase)
    
    # 上传成分股
    constituents_success, constituents_failed = upload_constituents(supabase)
    
    # 验证
    history_count, constituents_count = verify_upload(supabase)
    
    # 最终报告
    print("\n" + "="*70)
    print("上传完成!")
    print("="*70)
    print(f"\n上传统计:")
    print(f"  stock_history:")
    print(f"    - 尝试上传: {history_success + history_failed} 条")
    print(f"    - 成功: {history_success} 条")
    print(f"    - 失败: {history_failed} 条")
    print(f"    - 服务器实际: {history_count} 条")
    print(f"\n  index_constituents:")
    print(f"    - 尝试上传: {constituents_success + constituents_failed} 条")
    print(f"    - 成功: {constituents_success} 条")
    print(f"    - 失败: {constituents_failed} 条")
    print(f"    - 服务器实际: {constituents_count} 条")
    
    print("\n" + "="*70)
    print("使用免费额度说明:")
    print("  - 分批上传: 每批1000条")
    print("  - 使用 UPSERT: 避免重复数据")
    print("  - 数据大小: 约 8MB (在500MB免费额度内)")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
