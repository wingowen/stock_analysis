"""
Stock Analysis MVP - Core Module

极致缩量信号初筛系统核心模块。
"""

import os
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Optional imports
try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None

from ..data.sources import StockDataSourceFactory

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

# Database settings
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/stock_signals.db")

# Data source settings
DEFAULT_DATA_SOURCE = os.getenv("DEFAULT_DATA_SOURCE", "akshare")

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client only if not using SQLite
supabase = None
if not USE_SQLITE and create_client and SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Signal detection thresholds
THRESHOLD_VOLUME_RATIO = float(os.getenv("THRESHOLD_VOLUME_RATIO", "0.2"))
THRESHOLD_PRICE_CHANGE = float(os.getenv("THRESHOLD_PRICE_CHANGE", "0.05"))
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "20"))


# =============================================================================
# Database Functions
# =============================================================================

def init_sqlite_db(db_path: str) -> None:
    """
    初始化 SQLite 数据库并创建信号表。
    
    Args:
        db_path: SQLite 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            signal_date DATE NOT NULL,
            volume_ratio REAL NOT NULL,
            price_change REAL NOT NULL,
            max_volume_recent INTEGER NOT NULL,
            current_volume INTEGER NOT NULL,
            current_price REAL NOT NULL,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"SQLite database initialized at {db_path}")


# =============================================================================
# Data Retrieval
# =============================================================================

async def scrape_stock_data(stock_code: str) -> Optional[Dict[str, Any]]:
    """
    从配置的数据源获取股票实时数据。
    
    Args:
        stock_code: 股票代码，A股格式 (如 '000001', '600000')
        
    Returns:
        包含股票数据的字典，失败时返回 None
    """
    try:
        data_source = StockDataSourceFactory.create_data_source(DEFAULT_DATA_SOURCE)
        
        if data_source:
            return await data_source.get_stock_data(stock_code)
        else:
            print(f"Failed to create data source: {DEFAULT_DATA_SOURCE}")
            return None
    except Exception as e:
        print(f"Error getting data for {stock_code}: {e}")
        return None


def get_historical_data(stock_code: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    获取股票历史数据用于信号计算。
    
    Args:
        stock_code: 股票代码
        days: 回溯天数
        
    Returns:
        包含历史数据的 DataFrame
    """
    try:
        data_source = StockDataSourceFactory.create_data_source(DEFAULT_DATA_SOURCE)
        
        if data_source:
            return data_source.get_historical_data(stock_code, days)
        else:
            print(f"Failed to create data source: {DEFAULT_DATA_SOURCE}")
    except Exception as e:
        print(f"Error getting historical data for {stock_code}: {e}")
    
    return pd.DataFrame(columns=['date', 'volume', 'price'])


# =============================================================================
# Signal Detection
# =============================================================================

def detect_signal(stock_code: str, current_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    检测极致缩量信号。
    
    信号条件：
    1. 当前成交量 < 阈值 × 近期最大成交量 (极致缩量)
    2. 价格变动 < 阈值 (横盘整理)
    
    Args:
        stock_code: 股票代码
        current_data: 当前股票数据
        
    Returns:
        信号数据字典，不满足条件时返回 None
    """
    if not current_data:
        return None
    
    hist_df = get_historical_data(stock_code)
    
    if hist_df.empty:
        return None
    
    max_volume_recent = hist_df['volume'].max()
    current_volume = current_data['volume']
    volume_ratio = current_volume / max_volume_recent if max_volume_recent > 0 else 1.0

    price_change = ((current_data['price'] - hist_df['price'].iloc[-1]) 
                   / hist_df['price'].iloc[-1] if hist_df['price'].iloc[-1] != 0 else 0.0)
    
    low_volume = volume_ratio < THRESHOLD_VOLUME_RATIO
    price_consolidation = abs(price_change) < THRESHOLD_PRICE_CHANGE
    
    if low_volume and price_consolidation:
        return {
            'stock_code': stock_code,
            'signal_date': current_data['date'],
            'volume_ratio': volume_ratio,
            'price_change': price_change,
            'max_volume_recent': max_volume_recent,
            'current_volume': current_volume,
            'current_price': current_data['price'],
            'source': current_data['source']
        }
    
    return None


# =============================================================================
# Signal Storage
# =============================================================================

async def store_signal(signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    存储检测到的信号到数据库。
    
    Args:
        signal: 信号数据字典
        
    Returns:
        存储结果，失败时返回 None
    """
    try:
        if USE_SQLITE:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO signals (
                    stock_code, signal_date, volume_ratio, price_change,
                    max_volume_recent, current_volume, current_price, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal['stock_code'],
                signal['signal_date'],
                signal['volume_ratio'],
                signal['price_change'],
                signal['max_volume_recent'],
                signal['current_volume'],
                signal['current_price'],
                signal['source']
            ))

            conn.commit()
            conn.close()
            print(f"✓ Stored signal for {signal['stock_code']} in SQLite")
            return {"status": "success", "db": "sqlite"}
        else:
            if supabase:
                response = supabase.table('signals').insert(signal).execute()
                print(f"✓ Stored signal for {signal['stock_code']} in Supabase")
                return response
            else:
                print("⚠ Supabase not configured")
                return None
    except Exception as e:
        print(f"✗ Error storing signal: {e}")
        return None


# =============================================================================
# Main Entry
# =============================================================================

async def main(stock_codes: Optional[list] = None) -> list:
    """
    主函数：扫描股票并检测信号。
    
    Args:
        stock_codes: 要扫描的股票代码列表，默认使用示例股票
        
    Returns:
        检测到的信号列表
    """
    if USE_SQLITE:
        init_sqlite_db(SQLITE_DB_PATH)

    if stock_codes is None:
        stock_codes = ['000001', '000002', '600000']
    
    print(f"\n{'='*60}")
    print(f"开始扫描 {len(stock_codes)} 只股票...")
    print(f"数据源: {DEFAULT_DATA_SOURCE}")
    print(f"数据库: {'SQLite' if USE_SQLITE else 'Supabase'}")
    print(f"{'='*60}\n")
    
    detected_signals = []
    
    for i, code in enumerate(stock_codes, 1):
        print(f"[{i}/{len(stock_codes)}] Processing {code}...")
        
        try:
            data = await scrape_stock_data(code)
            if data:
                signal = detect_signal(code, data)
                if signal:
                    detected_signals.append(signal)
                    await store_signal(signal)
                    print(f"  ✓ Signal detected! Volume ratio: {signal['volume_ratio']:.4f}")
            
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  ✗ Error processing {code}: {e}")
    
    print(f"\n{'='*60}")
    print(f"扫描完成！检测到 {len(detected_signals)} 个信号")
    print(f"{'='*60}\n")
    
    return detected_signals


if __name__ == "__main__":
    asyncio.run(main())
