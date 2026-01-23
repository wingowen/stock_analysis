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
from eastmoney import get_fundamentals

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Constants
EASTMONEY_BASE_URL = "https://quote.eastmoney.com"
THRESHOLD_VOLUME_RATIO = 0.2  # 成交量比阈值
THRESHOLD_PRICE_CHANGE = 0.05  # 价格变动阈值 (5%)
LOOKBACK_DAYS = 20  # 回溯天数

async def scrape_stock_data(stock_code: str) -> dict | None:
    """
    Scrape stock data from eastmoney using Playwright.
    Prefer structured data from JS variables, fallback to screenshot + OCR.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Visit stock page
            url = f"{EASTMONEY_BASE_URL}/{stock_code}.html"
            await page.goto(url, wait_until="networkidle")
            
            # Try to extract structured data from page
            # Eastmoney often stores data in window objects or data attributes
            data = await page.evaluate("""
                () => {
                    // Try to find stock data in common locations
                    const priceElement = document.querySelector('.price');
                    const volumeElement = document.querySelector('.volume');
                    
                    return {
                        price: priceElement ? priceElement.textContent.trim() : null,
                        volume: volumeElement ? volumeElement.textContent.trim() : null,
                        // Add more fields as needed
                    };
                }
            """)
            
            if data['price'] and data['volume']:
                return {
                    'code': stock_code,
                    'price': float(data['price'].replace(',', '')),
                    'volume': int(data['volume'].replace(',', '')),
                    'date': datetime.now().date(),
                    'source': 'structured'
                }
            else:
                # Fallback to screenshot + OCR
                screenshot_path = f"screenshots/{stock_code}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # OCR processing (placeholder - need to implement region detection)
                # This is a simplified version
                image = cv2.imread(screenshot_path)
                # Assume price and volume are in specific regions
                # You'd need to train or manually define regions
                price_text = pytesseract.image_to_string(image[100:150, 200:300])  # Example coordinates
                volume_text = pytesseract.image_to_string(image[150:200, 200:300])  # Example coordinates
                
                return {
                    'code': stock_code,
                    'price': float(price_text.strip()),
                    'volume': int(volume_text.strip().replace(',', '')),
                    'date': datetime.now().date(),
                    'source': 'ocr'
                }
                
        except Exception as e:
            print(f"Error scraping {stock_code}: {e}")
            return None
        finally:
            await browser.close()

def get_historical_data(stock_code: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    Get historical data for signal calculation using pyeastmoney.
    """
    try:
        # Use pyeastmoney to get historical data
        # Note: Adjust API calls based on actual library capabilities
        # This is a simplified example - you may need to adapt
        data = get_fundamentals(stock_code, 'daily', days)
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error getting historical data for {stock_code}: {e}")
        # Fallback to dummy data
        dates = [datetime.now().date() - timedelta(days=i) for i in range(days)]
        volumes = [1000000 * (0.9 ** i) for i in range(days)]
        prices = [10.0 + np.random.normal(0, 0.1) for _ in range(days)]

        return pd.DataFrame({
            'date': dates,
            'volume': volumes,
            'price': prices
        })

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
    Store detected signal in Supabase.
    """
    try:
        response = supabase.table('signals').insert(signal).execute()
        print(f"Stored signal for {signal['stock_code']}")
        return response
    except Exception as e:
        print(f"Error storing signal: {e}")
        return None

async def main():
    """
    Main function to scan stocks and detect signals.
    """
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