# Stock Analysis MVP
# 极致缩量信号初筛系统

# This script implements the MVP for identifying extreme volume contraction signals
# in Chinese A-share stocks using Playwright scraping and Supabase storage.

import os
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
import cv2
import pytesseract
import numpy as np
import requests
import sqlite3

# Import data sources
from data_sources import StockDataSourceFactory, StockDataSource

# Load environment variables
load_dotenv()

# Database setup
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "stock_signals.db")

# Data source setup
DEFAULT_DATA_SOURCE = os.getenv("DEFAULT_DATA_SOURCE", "akshare")  # Default to AKShare

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# Only create Supabase client if not using SQLite
supabase: Client = None
if not USE_SQLITE:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# Constants
THRESHOLD_VOLUME_RATIO = 0.2  # 成交量比阈值
THRESHOLD_PRICE_CHANGE = 0.05  # 价格变动阈值 (5%)
LOOKBACK_DAYS = 20  # 回溯天数

def init_sqlite_db(db_path: str):
    """
    Initialize SQLite database and create signals table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create signals table
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

async def scrape_stock_data(stock_code: str) -> dict | None:
    """
    Get stock data from the configured data source.
    """
    try:
        # Create data source instance based on configuration
        data_source = StockDataSourceFactory.create_data_source(DEFAULT_DATA_SOURCE)
        
        if data_source:
            # Use the data source to get stock data
            return await data_source.get_stock_data(stock_code)
        else:
            print(f"Failed to create data source: {DEFAULT_DATA_SOURCE}")
            return None
    except Exception as e:
        print(f"Error getting data for {stock_code}: {e}")
        return None

def get_historical_data(stock_code: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    Get historical data for signal calculation from the configured data source.
    """
    try:
        # Create data source instance based on configuration
        data_source = StockDataSourceFactory.create_data_source(DEFAULT_DATA_SOURCE)
        
        if data_source:
            # Use the data source to get historical data
            return data_source.get_historical_data(stock_code, days)
        else:
            print(f"Failed to create data source: {DEFAULT_DATA_SOURCE}")
    except Exception as e:
        print(f"Error getting historical data for {stock_code}: {e}")
    
    # Return empty DataFrame if all else fails
    return pd.DataFrame(columns=['date', 'volume', 'price'])

def detect_signal(stock_code: str, current_data: dict) -> dict | None:
    """
    Detect extreme volume contraction signal.
    """
    if not current_data:
        return None
    
    # Get historical data
    hist_df = get_historical_data(stock_code)
    
    if hist_df.empty:
        return None
    
    # Calculate metrics
    max_volume_recent = hist_df['volume'].max()
    current_volume = current_data['volume']
    volume_ratio = current_volume / max_volume_recent if max_volume_recent > 0 else 1.0

    # Price change over lookback period
    price_change = (current_data['price'] - hist_df['price'].iloc[-1]) / hist_df['price'].iloc[-1] if hist_df['price'].iloc[-1] != 0 else 0.0
    
    # Signal conditions
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

async def store_signal(signal: dict):
    """
    Store detected signal in Supabase or SQLite based on configuration.
    """
    try:
        if USE_SQLITE:
            # Store in SQLite
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
            print(f"Stored signal for {signal['stock_code']} in SQLite")
            return {"status": "success", "db": "sqlite"}
        else:
            # Store in Supabase
            if supabase:
                response = supabase.table('signals').insert(signal).execute()
                print(f"Stored signal for {signal['stock_code']} in Supabase")
                return response
            else:
                print("Supabase not configured")
                return None
    except Exception as e:
        print(f"Error storing signal: {e}")
        return None

async def main():
    """
    Main function to scan stocks and detect signals.
    """
    # Initialize SQLite if using SQLite
    if USE_SQLITE:
        init_sqlite_db(SQLITE_DB_PATH)

    # Example stock codes (A-share format)
    stock_codes = ['000001', '000002', '600000']  # Add more as needed
    
    detected_signals = []
    
    for code in stock_codes:
        print(f"Processing {code}...")
        data = await scrape_stock_data(code)
        if data:
            signal = detect_signal(code, data)
            if signal:
                detected_signals.append(signal)
                await store_signal(signal)
        
        # Rate limiting
        await asyncio.sleep(1)
    
    print(f"Detected {len(detected_signals)} signals")
    return detected_signals

if __name__ == "__main__":
    asyncio.run(main())