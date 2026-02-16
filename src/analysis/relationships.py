"""
股票关系分析模块

提供股票间的相关性分析、聚类分析和网络分析功能。

功能：
- 计算股票间价格涨跌幅的相关性
- K-means 聚类分析
- 构建股票关系网络
- 分析股票与概念版块的关系
"""

import sqlite3
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

# Optional imports
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ImportError:
    KMeans = None
    StandardScaler = None


class StockRelationshipAnalyzer:
    """
    股票关系分析器。
    
    用于分析多只股票之间的关系，包括相关性、聚类和网络分析。
    
    Attributes:
        db_path: SQLite 数据库路径
        conn: 数据库连接
        cursor: 数据库游标
    """
    
    def __init__(self, db_path: str = 'stock_history.db'):
        """
        初始化分析器。
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def get_stock_list(self):
        """获取所有股票代码"""
        self.cursor.execute("SELECT DISTINCT stock_code FROM stock_history")
        result = self.cursor.fetchall()
        return [item[0] for item in result]
    
    def get_stock_data(self, stock_code, start_date=None, end_date=None):
        """获取单个股票的历史数据"""
        query = "SELECT * FROM stock_history WHERE stock_code = ?"
        params = [stock_code]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        return pd.read_sql_query(query, self.conn, params=params)
    
    def get_all_stocks_data(self, start_date=None, end_date=None):
        """获取所有股票的历史数据"""
        query = "SELECT * FROM stock_history"
        params = []
        
        if start_date:
            query += " WHERE date >= ?"
            params.append(start_date)
        if end_date:
            if start_date:
                query += " AND date <= ?"
            else:
                query += " WHERE date <= ?"
            params.append(end_date)
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def calculate_correlation(self, start_date=None, end_date=None):
        """计算股票之间的相关性"""
        # 获取所有股票数据
        df = self.get_all_stocks_data(start_date, end_date)
        
        if df.empty:
            print("没有找到数据")
            return None
        
        # 重塑数据为透视表
        pivot_df = df.pivot(index='date', columns='stock_code', values='pct_change')
        
        # 计算相关性矩阵
        correlation_matrix = pivot_df.corr()
        
        return correlation_matrix
    
    def cluster_stocks(self, n_clusters: int = 5, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        使用 K-means 对股票进行聚类。
        
        Args:
            n_clusters: 聚类数量
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            
        Returns:
            包含聚类结果的 DataFrame，失败返回 None
        """
        if KMeans is None or StandardScaler is None:
            print("scikit-learn not installed. Please install: pip install scikit-learn")
            return None
        
        df = self.get_all_stocks_data(start_date, end_date)
        
        if df.empty:
            print("没有找到数据")
            return None
        
        pivot_df = df.pivot(index='date', columns='stock_code', values='pct_change')
        
        # 计算股票的统计特征
        stock_features = pd.DataFrame({
            'mean_return': pivot_df.mean(),
            'std_return': pivot_df.std(),
            'max_return': pivot_df.max(),
            'min_return': pivot_df.min(),
            'skewness': pivot_df.skew(),
            'kurtosis': pivot_df.kurtosis()
        })
        
        # 标准化特征
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(stock_features)
        
        # 聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_features)
        
        stock_features['cluster'] = clusters
        
        return stock_features
    
    def build_relationship_network(self, threshold=0.7, start_date=None, end_date=None):
        """构建股票关系网络"""
        # 计算相关性矩阵
        correlation_matrix = self.calculate_correlation(start_date, end_date)
        
        if correlation_matrix is None:
            return None
        
        # 创建图
        G = nx.Graph()
        
        # 添加节点
        for stock in correlation_matrix.columns:
            G.add_node(stock)
        
        # 添加边（相关性超过阈值）
        for i, stock1 in enumerate(correlation_matrix.columns):
            for j, stock2 in enumerate(correlation_matrix.columns):
                if i < j:
                    correlation = correlation_matrix.iloc[i, j]
                    if abs(correlation) > threshold:
                        G.add_edge(stock1, stock2, weight=abs(correlation))
        
        return G
    
    def analyze_industry_relationship(self, industry_stocks=None, start_date=None, end_date=None):
        """分析行业内股票的关系"""
        if industry_stocks is None:
            industry_stocks = self.get_stock_list()
        
        # 获取行业股票数据
        query = "SELECT * FROM stock_history WHERE stock_code IN ({})"
        placeholders = ','.join(['?'] * len(industry_stocks))
        query = query.format(placeholders)
        
        params = industry_stocks.copy()
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        df = pd.read_sql_query(query, self.conn, params=params)
        
        if df.empty:
            print("没有找到数据")
            return None
        
        # 计算行业平均涨跌幅
        industry_avg = df.groupby('date')['pct_change'].mean().reset_index()
        industry_avg.columns = ['date', 'industry_avg_return']
        
        # 计算每个股票与行业平均的相关性
        pivot_df = df.pivot(index='date', columns='stock_code', values='pct_change')
        merged_df = pivot_df.merge(industry_avg, on='date', how='left')
        
        correlations = {}
        for stock in pivot_df.columns:
            correlation = merged_df[stock].corr(merged_df['industry_avg_return'])
            correlations[stock] = correlation
        
        return correlations
    
    def get_concept_data(self, concept_name="商业航天", start_date=None, end_date=None):
        """获取概念版块数据"""
        query = "SELECT * FROM concept_index_history WHERE concept_name = ?"
        params = [concept_name]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        return pd.read_sql_query(query, self.conn, params=params)
    
    def analyze_stock_concept_relationship(self, stock_list, concept_name="商业航天", start_date=None, end_date=None):
        """分析个股与概念版块的关系"""
        # 获取概念版块数据
        concept_df = self.get_concept_data(concept_name, start_date, end_date)
        
        if concept_df.empty:
            print(f"没有找到 {concept_name} 概念版块的数据")
            return None
        
        # 计算概念版块涨跌幅
        concept_df['pct_change'] = ((concept_df['close'] - concept_df['open']) / concept_df['open'] * 100).round(2)
        concept_df = concept_df[['date', 'pct_change']]
        concept_df.columns = ['date', 'concept_pct_change']
        
        # 获取个股数据
        query = "SELECT * FROM stock_history WHERE stock_code IN ({})"
        placeholders = ','.join(['?'] * len(stock_list))
        query = query.format(placeholders)
        
        params = stock_list.copy()
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        stock_df = pd.read_sql_query(query, self.conn, params=params)
        
        if stock_df.empty:
            print("没有找到个股数据")
            return None
        
        # 计算个股与概念版块的相关性
        correlations = {}
        for stock in stock_list:
            # 获取单个股票数据
            single_stock_df = stock_df[stock_df['stock_code'] == stock][['date', 'pct_change']]
            
            if single_stock_df.empty:
                correlations[stock] = 0.0
                continue
            
            # 合并数据
            merged_df = pd.merge(single_stock_df, concept_df, on='date', how='inner')
            
            if merged_df.empty:
                correlations[stock] = 0.0
                continue
            
            # 计算相关性
            correlation = merged_df['pct_change'].corr(merged_df['concept_pct_change'])
            correlations[stock] = correlation
        
        return correlations
    
    def visualize_correlation(self, start_date=None, end_date=None):
        """可视化股票相关性"""
        correlation_matrix = self.calculate_correlation(start_date, end_date)
        
        if correlation_matrix is None:
            return
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(correlation_matrix, annot=False, cmap='coolwarm', center=0)
        plt.title('股票涨跌幅相关性矩阵')
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png')
        plt.show()
    
    def visualize_network(self, threshold=0.7, start_date=None, end_date=None):
        """可视化股票关系网络"""
        G = self.build_relationship_network(threshold, start_date, end_date)
        
        if G is None:
            return
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        
        plt.figure(figsize=(15, 12))
        pos = nx.spring_layout(G, k=0.15, iterations=20)
        
        # 绘制节点
        nx.draw_networkx_nodes(G, pos, node_size=300, node_color='lightblue')
        
        # 绘制边
        edges = G.edges(data=True)
        weights = [d['weight'] * 3 for (u, v, d) in edges]
        nx.draw_networkx_edges(G, pos, width=weights, alpha=0.6)
        
        # 绘制标签
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        plt.title(f'股票关系网络 (相关性阈值: {threshold})')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('stock_relationship_network.png')
        plt.show()
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

def main():
    """主函数"""
    analyzer = StockRelationshipAnalyzer('data/stock_data.db')
    
    try:
        # 获取股票列表
        stock_list = analyzer.get_stock_list()
        print(f"数据库中有 {len(stock_list)} 只股票")
        
        # 计算相关性
        print("\n计算股票相关性...")
        correlation_matrix = analyzer.calculate_correlation()
        if correlation_matrix is not None:
            print(f"相关性矩阵形状: {correlation_matrix.shape}")
            
        # 聚类分析
        print("\n进行股票聚类...")
        clusters = analyzer.cluster_stocks()
        if clusters is not None:
            print("聚类结果:")
            print(clusters['cluster'].value_counts())
        
        # 构建关系网络
        print("\n构建股票关系网络...")
        network = analyzer.build_relationship_network()
        if network is not None:
            print(f"网络节点数: {network.number_of_nodes()}")
            print(f"网络边数: {network.number_of_edges()}")
        
        # 分析行业关系
        print("\n分析行业关系...")
        industry_relations = analyzer.analyze_industry_relationship()
        if industry_relations is not None:
            print("股票与行业平均相关性前10:")
            sorted_relations = sorted(industry_relations.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            for stock, corr in sorted_relations:
                print(f"{stock}: {corr:.4f}")
        
        # 分析全部个股与商业航天概念版块的关系
        print("\n分析个股与商业航天概念版块的关系...")
        concept_relations = analyzer.analyze_stock_concept_relationship(stock_list, "商业航天")
        if concept_relations is not None:
            print("个股与商业航天概念版块相关性前10:")
            sorted_concept_relations = sorted(concept_relations.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            for stock, corr in sorted_concept_relations:
                print(f"{stock}: {corr:.4f}")
        
        # 可视化
        print("\n生成可视化图表...")
        analyzer.visualize_correlation()
        analyzer.visualize_network()
        
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
