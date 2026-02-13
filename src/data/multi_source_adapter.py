"""
Multi-Source Stock Data Adapter

多数据源股票数据适配器

统一不同数据源的数据格式，确保数据一致性。

支持的数据源：
- AKShare (默认)
- Sina Finance (新浪财经)
- East Money (东方财富直接接口)
- Tencent Finance (腾讯财经)

数据统一格式：
{
    'stock_code': str,      # 股票代码
    'date': str,            # 日期 (YYYY-MM-DD)
    'open': float,          # 开盘价
    'close': float,         # 收盘价
    'high': float,          # 最高价
    'low': float,           # 最低价
    'volume': int,          # 成交量（股）
    'amount': float,        # 成交额（元）
    'amplitude': float,     # 振幅（%）
    'pct_change': float,    # 涨跌幅（%）
    'change_amount': float, # 涨跌额（元）
    'turnover': float,      # 换手率（%）
    'source': str           # 数据来源
}
"""

import re
import json
import logging
import requests
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataSourceAdapter(ABC):
    """数据源适配器基类"""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称"""
        pass
    
    @abstractmethod
    def get_stock_history(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            统一格式的 DataFrame
        """
        pass
    
    def normalize_code(self, code: str) -> str:
        """标准化股票代码"""
        # 移除空格和交易所后缀
        code = code.strip()
        code = re.sub(r'\.(SH|SZ|ss|sz)$', '', code, flags=re.IGNORECASE)
        return code
    
    def standardize_dataframe(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        标准化 DataFrame 格式
        
        Args:
            df: 原始数据
            stock_code: 股票代码
            
        Returns:
            标准化后的 DataFrame
        """
        if df.empty:
            return df
        
        # 添加股票代码和数据源
        df['stock_code'] = self.normalize_code(stock_code)
        df['source'] = self.source_name
        
        # 确保所有标准列存在
        standard_columns = [
            'stock_code', 'date', 'open', 'close', 'high', 'low',
            'volume', 'amount', 'amplitude', 'pct_change', 
            'change_amount', 'turnover', 'source'
        ]
        
        for col in standard_columns:
            if col not in df.columns:
                df[col] = None
        
        # 按标准顺序排列列
        df = df[standard_columns]
        
        return df


class SinaFinanceAdapter(DataSourceAdapter):
    """新浪财经数据源适配器"""
    
    @property
    def source_name(self) -> str:
        return "sina_finance"
    
    def _format_code(self, code: str) -> str:
        """转换为新浪财经代码格式"""
        code = self.normalize_code(code)
        # 上海股票: sh600000, 深圳股票: sz000001
        if code.startswith('6'):
            return f"sh{code}"
        else:
            return f"sz{code}"
    
    def _parse_sina_data(self, text: str) -> pd.DataFrame:
        """解析新浪财经返回的数据"""
        try:
            # 查找JSON数据
            match = re.search(r'\(({.*})\)', text)
            if not match:
                return pd.DataFrame()
            
            data = json.loads(match.group(1))
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            records = []
            for item in data['data']:
                # 新浪财经数据格式: [日期, 开盘价, 最高价, 最低价, 收盘价, 成交量]
                records.append({
                    'date': item[0],
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': int(item[5]),
                })
            
            df = pd.DataFrame(records)
            
            # 计算其他字段
            df['amount'] = df['close'] * df['volume']  # 估算成交额
            df['change_amount'] = df['close'].diff()
            df['pct_change'] = df['close'].pct_change() * 100
            df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100
            df['turnover'] = None  # 新浪财经不直接提供换手率
            
            return df
            
        except Exception as e:
            logger.error(f"解析新浪财经数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_history(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        从新浪财经获取股票历史数据
        
        API: https://quotes.sina.cn/cn/api/quotes.php?
        """
        try:
            code = self._format_code(stock_code)
            
            # 新浪财经历史数据接口
            url = f"https://quotes.sina.cn/cn/api/quotes.php"
            params = {
                'symbol': code,
                'from': start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'to': end_date or datetime.now().strftime('%Y-%m-%d'),
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://finance.sina.com.cn/'
            }
            
            logger.debug(f"请求新浪财经: {code}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                df = self._parse_sina_data(response.text)
                if not df.empty:
                    return self.standardize_dataframe(df, stock_code)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"新浪财经获取数据失败 {stock_code}: {e}")
            return pd.DataFrame()


class EastMoneyAdapter(DataSourceAdapter):
    """东方财富直接接口适配器"""
    
    @property
    def source_name(self) -> str:
        return "eastmoney_direct"
    
    def _format_code(self, code: str) -> str:
        """转换为东方财富代码格式"""
        code = self.normalize_code(code)
        # 1.上海股票, 0.深圳股票
        if code.startswith('6'):
            return f"1.{code}"
        else:
            return f"0.{code}"
    
    def get_stock_history(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        从东方财富直接接口获取股票历史数据
        
        API: https://push2his.eastmoney.com/api/qt/stock/kline/get
        """
        try:
            code = self._format_code(stock_code)
            
            # 转换日期格式
            if start_date:
                start_date = start_date.replace('-', '')
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            if end_date:
                end_date = end_date.replace('-', '')
            else:
                end_date = datetime.now().strftime('%Y%m%d')
            
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': code,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K
                'fqt': '0',    # 不复权
                'beg': start_date,
                'end': end_date,
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/'
            }
            
            logger.debug(f"请求东方财富: {code}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' not in data or not data['data'] or 'klines' not in data['data']:
                    return pd.DataFrame()
                
                records = []
                for line in data['data']['klines']:
                    # 格式: 日期,开盘价,收盘价,最低价,最高价,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
                    parts = line.split(',')
                    if len(parts) >= 11:
                        records.append({
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
                        })
                
                df = pd.DataFrame(records)
                if not df.empty:
                    return self.standardize_dataframe(df, stock_code)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"东方财富获取数据失败 {stock_code}: {e}")
            return pd.DataFrame()


class TencentFinanceAdapter(DataSourceAdapter):
    """腾讯财经数据源适配器"""
    
    @property
    def source_name(self) -> str:
        return "tencent_finance"
    
    def _format_code(self, code: str) -> str:
        """转换为腾讯财经代码格式"""
        code = self.normalize_code(code)
        # sh600000, sz000001
        if code.startswith('6'):
            return f"sh{code}"
        else:
            return f"sz{code}"
    
    def get_stock_history(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        从腾讯财经获取股票历史数据
        
        API: https://web.ifzq.gtimg.cn/appstock/finance_panel/getfqkline
        """
        try:
            code = self._format_code(stock_code)
            
            url = "https://web.ifzq.gtimg.cn/appstock/finance_panel/getfqkline"
            params = {
                'param': f"{code},day,,,1000,qfq",  # 前复权，最多1000天
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://stock.finance.qq.com/'
            }
            
            logger.debug(f"请求腾讯财经: {code}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 解析腾讯财经数据格式
                key = code
                if key in data.get('data', {}):
                    klines = data['data'][key].get('qfqday', [])
                    
                    records = []
                    for item in klines:
                        # 格式: [日期, 开盘价, 收盘价, 最低价, 最高价, 成交量]
                        if len(item) >= 6:
                            records.append({
                                'date': item[0],
                                'open': float(item[1]),
                                'close': float(item[2]),
                                'low': float(item[3]),
                                'high': float(item[4]),
                                'volume': int(item[5]),
                            })
                    
                    df = pd.DataFrame(records)
                    
                    # 计算其他字段
                    if not df.empty:
                        df['amount'] = df['close'] * df['volume']
                        df['change_amount'] = df['close'].diff()
                        df['pct_change'] = df['close'].pct_change() * 100
                        df['amplitude'] = ((df['high'] - df['low']) / df['close'].shift(1)) * 100
                        df['turnover'] = None
                        
                        # 过滤日期范围
                        if start_date:
                            df = df[df['date'] >= start_date]
                        if end_date:
                            df = df[df['date'] <= end_date]
                        
                        return self.standardize_dataframe(df, stock_code)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"腾讯财经获取数据失败 {stock_code}: {e}")
            return pd.DataFrame()


class MultiSourceDataFetcher:
    """
    多数据源获取器
    
    按优先级尝试多个数据源，确保数据获取成功
    """
    
    # 数据源优先级列表
    DEFAULT_SOURCES = [
        'eastmoney_direct',  # 东方财富（数据最完整）
        'sina_finance',      # 新浪财经
        'tencent_finance',   # 腾讯财经
    ]
    
    def __init__(self, sources: Optional[List[str]] = None):
        """
        初始化多数据源获取器
        
        Args:
            sources: 数据源列表，默认使用 DEFAULT_SOURCES
        """
        self.sources = sources or self.DEFAULT_SOURCES
        self.adapters: Dict[str, DataSourceAdapter] = {}
        
        # 初始化适配器
        for source in self.sources:
            if source == 'sina_finance':
                self.adapters[source] = SinaFinanceAdapter()
            elif source == 'eastmoney_direct':
                self.adapters[source] = EastMoneyAdapter()
            elif source == 'tencent_finance':
                self.adapters[source] = TencentFinanceAdapter()
            else:
                logger.warning(f"未知数据源: {source}")
    
    def fetch_stock_history(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_records: int = 5
    ) -> Tuple[pd.DataFrame, str]:
        """
        获取股票历史数据（自动切换数据源）
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            min_records: 最小记录数要求
            
        Returns:
            (DataFrame, 数据源名称)
        """
        for source_name in self.sources:
            if source_name not in self.adapters:
                continue
            
            adapter = self.adapters[source_name]
            logger.info(f"尝试从 {source_name} 获取 {stock_code}...")
            
            try:
                df = adapter.get_stock_history(stock_code, start_date, end_date)
                
                if not df.empty and len(df) >= min_records:
                    logger.info(f"[OK] 从 {source_name} 成功获取 {stock_code}, {len(df)} 条记录")
                    return df, source_name
                elif not df.empty:
                    logger.warning(f"从 {source_name} 获取数据量不足: {len(df)} 条")
                else:
                    logger.warning(f"从 {source_name} 获取数据为空")
                    
            except Exception as e:
                logger.error(f"从 {source_name} 获取失败: {e}")
                continue
        
        logger.error(f"所有数据源都无法获取 {stock_code}")
        return pd.DataFrame(), ""
    
    def fetch_multiple_stocks(
        self,
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        show_progress: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        批量获取多只股票数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            show_progress: 是否显示进度
            
        Returns:
            (合并的DataFrame, 各数据源统计)
        """
        all_data = []
        source_stats: Dict[str, int] = {}
        failed_stocks = []
        
        total = len(stock_codes)
        
        for i, code in enumerate(stock_codes, 1):
            if show_progress:
                print(f"[{i}/{total}] 获取 {code}...")
            
            df, source = self.fetch_stock_history(code, start_date, end_date)
            
            if not df.empty:
                all_data.append(df)
                source_stats[source] = source_stats.get(source, 0) + 1
            else:
                failed_stocks.append(code)
            
            # 添加延迟避免请求过快
            import time
            time.sleep(0.5)
        
        # 合并数据
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
        else:
            result = pd.DataFrame()
        
        # 输出统计
        if show_progress:
            print(f"\n[统计] 成功: {len(stock_codes) - len(failed_stocks)}/{total}")
            print(f"[统计] 数据源分布: {source_stats}")
            if failed_stocks:
                print(f"[统计] 失败: {len(failed_stocks)} 只: {failed_stocks[:5]}...")
        
        return result, source_stats


# 便捷函数
def fetch_stock_history(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    便捷函数：获取单只股票历史数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
        
    Returns:
        标准化格式的 DataFrame
    """
    fetcher = MultiSourceDataFetcher()
    df, _ = fetcher.fetch_stock_history(stock_code, start_date, end_date)
    return df


if __name__ == "__main__":
    # 测试多数据源获取
    print("="*70)
    print("多数据源适配器测试")
    print("="*70)
    
    test_code = "000001"
    
    # 测试各个数据源
    adapters = [
        EastMoneyAdapter(),
        SinaFinanceAdapter(),
        TencentFinanceAdapter(),
    ]
    
    for adapter in adapters:
        print(f"\n测试 {adapter.source_name}:")
        df = adapter.get_stock_history(test_code, "20250201", "20250213")
        if not df.empty:
            print(f"  [OK] 获取 {len(df)} 条记录")
            print(f"  列: {list(df.columns)}")
            print(f"  数据预览:\n{df.head(3)}")
        else:
            print(f"  [FAIL] 获取失败")
    
    # 测试自动切换
    print(f"\n测试自动切换数据源:")
    fetcher = MultiSourceDataFetcher()
    df, source = fetcher.fetch_stock_history(test_code, "20250201", "20250213")
    if not df.empty:
        print(f"  [OK] 从 {source} 获取 {len(df)} 条记录")
    else:
        print(f"  [FAIL] 所有数据源都失败")
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
