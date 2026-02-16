"""
Stock Analysis Web Application

Flask Web 应用，提供：
- 股票信号扫描 Web 界面
- RESTful API 接口
- 实时扫描进度显示
"""

import os
import sqlite3
import subprocess
import threading
from datetime import datetime

from flask import Flask, render_template, jsonify
from flask_cors import CORS

# =============================================================================
# App Configuration
# =============================================================================

# Get the absolute path to the web directory
web_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(web_dir, 'templates')
static_dir = os.path.join(web_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)

# Database configuration
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/stock_signals.db")

# =============================================================================
# Global State
# =============================================================================

scan_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'results': [],
    'start_time': None
}

# Thread lock for status updates
status_lock = threading.Lock()


# =============================================================================
# Database Functions
# =============================================================================

def init_sqlite_db(db_path: str) -> None:
    """初始化 SQLite 数据库并创建信号表。"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            signal_date DATE NOT NULL,
            volume_ratio REAL NOT NULL,
            price_change REAL NOT NULL,
            max_volume_recent INTEGER NOT NULL,
            current_volume INTEGER NOT NULL,
            current_price REAL NOT NULL,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✓ SQLite database initialized at {db_path}")

def run_scan_async() -> None:
    """在后台线程中运行股票扫描。"""
    global scan_status
    
    with status_lock:
        scan_status['running'] = True
        scan_status['progress'] = 10
        scan_status['message'] = '正在初始化扫描...'
        scan_status['start_time'] = datetime.now().isoformat()
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['USE_SQLITE'] = str(USE_SQLITE).lower()
        
        # 运行扫描脚本
        result = subprocess.run(
            ['python', 'main.py'],
            capture_output=True,
            text=True,
            env=env,
            timeout=300  # 5分钟超时
        )
        
        with status_lock:
            if result.returncode == 0:
                scan_status['progress'] = 100
                scan_status['message'] = '扫描完成'
            else:
                scan_status['message'] = f'扫描失败: {result.stderr[:200]}'
                
    except subprocess.TimeoutExpired:
        with status_lock:
            scan_status['message'] = '扫描超时'
    except Exception as e:
        with status_lock:
            scan_status['message'] = f'错误: {str(e)}'
    finally:
        with status_lock:
            scan_status['running'] = False

# =============================================================================
# Routes
# =============================================================================

@app.route('/')
def index():
    """渲染主页。"""
    return render_template('index.html')


@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    """启动股票扫描。"""
    global scan_status

    with status_lock:
        if scan_status['running']:
            return jsonify({'error': '扫描已在运行中'}), 400

    # 在后台线程启动扫描
    thread = threading.Thread(target=run_scan_async, daemon=True)
    thread.start()

    return jsonify({'status': 'started', 'message': '扫描已启动'})


@app.route('/api/scan/status')
def get_scan_status():
    """获取扫描状态。"""
    with status_lock:
        return jsonify(scan_status)


@app.route('/api/signals')
def get_signals():
    """获取所有信号数据。"""
    if not USE_SQLITE:
        return jsonify({'error': 'SQLite not enabled'}), 400
    
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM signals ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()

        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'stock_code': row[1],
                'signal_date': row[2],
                'volume_ratio': row[3],
                'price_change': row[4],
                'max_volume_recent': row[5],
                'current_volume': row[6],
                'current_price': row[7],
                'source': row[8],
                'created_at': row[9]
            })
        return jsonify(signals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config')
def get_config():
    """获取系统配置。"""
    return jsonify({
        'use_sqlite': USE_SQLITE,
        'sqlite_path': SQLITE_DB_PATH if USE_SQLITE else None
    })


@app.route('/backtest')
def backtest_page():
    """渲染回测结果页面。"""
    return render_template('backtest.html')


@app.route('/api/backtest/results')
def get_backtest_results():
    """获取回测结果数据。"""
    import pandas as pd
    
    backtest_file = 'data/backtest_results.csv'
    
    if not os.path.exists(backtest_file):
        return jsonify({'error': '回测结果文件不存在，请先运行回测'}), 404
    
    try:
        df = pd.read_csv(backtest_file)
        
        # 计算统计指标
        total_trades = len(df)
        winning_trades = len(df[df['return_pct'] > 0])
        losing_trades = len(df[df['return_pct'] <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_return = df['return_pct'].mean()
        median_return = df['return_pct'].median()
        std_return = df['return_pct'].std()
        
        max_return = df['return_pct'].max()
        min_return = df['return_pct'].min()
        
        # 按日期分组计算每日表现
        df['signal_date'] = pd.to_datetime(df['signal_date'])
        daily_returns = df.groupby(df['signal_date'].dt.date).agg({
            'return_pct': 'mean'
        }).reset_index()
        daily_returns.columns = ['date', 'avg_return']
        
        # 转换为字典
        results = {
            'statistics': {
                'total_trades': int(total_trades),
                'winning_trades': int(winning_trades),
                'losing_trades': int(losing_trades),
                'win_rate': float(win_rate),
                'avg_return': float(avg_return),
                'median_return': float(median_return),
                'std_return': float(std_return),
                'max_return': float(max_return),
                'min_return': float(min_return)
            },
            'trades': df.to_dict('records'),
            'daily_returns': daily_returns.to_dict('records')
        }
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Main Entry
# =============================================================================

if __name__ == '__main__':
    # 初始化数据库
    if USE_SQLITE:
        init_sqlite_db(SQLITE_DB_PATH)

    print("\n" + "="*60)
    print("股票信号分析系统 Web 服务")
    print("="*60)
    print(f"访问地址: http://localhost:5000")
    print(f"数据库: {'SQLite' if USE_SQLITE else 'Supabase'}")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)