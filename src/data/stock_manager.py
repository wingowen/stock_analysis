"""
A-Share Stock Data Manager Module

大A股票数据管理模块

提供功能：
- 获取指数成分股列表（沪深300、上证50、中证500等）
- 批量获取股票历史数据
- 数据导出到 CSV/SQLite
- 股票基本信息查询
- 代理支持和防爬机制

依赖:
    akshare: 用于获取A股数据
"""

import os
import sqlite3
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

import pandas as pd

# 导入代理管理器
try:
    from .proxy_manager import ProxyManager, with_retry
except ImportError:
    from proxy_manager import ProxyManager, with_retry

# Optional imports
try:
    import akshare as ak
except ImportError:
    ak = None

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StockManager:
    """
    A股股票数据管理器。
    
    用于管理A股股票数据，包括：
    - 获取指数成分股
    - 获取个股历史数据
    - 批量导出数据
    
    Attributes:
        data_dir: 数据保存目录
        db_path: SQLite 数据库路径（可选）
    """
    
    def __init__(
        self,
        data_dir: str = "data",
        db_path: Optional[str] = None,
        enable_proxy: bool = False,
        min_delay: float = 1.0,
        max_delay: float = 3.0
    ):
        """
        初始化股票管理器。

        Args:
            data_dir: 数据保存目录，默认为 "data"
            db_path: SQLite 数据库路径，默认为 data_dir/stock_data.db
            enable_proxy: 是否启用代理池
            min_delay: 最小请求延迟（秒）
            max_delay: 最大请求延迟（秒）
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if db_path:
            self.db_path = db_path
        else:
            self.db_path = str(self.data_dir / "stock_data.db")

        # 初始化代理管理器
        self.enable_proxy = enable_proxy
        self.proxy_manager = None
        if enable_proxy:
            logger.info("正在初始化代理管理器...")
            self.proxy_manager = ProxyManager(
                enable_proxy=True,
                min_delay=min_delay,
                max_delay=max_delay
            )
            # 获取并验证代理
            self.proxy_manager.fetch_proxies(max_proxies=20)
            if self.proxy_manager.proxies:
                self.proxy_manager.verify_all_proxies(sample_size=10)
            logger.info(f"代理管理器初始化完成，可用代理: {len(self.proxy_manager.proxies)}")

        # 延迟配置
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = None

        if ak is None:
            raise ImportError(
                "akshare is required for StockManager. "
                "Install it with: pip install akshare"
            )
    
    def get_index_constituents(self, index_code: str = "000300") -> pd.DataFrame:
        """
        获取指数成分股列表。
        
        Args:
            index_code: 指数代码
                - "000300": 沪深300 (默认)
                - "000016": 上证50
                - "000905": 中证500
                - "000852": 中证1000
                
        Returns:
            DataFrame 包含成分股信息
            columns: [代码, 名称, 行业, 权重, ...]
        """
        try:
            print(f"正在获取指数 {index_code} 的成分股...")
            
            # 使用 AKShare 获取成分股
            if index_code == "000300":
                # 沪深300
                df = ak.index_stock_cons_weight_csindex(symbol="000300")
            elif index_code == "000016":
                # 上证50
                df = ak.index_stock_cons_weight_csindex(symbol="000016")
            elif index_code == "000905":
                # 中证500
                df = ak.index_stock_cons_weight_csindex(symbol="000905")
            elif index_code == "000852":
                # 中证1000
                df = ak.index_stock_cons_weight_csindex(symbol="000852")
            else:
                # 通用接口
                df = ak.index_stock_cons_weight_csindex(symbol=index_code)
            
            print(f"[OK] 成功获取 {len(df)} 只成分股")
            return df
            
        except Exception as e:
            print(f"[ERROR] 获取成分股失败: {e}")
            return pd.DataFrame()
    
    def get_stock_history(
        self, 
        stock_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取个股历史行情数据。
        
        Args:
            stock_code: 股票代码 (如 '000001')
            start_date: 开始日期 (格式: 'YYYYMMDD')，默认一年前
            end_date: 结束日期 (格式: 'YYYYMMDD')，默认今天
            period: 周期 ('daily', 'weekly', 'monthly')
            adjust: 复权方式 ('qfq': 前复权, 'hfq': 后复权, '': 不复权)
            
        Returns:
            DataFrame 包含历史行情数据
            columns: [日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率]
        """
        try:
            # 设置默认日期
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if not df.empty:
                # 添加股票代码列
                df['股票代码'] = stock_code
                
                # 调整列顺序
                cols = ['股票代码'] + [col for col in df.columns if col != '股票代码']
                df = df[cols]
            
            return df
            
        except Exception as e:
            print(f"[ERROR] 获取股票 {stock_code} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def _apply_delay(self):
        """应用随机延迟，防止请求过快"""
        delay = random.uniform(self.min_delay, self.max_delay)

        # 如果距离上次请求时间太短，额外延迟
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < delay:
                extra_delay = delay - elapsed
                logger.debug(f"请求间隔太短，额外延迟 {extra_delay:.2f}s")
                time.sleep(extra_delay)

        time.sleep(delay)
        self.last_request_time = time.time()

    @with_retry(max_retries=3, delay=2.0)
    def get_stock_history_with_retry(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取个股历史行情数据（带重试机制）。

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 周期
            adjust: 复权方式

        Returns:
            DataFrame 包含历史行情数据
        """
        # 应用延迟
        self._apply_delay()

        # 设置默认日期
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        try:
            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if not df.empty:
                # 添加股票代码列
                df['股票代码'] = stock_code

                # 调整列顺序
                cols = ['股票代码'] + [col for col in df.columns if col != '股票代码']
                df = df[cols]

            return df

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
            raise  # 重新抛出异常，触发重试

    def get_stocks_history(
        self,
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        show_progress: bool = True,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """
        批量获取多只股票的历史数据（带防爬机制）。

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            show_progress: 是否显示进度
            max_retries: 每只股票最大重试次数

        Returns:
            DataFrame 包含所有股票的历史数据
        """
        all_data = []
        total = len(stock_codes)
        failed_stocks = []

        for i, code in enumerate(stock_codes, 1):
            if show_progress:
                print(f"[{i}/{total}] 获取 {code} 的历史数据...")

            # 尝试获取数据（带重试）
            for attempt in range(max_retries):
                try:
                    df = self.get_stock_history_with_retry(
                        code, start_date, end_date
                    )
                    if not df.empty:
                        all_data.append(df)
                        break  # 成功获取，跳出重试循环
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # 递增延迟
                        logger.warning(f"获取 {code} 失败，{wait_time}秒后重试...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"获取 {code} 失败，已达最大重试次数")
                        failed_stocks.append(code)

            # 每10只股票额外延迟一次，降低被封风险
            if i % 10 == 0:
                extra_delay = random.uniform(5, 10)
                logger.info(f"已处理 {i} 只股票，额外延迟 {extra_delay:.1f} 秒...")
                time.sleep(extra_delay)

        # 输出统计
        success_count = len(all_data)
        failed_count = len(failed_stocks)

        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            print(f"\n[OK] 成功获取 {success_count}/{total} 只股票的数据，共 {len(result)} 条记录")
            if failed_stocks:
                print(f"[WARN] 以下 {failed_count} 只股票获取失败: {', '.join(failed_stocks[:5])}{'...' if failed_count > 5 else ''}")
            return result
        else:
            print("\n[ERROR] 未获取到任何数据")
            return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        保存 DataFrame 到 CSV 文件。
        
        Args:
            df: 要保存的数据
            filename: 文件名（不含路径）
            
        Returns:
            保存的文件路径
        """
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"[OK] 数据已保存到: {filepath}")
        return str(filepath)
    
    def init_sqlite_tables(self) -> None:
        """
        初始化 SQLite 数据库表结构。
        创建股票历史数据表和成分股表，并建立索引。
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建股票历史数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    close REAL,
                    high REAL,
                    low REAL,
                    volume INTEGER,
                    amount REAL,
                    amplitude REAL,
                    pct_change REAL,
                    change_amount REAL,
                    turnover REAL,
                    UNIQUE(stock_code, date)
                )
            ''')
            
            # 创建成分股表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS index_constituents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_code TEXT NOT NULL,
                    index_name TEXT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    weight REAL,
                    update_date TEXT,
                    UNIQUE(index_code, stock_code, update_date)
                )
            ''')
            
            # 创建索引以加速查询
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_code ON stock_history(stock_code)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_history(date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_code_date ON stock_history(stock_code, date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_index_code ON index_constituents(index_code)
            ''')
            
            conn.commit()
            conn.close()
            print(f"[OK] SQLite 表结构初始化完成: {self.db_path}")
        except Exception as e:
            print(f"[ERROR] 初始化 SQLite 表失败: {e}")
    
    def save_to_sqlite(
        self, 
        df: pd.DataFrame, 
        table_name: str = "stock_history",
        if_exists: str = "append"
    ) -> None:
        """
        保存 DataFrame 到 SQLite 数据库。
        
        Args:
            df: 要保存的数据
            table_name: 表名
            if_exists: 如果表存在 ('fail', 'replace', 'append')
        """
        try:
            # 先初始化表结构
            self.init_sqlite_tables()
            
            conn = sqlite3.connect(self.db_path)
            
            # 重命名列以匹配数据库表结构
            column_mapping = {
                '股票代码': 'stock_code',
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change_amount',
                '换手率': 'turnover',
                # 成分股表字段映射
                '指数代码': 'index_code',
                '指数名称': 'index_name',
                '成分券代码': 'stock_code',
                '成分券名称': 'stock_name',
                '权重': 'weight',
                '日期': 'update_date'
            }
            
            # 只映射存在的列
            rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
            df_renamed = df.rename(columns=rename_dict)
            
            # 保存到数据库，使用 REPLACE 来处理重复数据
            df_renamed.to_sql(table_name, conn, if_exists=if_exists, index=False,
                            method='multi', chunksize=1000)
            
            conn.close()
            print(f"[OK] 数据已保存到 SQLite: {self.db_path} (表: {table_name}, 记录数: {len(df)})")
        except Exception as e:
            print(f"[ERROR] 保存到 SQLite 失败: {e}")
    
    def query_stock_history(
        self, 
        stock_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        从 SQLite 查询单只股票历史数据。
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (格式: 'YYYY-MM-DD')
            end_date: 结束日期 (格式: 'YYYY-MM-DD')
            
        Returns:
            DataFrame 包含历史数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
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
            conn.close()
            return df
        except Exception as e:
            print(f"[ERROR] 查询股票 {stock_code} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def query_all_stocks(self) -> pd.DataFrame:
        """
        从 SQLite 查询所有股票代码列表。
        
        Returns:
            DataFrame 包含所有股票代码
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT DISTINCT stock_code FROM stock_history ORDER BY stock_code",
                conn
            )
            conn.close()
            return df
        except Exception as e:
            print(f"[ERROR] 查询股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_count(self) -> int:
        """
        获取数据库中股票数量。
        
        Returns:
            股票数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT stock_code) FROM stock_history")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
    
    def get_record_count(self) -> int:
        """
        获取数据库中总记录数。
        
        Returns:
            记录数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stock_history")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息。
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票信息字典
        """
        try:
            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=stock_code)
            
            if not df.empty:
                # 转换为字典
                info = dict(zip(df['item'], df['value']))
                return info
            else:
                return {}
                
        except Exception as e:
            print(f"[ERROR] 获取股票 {stock_code} 信息失败: {e}")
            return {}
    
    def get_all_a_stocks(self) -> pd.DataFrame:
        """
        获取所有A股股票列表。
        
        Returns:
            DataFrame 包含所有A股信息
        """
        try:
            print("正在获取所有A股列表...")
            df = ak.stock_zh_a_spot_em()
            print(f"[OK] 成功获取 {len(df)} 只股票")
            return df
        except Exception as e:
            print(f"[ERROR] 获取A股列表失败: {e}")
            return pd.DataFrame()


def main():
    """
    示例用法
    """
    # 创建管理器
    manager = StockManager()
    
    # 获取沪深300成分股
    hs300 = manager.get_index_constituents("000300")
    print(f"\n沪深300成分股:\n{hs300.head()}")
    
    # 获取前5只股票的历史数据
    if not hs300.empty:
        stock_codes = hs300['成分券代码'].head(5).tolist()
        history = manager.get_stocks_history(stock_codes)
        
        # 保存到CSV
        if not history.empty:
            manager.save_to_csv(history, "hs300_history.csv")


if __name__ == "__main__":
    main()
