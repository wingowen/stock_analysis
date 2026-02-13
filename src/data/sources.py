"""
Stock Data Sources Module

提供股票数据源的抽象基类和具体实现：
- SinaFinanceDataSource: 新浪财经数据源
- EastMoneyDataSource: 东方财富数据源
- AKShareDataSource: AKShare数据源(推荐)

使用工厂模式创建数据源实例。
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

import pandas as pd
import requests

# Optional imports
try:
    import akshare as ak
except ImportError:
    ak = None

class StockDataSource(ABC):
    """
    股票数据源抽象基类。
    
    所有数据源实现必须继承此类并实现抽象方法。
    """
    
    @abstractmethod
    async def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时数据。
        
        Args:
            stock_code: A股代码 (如 '000001', '600000')
            
        Returns:
            包含股票数据的字典，失败返回 None
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        获取股票历史数据。
        
        Args:
            stock_code: A股代码
            days: 回溯天数
            
        Returns:
            包含历史数据的 DataFrame
        """
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称。"""
        pass

class SinaFinanceDataSource(StockDataSource):
    """
    Stock data source implementation for Sina Finance.
    """
    
    def __init__(self):
        self._base_url = "https://hq.sinajs.cn"
        self._historical_url = "https://finance.sina.com.cn/realstock/company"
    
    @property
    def source_name(self) -> str:
        return "sina_finance"
    
    async def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock data from Sina Finance.
        """
        try:
            # Convert A-share code to Sina format
            # 000001 -> sz000001, 600000 -> sh600000
            sina_code = f"sz{stock_code}" if stock_code.startswith('0') or stock_code.startswith('3') else f"sh{stock_code}"
            
            # Updated URL with callback parameter to avoid caching issues
            url = f"{self._base_url}/list={sina_code}&_={int(datetime.now().timestamp() * 1000)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://finance.sina.com.cn/',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = response.text
                print(f"Response content: {content}")  # Debug info
                
                # Check if response contains valid data
                if f'hq_str_{sina_code}' in content:
                    # Parse the response format: var hq_str_sz000001="平安银行,14.26,14.25,..."
                    import re
                    match = re.search(rf'hq_str_{sina_code}=\"([^\"]+)\"', content)
                    if match:
                        data_part = match.group(1)
                        stock_data = data_part.split(',')
                        print(f"Parsed data: {stock_data}")  # Debug info
                        
                        if len(stock_data) >= 9:  # Ensure we have enough data
                            # Extract relevant data
                            try:
                                return {
                                    'code': stock_code,
                                    'price': float(stock_data[3]),  # Current price
                                    'volume': int(float(stock_data[8]) * 100),  # Volume in shares (convert from lots)
                                    'date': datetime.now().date(),
                                    'source': self.source_name
                                }
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing stock data: {e}")
                        else:
                            print(f"Insufficient data length: {len(stock_data)}")
                    else:
                        print("Failed to extract data using regex")
                else:
                    print(f"No data found for {sina_code}")
            else:
                print(f"HTTP error: {response.status_code}")
                print(f"Response content: {response.text}")
        except Exception as e:
            print(f"Error getting data from Sina Finance for {stock_code}: {e}")
        
        # Return None if real data fails
        return None
    
    def get_historical_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        Get historical stock data from Sina Finance.
        """
        try:
            # Convert A-share code to Sina format
            sina_code = f"sz{stock_code}" if stock_code.startswith('0') or stock_code.startswith('3') else f"sh{stock_code}"
            
            # Use Sina Finance API to get historical data
            # This is a placeholder for the actual API call
            # In a real implementation, you would use the appropriate API endpoint
            print(f"Attempting to get historical data for {stock_code} from Sina Finance")
            
            # For now, we'll return an empty DataFrame until we implement the actual API call
            # TODO: Implement real historical data fetching from Sina Finance
            return pd.DataFrame(columns=['date', 'volume', 'price'])
        except Exception as e:
            print(f"Error getting historical data from Sina Finance for {stock_code}: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame(columns=['date', 'volume', 'price'])

class EastMoneyDataSource(StockDataSource):
    """
    Stock data source implementation for East Money (original source).
    """
    
    def __init__(self):
        self._base_url = "https://quote.eastmoney.com"
    
    @property
    def source_name(self) -> str:
        return "eastmoney"
    
    async def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock data from East Money.
        This is a simplified version - in the actual implementation, we'd use Playwright.
        """
        # For simplicity, we'll just return mock data for now
        # The original scraping logic is still in main.py
        return None
    
    def get_historical_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        Get historical stock data from East Money.
        """
        try:
            # Use East Money API to get historical data
            # This is a placeholder for the actual API call
            # In a real implementation, you would use the appropriate API endpoint
            print(f"Attempting to get historical data for {stock_code} from East Money")
            
            # For now, we'll return an empty DataFrame until we implement the actual API call
            # TODO: Implement real historical data fetching from East Money
            return pd.DataFrame(columns=['date', 'volume', 'price'])
        except Exception as e:
            print(f"Error getting historical data from East Money for {stock_code}: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame(columns=['date', 'volume', 'price'])

class AKShareDataSource(StockDataSource):
    """
    Stock data source implementation using AKShare.
    """
    
    def __init__(self):
        pass
    
    @property
    def source_name(self) -> str:
        return "akshare"
    
    async def get_stock_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time stock data using AKShare.
        """
        try:
            print(f"Attempting to get real-time data for {stock_code} using AKShare")
            
            # Get all A-share spot data
            stock_spot_df = ak.stock_zh_a_spot()
            
            # Find the specific stock
            stock_data = stock_spot_df[stock_spot_df['代码'] == stock_code]
            
            if not stock_data.empty:
                # Extract relevant data
                row = stock_data.iloc[0]
                return {
                    'code': stock_code,
                    'price': float(row['最新价']),
                    'volume': int(row['成交量'] * 100),  # Convert from lots to shares
                    'date': datetime.now().date(),
                    'source': self.source_name
                }
            else:
                print(f"No real-time data found for {stock_code}")
        except Exception as e:
            print(f"Error getting real-time data from AKShare for {stock_code}: {e}")
        
        # Return None if real data fails
        return None
    
    def get_historical_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        Get historical stock data using AKShare.
        """
        try:
            print(f"Attempting to get historical data for {stock_code} using AKShare")
            
            # Calculate start date
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')  # Get more days to ensure we have enough
            
            # Get historical data
            stock_hist_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if not stock_hist_df.empty:
                # Rename columns to match expected format
                df = pd.DataFrame({
                    'date': pd.to_datetime(stock_hist_df['日期']),
                    'volume': stock_hist_df['成交量'],
                    'price': stock_hist_df['收盘']
                })
                
                # Convert date to date only
                df['date'] = df['date'].dt.date
                
                # Sort by date ascending
                df = df.sort_values('date')
                
                # Limit to the specified number of days
                df = df.tail(days)
                
                print(f"Successfully got historical data with {len(df)} rows")
                return df
            else:
                print("No historical data returned")
        except Exception as e:
            print(f"Error getting historical data from AKShare for {stock_code}: {e}")
        
        # Return empty DataFrame on error
        return pd.DataFrame(columns=['date', 'volume', 'price'])

class StockDataSourceFactory:
    """
    Factory class for creating stock data source instances.
    """
    
    @staticmethod
    def create_data_source(source_name: str) -> Optional[StockDataSource]:
        """
        Create a stock data source instance based on the given name.
        
        Args:
            source_name: Name of the data source (e.g., 'sina_finance', 'eastmoney', 'akshare')
            
        Returns:
            Stock data source instance or None if invalid name
        """
        if source_name == "sina_finance":
            return SinaFinanceDataSource()
        elif source_name == "eastmoney":
            return EastMoneyDataSource()
        elif source_name == "akshare":
            return AKShareDataSource()
        else:
            print(f"Unknown data source: {source_name}")
            return None
