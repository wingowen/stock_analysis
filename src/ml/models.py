"""
Machine Learning Models for Stock Analysis

股票分析机器学习模型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVR, SVC
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')


class StockPricePredictor:
    """
    股票价格预测器
    
    使用多种机器学习模型预测股票价格或收益率
    
    支持的模型:
    - Random Forest
    - Gradient Boosting
    - Linear Regression
    - Support Vector Machine
    - Neural Network (MLP)
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        初始化预测器
        
        Args:
            model_type: 模型类型 ('random_forest', 'gradient_boosting', 
                       'linear', 'svm', 'neural_network')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
    def _create_model(self):
        """创建模型实例"""
        if self.model_type == 'random_forest':
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'linear':
            return LinearRegression()
        elif self.model_type == 'svm':
            return SVR(kernel='rbf', C=1.0, gamma='scale')
        elif self.model_type == 'neural_network':
            return MLPRegressor(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=42,
                early_stopping=True
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, 
              feature_names: Optional[List[str]] = None):
        """
        训练模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标
            feature_names: 特征名称列表
        """
        self.feature_names = feature_names or X_train.columns.tolist()
        
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X_train)
        
        # 创建并训练模型
        self.model = self._create_model()
        self.model.fit(X_scaled, y_train)
        self.is_trained = True
        
        print(f"Model trained: {self.model_type}")
        print(f"Features: {len(self.feature_names)}")
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测
        
        Args:
            X: 特征数据
            
        Returns:
            预测结果
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        评估模型
        
        Args:
            X_test: 测试特征
            y_test: 测试目标
            
        Returns:
            评估指标字典
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        y_pred = self.predict(X_test)
        
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred),
            'mape': np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        }
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性
        
        Returns:
            特征重要性DataFrame
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importance = np.abs(self.model.coef_)
        else:
            return pd.DataFrame()
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)


class StockDirectionClassifier:
    """
    股票涨跌方向分类器
    
    预测股票未来涨跌方向（涨/跌/平）
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        初始化分类器
        
        Args:
            model_type: 模型类型
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
    def _create_model(self):
        """创建模型实例"""
        if self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'logistic':
            return LogisticRegression(random_state=42, max_iter=1000)
        elif self.model_type == 'svm':
            return SVC(kernel='rbf', C=1.0, gamma='scale', probability=True)
        elif self.model_type == 'neural_network':
            return MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=42,
                early_stopping=True
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              feature_names: Optional[List[str]] = None):
        """
        训练模型
        
        Args:
            X_train: 训练特征
            y_train: 训练目标 (分类标签)
            feature_names: 特征名称
        """
        self.feature_names = feature_names or X_train.columns.tolist()
        
        X_scaled = self.scaler.fit_transform(X_train)
        
        self.model = self._create_model()
        self.model.fit(X_scaled, y_train)
        self.is_trained = True
        
        print(f"Classifier trained: {self.model_type}")
        print(f"Classes: {self.model.classes_}")
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测类别"""
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """
        评估模型
        
        Args:
            X_test: 测试特征
            y_test: 测试目标
            
        Returns:
            评估指标
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        y_pred = self.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
        
        return metrics


class StockClustering:
    """
    股票聚类分析
    
    使用无监督学习对股票进行聚类，发现相似股票群体
    """
    
    def __init__(self, method: str = 'kmeans', n_clusters: int = 5):
        """
        初始化聚类器
        
        Args:
            method: 聚类方法 ('kmeans', 'dbscan')
            n_clusters: 聚类数量（KMeans）
        """
        self.method = method
        self.n_clusters = n_clusters
        self.model = None
        self.scaler = StandardScaler()
        self.labels = None
        self.is_fitted = False
        
    def _create_model(self):
        """创建聚类模型"""
        if self.method == 'kmeans':
            return KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        elif self.method == 'dbscan':
            return DBSCAN(eps=0.5, min_samples=5)
        else:
            raise ValueError(f"Unknown clustering method: {self.method}")
    
    def fit(self, X: pd.DataFrame):
        """
        训练聚类模型
        
        Args:
            X: 特征数据
        """
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = self._create_model()
        self.labels = self.model.fit_predict(X_scaled)
        self.is_fitted = True
        
        unique_labels = np.unique(self.labels)
        print(f"Clustering completed: {len(unique_labels)} clusters found")
        
    def get_clusters(self) -> np.ndarray:
        """获取聚类标签"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet!")
        return self.labels
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测新数据的聚类"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet!")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)


class DimensionalityReducer:
    """
    降维分析
    
    使用 PCA 等降维技术可视化股票数据
    """
    
    def __init__(self, method: str = 'pca', n_components: int = 2):
        """
        初始化降维器
        
        Args:
            method: 降维方法
            n_components: 降维后的维度
        """
        self.method = method
        self.n_components = n_components
        self.model = None
        self.scaler = StandardScaler()
        
    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        拟合并转换数据
        
        Args:
            X: 原始特征
            
        Returns:
            降维后的数据
        """
        X_scaled = self.scaler.fit_transform(X)
        
        if self.method == 'pca':
            self.model = PCA(n_components=self.n_components)
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        return self.model.fit_transform(X_scaled)
    
    def get_explained_variance_ratio(self) -> np.ndarray:
        """获取解释方差比例"""
        if self.model is None:
            raise ValueError("Model not fitted yet!")
        return self.model.explained_variance_ratio_
