"""
Stock ML Analyzer - Main Class

股票机器学习分析器主类
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .data_loader import StockDataLoader
from .feature_engineering import FeatureEngineer
from .models import StockPricePredictor, StockDirectionClassifier, StockClustering, DimensionalityReducer


class StockMLAnalyzer:
    """
    股票机器学习分析器
    
    集成数据加载、特征工程、模型训练和预测的一体化分析工具
    
    Example:
        analyzer = StockMLAnalyzer()
        
        # 价格预测
        result = analyzer.price_prediction('000001', forecast_days=5)
        print(f"Predicted return: {result['prediction']:.2%}")
        
        # 涨跌分类
        result = analyzer.direction_classification('000001')
        print(f"Direction: {result['direction']}")
        
        # 聚类分析
        clusters = analyzer.cluster_analysis(n_clusters=5)
        print(clusters['cluster_summary'])
    """
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        初始化分析器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.data_loader = StockDataLoader(db_path)
        self.results_cache = {}
        
    def price_prediction(
        self,
        stock_code: str,
        forecast_days: int = 1,
        model_type: str = 'random_forest',
        test_size: float = 0.2
    ) -> Dict:
        """
        股票价格预测
        
        Args:
            stock_code: 股票代码
            forecast_days: 预测天数
            model_type: 模型类型
            test_size: 测试集比例
            
        Returns:
            预测结果字典
        """
        print(f"\n{'='*60}")
        print(f"Stock Price Prediction: {stock_code}")
        print(f"{'='*60}")
        
        # 加载数据
        df = self.data_loader.load_stock_data(stock_code)
        if df.empty:
            return {'error': f'No data found for {stock_code}'}
        
        print(f"Loaded {len(df)} records")
        
        # 特征工程
        fe = FeatureEngineer(df)
        fe.add_technical_indicators()\
          .add_statistical_features()\
          .add_volume_features()\
          .add_time_features()\
          .add_lag_features([1, 2, 3, 5])\
          .add_target_variable(forecast_horizon=forecast_days, target_type='return')
        
        df_features = fe.get_features_df(drop_na=True)
        
        if len(df_features) < 100:
            return {'error': 'Insufficient data for training'}
        
        # 准备特征和目标
        feature_cols = fe.get_feature_names()
        X = df_features[feature_cols]
        y = df_features['Target_Return']
        
        # 划分训练测试集
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 训练模型
        model = StockPricePredictor(model_type=model_type)
        model.train(X_train, y_train, feature_cols)
        
        # 评估
        train_metrics = model.evaluate(X_train, y_train)
        test_metrics = model.evaluate(X_test, y_test)
        
        # 预测未来
        latest_data = X.iloc[-1:].values
        prediction = model.predict(latest_data)[0]
        
        # 特征重要性
        importance = model.get_feature_importance().head(10)
        
        result = {
            'stock_code': stock_code,
            'forecast_days': forecast_days,
            'model_type': model_type,
            'prediction': prediction,
            'predicted_price': df['close'].iloc[-1] * (1 + prediction),
            'current_price': df['close'].iloc[-1],
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'feature_importance': importance.to_dict(),
            'data_points': len(df_features)
        }
        
        print(f"\nPrediction Results:")
        print(f"  Current Price: {result['current_price']:.2f}")
        print(f"  Predicted Return ({forecast_days}d): {prediction:.2%}")
        print(f"  Predicted Price: {result['predicted_price']:.2f}")
        print(f"  Test R²: {test_metrics['r2']:.4f}")
        print(f"  Test RMSE: {test_metrics['rmse']:.4f}")
        
        return result
    
    def direction_classification(
        self,
        stock_code: str,
        forecast_days: int = 1,
        model_type: str = 'random_forest',
        test_size: float = 0.2
    ) -> Dict:
        """
        股票涨跌方向分类
        
        Args:
            stock_code: 股票代码
            forecast_days: 预测天数
            model_type: 模型类型
            test_size: 测试集比例
            
        Returns:
            分类结果字典
        """
        print(f"\n{'='*60}")
        print(f"Direction Classification: {stock_code}")
        print(f"{'='*60}")
        
        # 加载数据
        df = self.data_loader.load_stock_data(stock_code)
        if df.empty:
            return {'error': f'No data found for {stock_code}'}
        
        # 特征工程
        fe = FeatureEngineer(df)
        fe.add_technical_indicators()\
          .add_statistical_features()\
          .add_volume_features()\
          .add_lag_features([1, 2, 3, 5])\
          .add_target_variable(forecast_horizon=forecast_days, target_type='direction')
        
        df_features = fe.get_features_df(drop_na=True)
        
        if len(df_features) < 100:
            return {'error': 'Insufficient data for training'}
        
        # 准备数据
        feature_cols = fe.get_feature_names()
        X = df_features[feature_cols]
        y = df_features['Target_Direction']
        
        # 过滤掉"平"的情况，只保留涨跌
        mask = y != 0
        X = X[mask]
        y = y[mask]
        
        if len(X) < 50:
            return {'error': 'Insufficient data after filtering'}
        
        # 划分数据集
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 训练分类器
        clf = StockDirectionClassifier(model_type=model_type)
        clf.train(X_train, y_train, feature_cols)
        
        # 评估
        metrics = clf.evaluate(X_test, y_test)
        
        # 预测
        latest_data = X.iloc[-1:].values
        direction = clf.predict(latest_data)[0]
        proba = clf.predict_proba(latest_data)[0]
        
        # 特征重要性
        importance = clf.get_feature_importance().head(10)
        
        direction_map = {-1: 'Down', 1: 'Up'}
        
        result = {
            'stock_code': stock_code,
            'forecast_days': forecast_days,
            'model_type': model_type,
            'direction': direction_map.get(direction, 'Unknown'),
            'direction_code': direction,
            'confidence': max(proba),
            'accuracy': metrics['accuracy'],
            'f1_score': metrics['f1'],
            'feature_importance': importance.to_dict()
        }
        
        print(f"\nClassification Results:")
        print(f"  Direction: {result['direction']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Accuracy: {metrics['accuracy']:.2%}")
        print(f"  F1 Score: {metrics['f1']:.4f}")
        
        return result
    
    def cluster_analysis(
        self,
        n_clusters: int = 5,
        sample_size: int = 50,
        feature_days: int = 20
    ) -> Dict:
        """
        股票聚类分析
        
        Args:
            n_clusters: 聚类数量
            sample_size: 分析的股票数量
            feature_days: 特征计算天数
            
        Returns:
            聚类结果字典
        """
        print(f"\n{'='*60}")
        print(f"Stock Clustering Analysis")
        print(f"{'='*60}")
        
        # 获取股票列表
        all_stocks = self.data_loader.get_stock_list()
        stocks = all_stocks[:min(sample_size, len(all_stocks))]
        
        print(f"Analyzing {len(stocks)} stocks...")
        
        # 为每只股票计算特征
        stock_features = []
        stock_codes = []
        
        for code in stocks:
            df = self.data_loader.load_stock_data(code)
            if len(df) < feature_days:
                continue
            
            # 计算统计特征
            recent_df = df.tail(feature_days)
            
            features = {
                'stock_code': code,
                'avg_return': recent_df['pct_change'].mean(),
                'volatility': recent_df['pct_change'].std(),
                'sharpe_ratio': recent_df['pct_change'].mean() / (recent_df['pct_change'].std() + 1e-10),
                'max_return': recent_df['pct_change'].max(),
                'min_return': recent_df['pct_change'].min(),
                'win_rate': (recent_df['pct_change'] > 0).mean(),
                'avg_volume': recent_df['volume'].mean(),
                'volume_trend': recent_df['volume'].iloc[-5:].mean() / recent_df['volume'].iloc[:5].mean() - 1,
                'price_trend': recent_df['close'].iloc[-1] / recent_df['close'].iloc[0] - 1,
                'volatility_of_volatility': recent_df['pct_change'].rolling(5).std().std()
            }
            
            stock_features.append(features)
            stock_codes.append(code)
        
        if len(stock_features) < n_clusters:
            return {'error': 'Insufficient stocks for clustering'}
        
        # 创建特征DataFrame
        df_features = pd.DataFrame(stock_features)
        X = df_features.drop('stock_code', axis=1)
        
        # 聚类
        clustering = StockClustering(method='kmeans', n_clusters=n_clusters)
        clustering.fit(X)
        labels = clustering.get_clusters()
        
        df_features['cluster'] = labels
        
        # 分析每个聚类
        cluster_summary = []
        for cluster_id in range(n_clusters):
            cluster_stocks = df_features[df_features['cluster'] == cluster_id]
            
            summary = {
                'cluster_id': cluster_id,
                'stock_count': len(cluster_stocks),
                'stocks': cluster_stocks['stock_code'].tolist(),
                'avg_return': cluster_stocks['avg_return'].mean(),
                'avg_volatility': cluster_stocks['volatility'].mean(),
                'avg_sharpe': cluster_stocks['sharpe_ratio'].mean(),
                'avg_win_rate': cluster_stocks['win_rate'].mean(),
                'avg_price_trend': cluster_stocks['price_trend'].mean()
            }
            cluster_summary.append(summary)
        
        result = {
            'n_clusters': n_clusters,
            'n_stocks': len(stock_features),
            'clusters': cluster_summary,
            'cluster_data': df_features.to_dict()
        }
        
        print(f"\nCluster Summary:")
        for summary in cluster_summary:
            print(f"\n  Cluster {summary['cluster_id']} ({summary['stock_count']} stocks):")
            print(f"    Avg Return: {summary['avg_return']:.2%}")
            print(f"    Avg Volatility: {summary['avg_volatility']:.2%}")
            print(f"    Avg Sharpe: {summary['avg_sharpe']:.4f}")
            print(f"    Stocks: {', '.join(summary['stocks'][:5])}{'...' if len(summary['stocks']) > 5 else ''}")
        
        return result
    
    def correlation_analysis(
        self,
        stock_codes: Optional[List[str]] = None,
        period: int = 60
    ) -> pd.DataFrame:
        """
        股票相关性分析
        
        Args:
            stock_codes: 股票代码列表
            period: 分析周期
            
        Returns:
            相关性矩阵
        """
        if stock_codes is None:
            stock_codes = self.data_loader.get_stock_list()[:20]
        
        print(f"\nAnalyzing correlation for {len(stock_codes)} stocks...")
        
        # 加载收益率数据
        returns_data = {}
        
        for code in stock_codes:
            df = self.data_loader.load_stock_data(code)
            if len(df) >= period:
                returns_data[code] = df['pct_change'].tail(period)
        
        if len(returns_data) < 2:
            return pd.DataFrame()
        
        # 创建收益率DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # 计算相关性
        corr_matrix = returns_df.corr()
        
        return corr_matrix
    
    def visualize_results(self, result: Dict, save_path: Optional[str] = None):
        """
        可视化分析结果
        
        Args:
            result: 分析结果字典
            save_path: 保存路径
        """
        # 根据结果类型创建不同的可视化
        if 'prediction' in result:
            # 价格预测结果可视化
            fig, axes = plt.subplots(2, 1, figsize=(12, 8))
            
            # 特征重要性
            if 'feature_importance' in result:
                importance = pd.DataFrame(result['feature_importance'])
                importance.plot(x='feature', y='importance', kind='barh', ax=axes[0])
                axes[0].set_title('Feature Importance')
            
            # 预测信息
            axes[1].text(0.1, 0.7, f"Prediction: {result['prediction']:.2%}", fontsize=14)
            axes[1].text(0.1, 0.5, f"R² Score: {result['test_metrics']['r2']:.4f}", fontsize=12)
            axes[1].axis('off')
            
            plt.tight_layout()
            
        elif 'direction' in result:
            # 分类结果可视化
            fig, ax = plt.subplots(figsize=(8, 6))
            direction = result['direction']
            confidence = result['confidence']
            
            colors = {'Up': 'green', 'Down': 'red'}
            ax.barh([0], [confidence], color=colors.get(direction, 'gray'))
            ax.set_yticks([0])
            ax.set_yticklabels([direction])
            ax.set_xlabel('Confidence')
            ax.set_title(f"Direction Prediction: {result['stock_code']}")
            
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Visualization saved to {save_path}")
        else:
            plt.show()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.data_loader.close()
