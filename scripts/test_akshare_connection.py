#!/usr/bin/env python3
"""
测试 AKShare 数据获取连通性
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

print("="*70)
print("AKShare 数据源连通性测试")
print("="*70)

# 测试1: 导入 AKShare
print("\n1. 测试 AKShare 导入...")
try:
    import akshare as ak
    print("   [OK] AKShare 导入成功")
except Exception as e:
    print(f"   [ERROR] AKShare 导入失败: {e}")
    sys.exit(1)

# 测试2: 获取A股实时行情（简单接口）
print("\n2. 测试获取 A 股实时行情（spot）...")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"   [OK] 成功获取 {len(df)} 只股票实时行情")
    print(f"   前3只: {df['代码'].head(3).tolist()}")
except Exception as e:
    print(f"   [ERROR] 获取失败: {e}")

# 测试3: 获取单只股票历史数据
print("\n3. 测试获取单只股票历史数据...")
try:
    df = ak.stock_zh_a_hist(
        symbol="000001",
        period="daily",
        start_date="20250201",
        end_date="20250213",
        adjust="qfq"
    )
    if not df.empty:
        print(f"   [OK] 成功获取 000001 的历史数据，{len(df)} 条记录")
        print(f"   最新日期: {df['日期'].iloc[-1]}")
    else:
        print("   [WARN] 返回空数据")
except Exception as e:
    print(f"   [ERROR] 获取失败: {e}")

# 测试4: 获取沪深300成分股
print("\n4. 测试获取沪深300成分股...")
try:
    df = ak.index_stock_cons_weight_csindex(symbol="000300")
    print(f"   [OK] 成功获取沪深300成分股，{len(df)} 只")
except Exception as e:
    print(f"   [ERROR] 获取失败: {e}")

print("\n" + "="*70)
print("测试完成")
print("="*70)
