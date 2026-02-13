#!/usr/bin/env python3
"""
沪深300数据获取脚本

功能：
1. 获取沪深300成分股列表
2. 获取这些股票近一年的历史数据
3. 保存到 SQLite 数据库（默认）
4. 可选导出 CSV 文件
5. 支持代理池和防爬机制

用法：
    python fetch_hs300_data.py                    # 获取近一年数据，保存到 SQLite
    python fetch_hs300_data.py --csv              # 同时导出 CSV 文件
    python fetch_hs300_data.py --proxy            # 启用代理池
    python fetch_hs300_data.py --start 20230101   # 指定开始日期
    python fetch_hs300_data.py --limit 10         # 只获取前10只股票（测试用）
    
参数：
    --start: 开始日期 (默认: 一年前)
    --end: 结束日期 (默认: 今天)
    --limit: 限制获取的股票数量 (用于测试)
    --csv: 同时导出 CSV 文件
    --index: 指数代码 (默认: 000300)
    --proxy: 启用代理池
    --min-delay: 最小请求延迟 (默认: 1.0秒)
    --max-delay: 最大请求延迟 (默认: 3.0秒)
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.stock_manager import StockManager


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='获取沪深300股票历史数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fetch_hs300_data.py                    # 获取近一年数据，保存到 SQLite
  python fetch_hs300_data.py --csv              # 同时导出 CSV 文件
  python fetch_hs300_data.py --proxy            # 启用代理池（更稳定）
  python fetch_hs300_data.py --limit 10         # 只获取前10只股票（测试用）
  python fetch_hs300_data.py --start 20230101 --min-delay 2.0  # 指定日期和延迟
        """
    )
    
    parser.add_argument(
        '--start',
        type=str,
        help='开始日期 (格式: YYYYMMDD)'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        help='结束日期 (格式: YYYYMMDD)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='限制获取的股票数量（用于测试）'
    )
    
    parser.add_argument(
        '--index',
        type=str,
        default='000300',
        help='指数代码 (默认: 000300 沪深300, 可选: 000016 上证50, 000905 中证500)'
    )
    
    parser.add_argument(
        '--csv',
        action='store_true',
        help='同时导出 CSV 文件'
    )

    parser.add_argument(
        '--proxy',
        action='store_true',
        help='启用代理池（从免费代理源获取代理）'
    )

    parser.add_argument(
        '--min-delay',
        type=float,
        default=1.0,
        help='最小请求延迟（秒），默认: 1.0'
    )

    parser.add_argument(
        '--max-delay',
        type=float,
        default=3.0,
        help='最大请求延迟（秒），默认: 3.0'
    )

    args = parser.parse_args()
    
    # 设置默认日期
    if args.end is None:
        end_date = datetime.now().strftime('%Y%m%d')
    else:
        end_date = args.end
    
    if args.start is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    else:
        start_date = args.start
    
    # 显示配置
    print("="*70)
    print("沪深300历史数据获取工具")
    print("="*70)
    print(f"指数代码: {args.index}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"存储方式: SQLite 数据库")
    print(f"防爬机制: 延迟 {args.min_delay}-{args.max_delay}秒")
    if args.proxy:
        print(f"代理池: 启用")
    if args.csv:
        print(f"额外导出: CSV 文件")
    if args.limit:
        print(f"数量限制: 前 {args.limit} 只股票")
    print("="*70)
    print()
    
    try:
        # 创建股票管理器（传入代理配置）
        print("【步骤1】初始化管理器...")
        manager = StockManager(
            enable_proxy=args.proxy,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )

        # 初始化数据库
        manager.init_sqlite_tables()
        print()
        
        # 2. 获取指数成分股
        print("【步骤2】获取指数成分股列表...")
        constituents = manager.get_index_constituents(args.index)
        
        if constituents.empty:
            print("[ERROR] 获取成分股列表失败，程序退出")
            return 1
        
        print(f"\n成分股列表预览:")
        print(constituents.head(10))
        print(f"\n共 {len(constituents)} 只成分股\n")
        
        # 获取股票代码列表
        stock_codes = constituents['成分券代码'].tolist()
        
        # 限制数量（用于测试）
        if args.limit:
            stock_codes = stock_codes[:args.limit]
            print(f"[WARN] 已限制为前 {args.limit} 只股票\n")
        
        # 3. 批量获取历史数据
        print("【步骤3】获取历史行情数据...")
        print("这可能需要几分钟时间，请耐心等待...\n")
        
        history_data = manager.get_stocks_history(
            stock_codes=stock_codes,
            start_date=start_date,
            end_date=end_date,
            show_progress=True
        )
        
        if history_data.empty:
            print("[ERROR] 未获取到任何历史数据")
            return 1
        
        # 显示数据预览
        print("\n【数据预览】")
        print(history_data.head(20))
        print(f"\n数据维度: {history_data.shape}")
        
        # 统计信息
        unique_stocks = history_data['股票代码'].nunique()
        total_records = len(history_data)
        date_range = f"{history_data['日期'].min()} 至 {history_data['日期'].max()}"
        
        print(f"\n【数据统计】")
        print(f"股票数量: {unique_stocks}")
        print(f"总记录数: {total_records}")
        print(f"日期范围: {date_range}")
        
        # 4. 保存数据到 SQLite
        print("\n【步骤4】保存数据到 SQLite...")
        
        # 保存历史数据
        manager.save_to_sqlite(history_data, table_name="stock_history", if_exists="append")
        
        # 保存成分股列表
        constituents['日期'] = datetime.now().strftime('%Y-%m-%d')
        manager.save_to_sqlite(constituents, table_name="index_constituents", if_exists="append")
        
        # 5. 可选：导出 CSV
        if args.csv:
            print("\n【步骤5】导出 CSV 文件...")
            output_file = f"hs300_history_{start_date}_{end_date}.csv"
            manager.save_to_csv(history_data, output_file)
            
            constituents_file = f"hs300_constituents_{end_date}.csv"
            manager.save_to_csv(constituents, constituents_file)
        
        # 最终统计
        print("\n" + "="*70)
        print("[OK] 数据获取完成!")
        print("="*70)
        print(f"\n数据库文件: {manager.db_path}")
        print(f"  - 股票数量: {manager.get_stock_count()}")
        print(f"  - 总记录数: {manager.get_record_count()}")
        
        if args.csv:
            print(f"\nCSV 文件已导出到: {manager.data_dir}")
        
        print("\n使用示例:")
        print(f"  查询单只股票: manager.query_stock_history('000001')")
        print(f"  查询所有股票: manager.query_all_stocks()")
        print("="*70)
        
        return 0
        
    except ImportError as e:
        print(f"\n[ERROR] 缺少依赖: {e}")
        print("\n请安装依赖:")
        print("  pip install akshare pandas")
        return 1
        
    except Exception as e:
        print(f"\n[ERROR] 程序出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
