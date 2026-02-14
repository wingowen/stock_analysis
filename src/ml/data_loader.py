"""
Stock Data Loader for ML

股票数据加载器 - 为机器学习准备数据
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path


class StockDataLoader:
    """
    股票数据加载器
    
    从SQLite数据库加载股票数据，为机器学习模型准备
    
    Attributes:
        db_path: SQLite数据库路径
        conn: 数据库连接
    """
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初始化数据加载器
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_stock_list(self) -> List[str]:
        """
        获取所有股票代码列表
        
        Returns:
            股票代码列表
        """
        conn = self.connect()
        df = pd.read_sql_query(
            "SELECT DISTINCT stock_code FROM stock_history ORDER BY stock_code",
            conn
        )
        return df['stock_code'].tolist()
    
    def load_stock_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载单只股票的历史数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            股票历史数据DataFrame
        """
        conn = self.connect()
        
        query = "SELECT * FROM stock_history WHERE stock_code = ?"
        params = [stock_code]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        return df
    
    def load_multiple_stocks(
        self,
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载多只股票的历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            合并的多股票数据
        """
        all_data = []
        
        for code in stock_codes:
            df = self.load_stock_data(code, start_date, end_date)
            if not df.empty:
                all_data.append(df)
        
        if all_data:
            return pd.concat(all_data, ignore_index=False)
        else:
            return pd.DataFrame()
    
    def load_index_constituents(self, index_code: str = '000300') -> pd.DataFrame:
        """
        加载指数成分股列表
        
        Args:
            index_code: 指数代码，默认沪深300
            
        Returns:
            成分股列表
        """
        conn = self.connect()
        df = pd.read_sql_query(
            """SELECT DISTINCT stock_code, stock_name, weight 
               FROM index_constituents 
               WHERE index_code = ? 
               ORDER BY weight DESC""",
            conn,
            params=[index_code]
        )
        return df
    
    def get_data_summary(self) -> dict:
        """
        获取数据摘要信息
        
        Returns:
            数据摘要字典
        """
        conn = self.connect()
        
        # 股票数量
        stock_count = pd.read_sql_query(
            "SELECT COUNT(DISTINCT stock_code) as cnt FROM stock_history",
            conn
        ).iloc[0]['cnt']
        
        # 记录总数
        record_count = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM stock_history",
            conn
        ).iloc[0]['cnt']
        
        # 日期范围
        date_range = pd.read_sql_query(
            "SELECT MIN(date) as min_date, MAX(date) as max_date FROM stock_history",
            conn
        )
        
        return {
            'stock_count': stock_count,
            'record_count': record_count,
            'min_date': date_range.iloc[0]['min_date'],
            'max_date': date_range.iloc[0]['max_date']
        }
    
    def prepare_panel_data(
        self,
        stock_codes: Optional[List[str]] = None,
        features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        准备面板数据（用于机器学习）
        
        Args:
            stock_codes: 股票代码列表，None表示所有股票
            features: 特征列列表，None表示所有数值列
            
        Returns:
            面板数据（wide format）
        """
        if stock_codes is None:
            stock_codes = self.get_stock_list()
        
        # 加载所有数据
        df = self.load_multiple_stocks(stock_codes)
        
        if df.empty:
            return pd.DataFrame()
        
        # 选择特征列
        if features is None:
            features = ['open', 'close', 'high', 'low', 'volume', 'amount', 
                       'pct_change', 'turnover']
        
        # 创建面板数据
        panel_data = []
        for code in stock_codes:
            stock_df = df[df['stock_code'] == code].copy()
            if stock_df.empty:
                continue
            
            for feat in features:
                if feat in stock_df.columns:
                    temp = stock_df[['stock_code', feat]].copy()
                    temp['feature'] = f"{code}_{feat}"
                    temp.rename(columns={feat: 'value'}, inplace=True)
                    panel_data.append(temp)
        
        if panel_data:
            result = pd.concat(panel_data, ignore_index=False)
            return result
        else:
            return pd.DataFrame()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
