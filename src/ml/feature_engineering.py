"""
Feature Engineering for Stock Analysis

股票特征工程 - 创建机器学习特征
"""

import pandas as pd
import numpy as np
from typing import List, Optional


class FeatureEngineer:
    """
    股票特征工程类
    
    从原始股票数据中提取机器学习特征
    
    支持的指标:
    - 技术指标: MA, MACD, RSI, KDJ, Bollinger Bands等
    - 统计特征: 均值、方差、偏度、峰度等
    - 量价特征: 成交量变化、资金流向等
    - 时间特征: 星期、月份、季度等
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化特征工程器
        
        Args:
            df: 股票历史数据DataFrame
        """
        self.df = df.copy()
        self.features = []
        
    def add_technical_indicators(self) -> 'FeatureEngineer':
        """
        添加技术指标
        
        Returns:
            self，支持链式调用
        """
        # 简单移动平均线
        for window in [5, 10, 20, 60]:
            self.df[f'MA{window}'] = self.df['close'].rolling(window=window).mean()
            self.features.append(f'MA{window}')
        
        # 指数移动平均线
        self.df['EMA12'] = self.df['close'].ewm(span=12, adjust=False).mean()
        self.df['EMA26'] = self.df['close'].ewm(span=26, adjust=False).mean()
        self.features.extend(['EMA12', 'EMA26'])
        
        # MACD
        self.df['MACD'] = self.df['EMA12'] - self.df['EMA26']
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=9, adjust=False).mean()
        self.df['MACD_Hist'] = self.df['MACD'] - self.df['MACD_Signal']
        self.features.extend(['MACD', 'MACD_Signal', 'MACD_Hist'])
        
        # RSI (相对强弱指数)
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        self.features.append('RSI')
        
        # 布林带
        self.df['BB_Middle'] = self.df['close'].rolling(window=20).mean()
        bb_std = self.df['close'].rolling(window=20).std()
        self.df['BB_Upper'] = self.df['BB_Middle'] + (bb_std * 2)
        self.df['BB_Lower'] = self.df['BB_Middle'] - (bb_std * 2)
        self.df['BB_Width'] = (self.df['BB_Upper'] - self.df['BB_Lower']) / self.df['BB_Middle']
        self.df['BB_Position'] = (self.df['close'] - self.df['BB_Lower']) / (self.df['BB_Upper'] - self.df['BB_Lower'])
        self.features.extend(['BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width', 'BB_Position'])
        
        # 动量指标
        for window in [5, 10, 20]:
            self.df[f'Momentum{window}'] = self.df['close'].diff(window)
            self.features.append(f'Momentum{window}')
        
        return self
    
    def add_statistical_features(self, window: int = 20) -> 'FeatureEngineer':
        """
        添加统计特征
        
        Args:
            window: 滚动窗口大小
            
        Returns:
            self，支持链式调用
        """
        # 波动率
        self.df[f'Volatility_{window}'] = self.df['pct_change'].rolling(window=window).std()
        self.features.append(f'Volatility_{window}')
        
        # 收益率的统计量
        self.df[f'Return_Mean_{window}'] = self.df['pct_change'].rolling(window=window).mean()
        self.df[f'Return_Std_{window}'] = self.df['pct_change'].rolling(window=window).std()
        self.df[f'Return_Skew_{window}'] = self.df['pct_change'].rolling(window=window).skew()
        self.df[f'Return_Kurt_{window}'] = self.df['pct_change'].rolling(window=window).kurt()
        self.features.extend([f'Return_Mean_{window}', f'Return_Std_{window}', 
                             f'Return_Skew_{window}', f'Return_Kurt_{window}'])
        
        # 价格位置（相对于近期高低点）
        self.df['Price_Position'] = (self.df['close'] - self.df['low'].rolling(window=window).min()) / \
                                    (self.df['high'].rolling(window=window).max() - self.df['low'].rolling(window=window).min())
        self.features.append('Price_Position')
        
        # 价格区间突破
        self.df['High_Break'] = (self.df['close'] > self.df['high'].shift(1).rolling(window=window).max()).astype(int)
        self.df['Low_Break'] = (self.df['close'] < self.df['low'].shift(1).rolling(window=window).min()).astype(int)
        self.features.extend(['High_Break', 'Low_Break'])
        
        return self
    
    def add_volume_features(self) -> 'FeatureEngineer':
        """
        添加成交量特征
        
        Returns:
            self，支持链式调用
        """
        # 成交量移动平均
        for window in [5, 10, 20]:
            self.df[f'Volume_MA{window}'] = self.df['volume'].rolling(window=window).mean()
            self.df[f'Volume_Ratio{window}'] = self.df['volume'] / self.df[f'Volume_MA{window}']
            self.features.extend([f'Volume_MA{window}', f'Volume_Ratio{window}'])
        
        # 量价关系
        self.df['Price_Volume_Trend'] = self.df['pct_change'] * self.df['volume']
        self.df['Volume_Price_Corr'] = self.df['volume'].rolling(window=10).corr(self.df['close'])
        self.features.extend(['Price_Volume_Trend', 'Volume_Price_Corr'])
        
        # 资金流向估算
        self.df['Money_Flow'] = (self.df['close'] - self.df['low'] - 
                                 (self.df['high'] - self.df['close'])) / (self.df['high'] - self.df['low']) * self.df['volume']
        self.features.append('Money_Flow')
        
        return self
    
    def add_time_features(self) -> 'FeatureEngineer':
        """
        添加时间特征
        
        Returns:
            self，支持链式调用
        """
        # 确保索引是datetime
        if not isinstance(self.df.index, pd.DatetimeIndex):
            if 'date' in self.df.columns:
                self.df['date'] = pd.to_datetime(self.df['date'])
                self.df.set_index('date', inplace=True)
        
        # 星期几 (0=Monday, 6=Sunday)
        self.df['DayOfWeek'] = self.df.index.dayofweek
        self.df['IsWeekend'] = (self.df.index.dayofweek >= 5).astype(int)
        
        # 月份
        self.df['Month'] = self.df.index.month
        self.df['Quarter'] = self.df.index.quarter
        
        # 是否月初/月末
        self.df['IsMonthStart'] = (self.df.index.day <= 5).astype(int)
        self.df['IsMonthEnd'] = (self.df.index.day >= 25).astype(int)
        
        self.features.extend(['DayOfWeek', 'IsWeekend', 'Month', 'Quarter', 
                             'IsMonthStart', 'IsMonthEnd'])
        
        return self
    
    def add_lag_features(self, lags: List[int] = [1, 2, 3, 5, 10]) -> 'FeatureEngineer':
        """
        添加滞后特征
        
        Args:
            lags: 滞后天数列表
            
        Returns:
            self，支持链式调用
        """
        for lag in lags:
            self.df[f'Close_Lag{lag}'] = self.df['close'].shift(lag)
            self.df[f'Return_Lag{lag}'] = self.df['pct_change'].shift(lag)
            self.df[f'Volume_Lag{lag}'] = self.df['volume'].shift(lag)
            self.features.extend([f'Close_Lag{lag}', f'Return_Lag{lag}', f'Volume_Lag{lag}'])
        
        return self
    
    def add_target_variable(self, forecast_horizon: int = 1, target_type: str = 'return') -> 'FeatureEngineer':
        """
        添加目标变量
        
        Args:
            forecast_horizon: 预测周期（天数）
            target_type: 目标类型 ('return'收益率, 'direction'方向, 'price'价格)
            
        Returns:
            self，支持链式调用
        """
        if target_type == 'return':
            # 未来收益率
            self.df['Target_Return'] = self.df['close'].shift(-forecast_horizon) / self.df['close'] - 1
        elif target_type == 'direction':
            # 涨跌方向 (1=涨, 0=平, -1=跌)
            future_return = self.df['close'].shift(-forecast_horizon) / self.df['close'] - 1
            self.df['Target_Direction'] = np.where(future_return > 0.01, 1,
                                          np.where(future_return < -0.01, -1, 0))
        elif target_type == 'price':
            # 未来价格
            self.df['Target_Price'] = self.df['close'].shift(-forecast_horizon)
        
        return self
    
    def get_features_df(self, drop_na: bool = True) -> pd.DataFrame:
        """
        获取特征DataFrame
        
        Args:
            drop_na: 是否删除包含NA的行
            
        Returns:
            包含所有特征的DataFrame
        """
        if drop_na:
            return self.df.dropna()
        else:
            return self.df
    
    def get_feature_names(self) -> List[str]:
        """
        获取特征名称列表
        
        Returns:
            特征名称列表
        """
        return self.features
    
    @staticmethod
    def normalize_features(df: pd.DataFrame, feature_cols: List[str], method: str = 'zscore') -> pd.DataFrame:
        """
        标准化特征
        
        Args:
            df: 输入DataFrame
            feature_cols: 需要标准化的特征列
            method: 标准化方法 ('zscore', 'minmax', 'robust')
            
        Returns:
            标准化后的DataFrame
        """
        df_normalized = df.copy()
        
        if method == 'zscore':
            for col in feature_cols:
                if col in df.columns:
                    mean = df[col].mean()
                    std = df[col].std()
                    if std != 0:
                        df_normalized[col] = (df[col] - mean) / std
        elif method == 'minmax':
            for col in feature_cols:
                if col in df.columns:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    if max_val != min_val:
                        df_normalized[col] = (df[col] - min_val) / (max_val - min_val)
        elif method == 'robust':
            for col in feature_cols:
                if col in df.columns:
                    median = df[col].median()
                    iqr = df[col].quantile(0.75) - df[col].quantile(0.25)
                    if iqr != 0:
                        df_normalized[col] = (df[col] - median) / iqr
        
        return df_normalized
