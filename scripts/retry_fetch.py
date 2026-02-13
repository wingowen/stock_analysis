#!/usr/bin/env python3
"""
再次尝试获取股票历史数据 - 使用增强的重试机制
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import requests
import pandas as pd

print("="*70)
print("尝试获取股票历史数据")
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# 测试股票
test_codes = ['000001', '000002', '600000']
start_date = '20250201'
end_date = '20250213'

# 数据源配置
apis = [
    {
        'name': '东方财富',
        'url': 'https://push2his.eastmoney.com/api/qt/stock/kline/get',
        'params_func': lambda code: {
            'secid': f"{('1' if code.startswith('6') else '0')}.{code}",
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',
            'fqt': '0',
            'beg': start_date,
            'end': end_date,
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/'
        }
    },
    {
        'name': '腾讯财经',
        'url': 'https://web.ifzq.gtimg.cn/appstock/finance_panel/getfqkline',
        'params_func': lambda code: {
            'param': f"{'sh' if code.startswith('6') else 'sz'}{code},day,,,1000,qfq",
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://stock.finance.qq.com/'
        }
    }
]

results = {}

for code in test_codes:
    print(f"\n测试股票 {code}:")
    print("-" * 70)
    
    for api in apis:
        print(f"  尝试 {api['name']}...", end=" ")
        
        try:
            # 指数退避重试
            for attempt in range(3):
                try:
                    response = requests.get(
                        api['url'],
                        params=api['params_func'](code),
                        headers=api['headers'],
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # 检查是否有数据
                        if api['name'] == '东方财富':
                            if data.get('data') and data['data'].get('klines'):
                                count = len(data['data']['klines'])
                                print(f"[OK] {count}条记录")
                                results[code] = api['name']
                                break
                        elif api['name'] == '腾讯财经':
                            key = f"{'sh' if code.startswith('6') else 'sz'}{code}"
                            if data.get('data', {}).get(key, {}).get('qfqday'):
                                count = len(data['data'][key]['qfqday'])
                                print(f"[OK] {count}条记录")
                                results[code] = api['name']
                                break
                    
                    # 如果到这里还没break，说明没有数据
                    if attempt < 2:
                        wait = (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(wait)
                        
                except Exception as e:
                    if attempt < 2:
                        wait = (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(wait)
                    else:
                        raise
            else:
                print("[无数据]")
                
        except Exception as e:
            print(f"[失败] {str(e)[:50]}")

print("\n" + "="*70)
print("测试结果汇总:")
print("="*70)

if results:
    print(f"\n成功获取 {len(results)} 只股票:")
    for code, source in results.items():
        print(f"  {code} - {source}")
    
    # 如果有成功的，立即开始批量获取
    print("\n" + "="*70)
    print("有可用数据源！开始批量获取沪深300数据...")
    print("="*70)
else:
    print("\n所有数据源仍然无法访问")
    print("建议:")
    print("  1. 检查网络连接")
    print("  2. 稍后重试（可能服务器临时限制）")
    print("  3. 尝试更换网络环境")
