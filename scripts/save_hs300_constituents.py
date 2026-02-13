#!/usr/bin/env python3
"""
保存沪深300成分股列表到数据库
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.stock_manager import StockManager

print("="*70)
print("保存沪深300成分股列表")
print("="*70)

# 创建管理器
manager = StockManager(enable_proxy=False)

# 初始化数据库
print("\n1. 初始化数据库...")
manager.init_sqlite_tables()

# 获取沪深300成分股
print("\n2. 获取沪深300成分股列表...")
constituents = manager.get_index_constituents("000300")

if constituents.empty:
    print("[ERROR] 获取成分股列表失败")
    sys.exit(1)

print(f"\n[OK] 成功获取 {len(constituents)} 只成分股")
print("\n成分股列表预览:")
print(constituents.head(10))

# 添加更新日期
constituents['日期'] = datetime.now().strftime('%Y-%m-%d')

# 保存到数据库
print("\n3. 保存到 SQLite...")
manager.save_to_sqlite(constituents, table_name="index_constituents", if_exists="replace")

# 同时保存CSV备份
print("\n4. 保存CSV备份...")
manager.save_to_csv(constituents, "hs300_constituents_backup.csv")

print("\n" + "="*70)
print("[OK] 成分股列表保存完成!")
print("="*70)
print(f"\n数据库文件: {manager.db_path}")
print(f"成分股数量: {len(constituents)}")
print("\n股票代码列表（前20只）:")
stock_codes = constituents['成分券代码'].tolist()
for i, code in enumerate(stock_codes[:20], 1):
    name = constituents[constituents['成分券代码'] == code]['成分券名称'].iloc[0]
    print(f"  {i:2d}. {code} - {name}")
print(f"  ... 共 {len(stock_codes)} 只")
