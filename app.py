from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import subprocess
import threading
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Configuration
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"  # Default to SQLite for web mode
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "stock_signals.db")

# Global scan status
scan_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'results': []
}

def init_sqlite_db(db_path: str):
    """Initialize SQLite database and create signals table."""
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
    print(f"SQLite database initialized at {db_path}")

def run_scan_async():
    """Run stock scan in background thread"""
    global scan_status
    try:
        scan_status['running'] = True
        scan_status['progress'] = 10
        scan_status['message'] = '正在初始化扫描...'

        # Run main.py as subprocess
        env = os.environ.copy()
        env['USE_SQLITE'] = str(USE_SQLITE)

        result = subprocess.run(['python', 'main.py'], capture_output=True, text=True, env=env)

        if result.returncode == 0:
            scan_status['progress'] = 100
            scan_status['message'] = '扫描完成'
        else:
            scan_status['message'] = f'扫描失败: {result.stderr}'

    except Exception as e:
        scan_status['message'] = f'错误: {str(e)}'
    finally:
        scan_status['running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    global scan_status

    if scan_status['running']:
        return jsonify({'error': 'Scan already running'}), 400

    # Start scan in background thread
    thread = threading.Thread(target=run_scan_async)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started'})

@app.route('/api/scan/status')
def get_scan_status():
    return jsonify(scan_status)

@app.route('/api/signals')
def get_signals():
    if USE_SQLITE:
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
    else:
        return jsonify({'error': 'SQLite not enabled'}), 400

@app.route('/api/config')
def get_config():
    return jsonify({
        'use_sqlite': USE_SQLITE,
        'sqlite_path': SQLITE_DB_PATH if USE_SQLITE else None
    })

if __name__ == '__main__':
    # Initialize database if using SQLite
    if USE_SQLITE:
        init_sqlite_db(SQLITE_DB_PATH)

    app.run(debug=True, host='0.0.0.0', port=5000)