#!/usr/bin/env python3
"""
测试 SQLite 数据查询功能
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.stock_manager import StockManager

# 创建管理器
manager = StockManager()

print("="*70)
print("SQLite 数据查询测试")
print("="*70)

# 1. 查询数据库中的股票数量
print("\n1. 数据库统计信息:")
print(f"   股票数量: {manager.get_stock_count()}")
print(f"   总记录数: {manager.get_record_count()}")

# 2. 查询所有股票代码
print("\n2. 查询所有股票代码:")
stocks = manager.query_all_stocks()
if not stocks.empty:
    print(f"   共有 {len(stocks)} 只股票:")
    print(stocks.head(10))
else:
    print("   数据库中暂无股票数据")

# 3. 查询单只股票历史数据（如果有的话）
print("\n3. 查询示例（平安银行 000001）:")
history = manager.query_stock_history('000001', start_date='2025-02-01')
if not history.empty:
    print(f"   查询到 {len(history)} 条记录")
    print(history.head())
else:
    print("   该股票暂无数据")

print("\n" + "="*70)
print("测试完成!")
print("="*70)
