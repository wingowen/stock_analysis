# Test script for data sources

import asyncio
from data_sources import StockDataSourceFactory

async def test_akshare():
    """
    Test AKShare data source.
    """
    print("Testing AKShare data source...")
    
    # Create AKShare data source
    data_source = StockDataSourceFactory.create_data_source("akshare")
    
    if data_source:
        # Test getting stock data
        stock_code = "000001"
        print(f"Getting data for stock {stock_code}...")
        data = await data_source.get_stock_data(stock_code)
        
        if data:
            print(f"Successfully got data: {data}")
        else:
            print(f"Failed to get data for {stock_code}")
        
        # Test getting historical data
        print(f"Getting historical data for stock {stock_code}...")
        hist_data = data_source.get_historical_data(stock_code, 10)
        
        if not hist_data.empty:
            print(f"Successfully got historical data with {len(hist_data)} rows")
            print(hist_data.head())
        else:
            print(f"Failed to get historical data for {stock_code}")
    else:
        print("Failed to create AKShare data source")

if __name__ == "__main__":
    asyncio.run(test_akshare())
