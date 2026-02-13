#!/usr/bin/env python3
"""
分批获取沪深300历史数据

使用多数据源适配器，分批获取数据，支持断点续传
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pandas as pd
from data.stock_manager import StockManager
from data.multi_source_adapter import MultiSourceDataFetcher


def fetch_with_retry(fetcher, code, start_date, end_date, max_retries=5):
    """带指数退避重试的数据获取"""
    for attempt in range(max_retries):
        try:
            df, source = fetcher.fetch_stock_history(code, start_date, end_date)
            if not df.empty:
                return df, source
        except Exception as e:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"  重试 {attempt + 1}/{max_retries}, 等待 {wait_time:.1f}s...")
            time.sleep(wait_time)
    return pd.DataFrame(), ""


def main():
    print("="*70)
    print("沪深300历史数据分批获取")
    print("="*70)
    
    # 参数设置
    batch_size = 10  # 每批处理10只股票
    delay_between_batches = 10  # 批次间延迟10秒
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')
    
    print(f"\n参数:")
    print(f"  时间范围: {start_date} 至 {end_date}")
    print(f"  批次大小: {batch_size} 只")
    print(f"  批次延迟: {delay_between_batches} 秒")
    
    # 初始化
    manager = StockManager(enable_proxy=False)
    fetcher = MultiSourceDataFetcher()
    
    # 获取成分股列表
    print("\n获取沪深300成分股列表...")
    try:
        conn = manager._get_connection()
        constituents = pd.read_sql_query(
            "SELECT DISTINCT stock_code, stock_name FROM index_constituents WHERE index_code='000300'",
            conn
        )
        conn.close()
        
        if constituents.empty:
            print("[ERROR] 数据库中没有成分股列表，请先运行 save_hs300_constituents.py")
            return
        
        stock_codes = constituents['stock_code'].tolist()
        print(f"[OK] 从数据库获取 {len(stock_codes)} 只成分股")
        
    except Exception as e:
        print(f"[ERROR] 读取成分股列表失败: {e}")
        return
    
    # 检查已存在的股票
    print("\n检查已获取的数据...")
    try:
        conn = manager._get_connection()
        existing = pd.read_sql_query(
            "SELECT DISTINCT stock_code FROM stock_history",
            conn
        )
        conn.close()
        existing_codes = set(existing['stock_code'].tolist())
        print(f"  已存在: {len(existing_codes)} 只股票")
    except:
        existing_codes = set()
        print("  数据库为空")
    
    # 过滤已存在的
    codes_to_fetch = [c for c in stock_codes if c not in existing_codes]
    print(f"  待获取: {len(codes_to_fetch)} 只股票")
    
    if not codes_to_fetch:
        print("\n[OK] 所有数据已存在！")
        return
    
    # 分批获取
    total = len(codes_to_fetch)
    successful = 0
    failed = []
    source_stats = {}
    
    print(f"\n开始获取数据（共 {total} 只）...")
    print("="*70)
    
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch_codes = codes_to_fetch[batch_start:batch_end]
        
        print(f"\n批次 {batch_start//batch_size + 1}/{(total-1)//batch_size + 1} "
              f"({batch_start+1}-{batch_end}/{total}):")
        
        batch_data = []
        for code in batch_codes:
            print(f"  获取 {code}...", end=" ")
            df, source = fetch_with_retry(fetcher, code, start_date, end_date)
            
            if not df.empty:
                batch_data.append(df)
                successful += 1
                source_stats[source] = source_stats.get(source, 0) + 1
                print(f"[OK] {len(df)}条 {source}")
            else:
                failed.append(code)
                print("[FAIL]")
        
        # 保存批次数据
        if batch_data:
            try:
                combined = pd.concat(batch_data, ignore_index=True)
                manager.save_to_sqlite(combined, table_name="stock_history", if_exists="append")
                print(f"  [OK] 批次数据已保存 ({len(combined)} 条)")
            except Exception as e:
                print(f"  [ERROR] 保存失败: {e}")
        
        # 批次延迟
        if batch_end < total:
            print(f"\n等待 {delay_between_batches} 秒...")
            time.sleep(delay_between_batches)
    
    # 最终统计
    print("\n" + "="*70)
    print("获取完成!")
    print("="*70)
    print(f"\n统计:")
    print(f"  成功: {successful}/{total}")
    print(f"  失败: {len(failed)}")
    print(f"  数据源分布: {source_stats}")
    
    if failed:
        print(f"\n失败列表 ({len(failed)} 只):")
        print(", ".join(failed))
        
        # 保存失败列表
        failed_file = manager.data_dir / "failed_stocks.txt"
        with open(failed_file, 'w') as f:
            f.write("\n".join(failed))
        print(f"\n已保存到: {failed_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，已保存的数据不会丢失")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
