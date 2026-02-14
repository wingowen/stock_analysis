#!/usr/bin/env python3
"""
机器学习股票分析示例

演示如何使用 ML 模块进行股票分析
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ml.stock_analyzer import StockMLAnalyzer


def main():
    """主函数"""
    print("="*70)
    print("股票机器学习分析示例")
    print("="*70)
    
    # 初始化分析器
    analyzer = StockMLAnalyzer()
    
    # 获取数据摘要
    summary = analyzer.data_loader.get_data_summary()
    print(f"\n数据摘要:")
    print(f"  股票数量: {summary['stock_count']}")
    print(f"  记录总数: {summary['record_count']:,}")
    print(f"  日期范围: {summary['min_date']} 至 {summary['max_date']}")
    
    # 示例 1: 价格预测
    print("\n" + "="*70)
    print("示例 1: 股票价格预测")
    print("="*70)
    
    result = analyzer.price_prediction(
        stock_code='000001',  # 平安银行
        forecast_days=5,
        model_type='random_forest'
    )
    
    if 'error' not in result:
        print(f"\n预测结果:")
        print(f"  当前价格: {result['current_price']:.2f}")
        print(f"  预测收益率: {result['prediction']:.2%}")
        print(f"  预测价格: {result['predicted_price']:.2f}")
        print(f"  测试集R²: {result['test_metrics']['r2']:.4f}")
        print(f"\nTop 5 重要特征:")
        for i, row in enumerate(result['feature_importance'].items(), 1):
            if i <= 5:
                print(f"  {i}. {row[0]}: {row[1]:.4f}")
    else:
        print(f"错误: {result['error']}")
    
    # 示例 2: 涨跌方向分类
    print("\n" + "="*70)
    print("示例 2: 涨跌方向分类")
    print("="*70)
    
    result = analyzer.direction_classification(
        stock_code='000001',
        forecast_days=1,
        model_type='random_forest'
    )
    
    if 'error' not in result:
        print(f"\n分类结果:")
        print(f"  预测方向: {result['direction']}")
        print(f"  置信度: {result['confidence']:.2%}")
        print(f"  准确率: {result['accuracy']:.2%}")
        print(f"  F1分数: {result['f1_score']:.4f}")
    else:
        print(f"错误: {result['error']}")
    
    # 示例 3: 聚类分析
    print("\n" + "="*70)
    print("示例 3: 股票聚类分析")
    print("="*70)
    
    result = analyzer.cluster_analysis(
        n_clusters=5,
        sample_size=50
    )
    
    if 'error' not in result:
        print(f"\n聚类结果:")
        for cluster in result['clusters']:
            print(f"\n  聚类 {cluster['cluster_id']} ({cluster['stock_count']} 只股票):")
            print(f"    平均收益率: {cluster['avg_return']:.2%}")
            print(f"    平均波动率: {cluster['avg_volatility']:.2%}")
            print(f"    平均夏普比率: {cluster['avg_sharpe']:.4f}")
            print(f"    平均胜率: {cluster['avg_win_rate']:.2%}")
    else:
        print(f"错误: {result['error']}")
    
    # 示例 4: 相关性分析
    print("\n" + "="*70)
    print("示例 4: 股票相关性分析")
    print("="*70)
    
    corr_matrix = analyzer.correlation_analysis(
        stock_codes=['000001', '000002', '000063', '000100', '000333'],
        period=60
    )
    
    if not corr_matrix.empty:
        print("\n相关性矩阵:")
        print(corr_matrix.round(2))
        
        # 找出相关性最高的股票对
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                stock1 = corr_matrix.columns[i]
                stock2 = corr_matrix.columns[j]
                corr = corr_matrix.iloc[i, j]
                corr_pairs.append((stock1, stock2, corr))
        
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        print("\n相关性最高的股票对:")
        for stock1, stock2, corr in corr_pairs[:3]:
            print(f"  {stock1} - {stock2}: {corr:.4f}")
    
    print("\n" + "="*70)
    print("分析完成!")
    print("="*70)
    
    # 关闭连接
    analyzer.data_loader.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
