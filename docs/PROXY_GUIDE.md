# 代理池和防爬机制使用指南

## 简介

为了提高数据获取的稳定性和成功率，系统集成了代理池和防爬机制。

## 功能特性

### 1. 代理池
- 从免费代理源自动获取代理
- 代理验证和筛选（自动移除无效代理）
- 代理轮换机制
- 支持 HTTP/HTTPS 代理

### 2. 防爬机制
- **随机延迟**：每次请求前随机等待 1-3 秒（可配置）
- **递增重试**：失败后自动重试，延迟时间递增
- **批量延迟**：每处理 10 只股票额外延迟 5-10 秒
- **User-Agent 轮换**：每次请求使用不同的 User-Agent

## 使用方法

### 命令行参数

```bash
# 基本用法（仅使用防爬机制）
python scripts/fetch_hs300_data.py

# 启用代理池
python scripts/fetch_hs300_data.py --proxy

# 调整延迟时间（更保守）
python scripts/fetch_hs300_data.py --min-delay 2.0 --max-delay 5.0

# 完整示例
python scripts/fetch_hs300_data.py \
    --proxy \
    --min-delay 1.5 \
    --max-delay 4.0 \
    --limit 20 \
    --csv
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--proxy` | 启用代理池 | 禁用 |
| `--min-delay` | 最小请求延迟（秒） | 1.0 |
| `--max-delay` | 最大请求延迟（秒） | 3.0 |
| `--limit` | 限制股票数量 | 无限制 |
| `--csv` | 导出 CSV 文件 | 仅 SQLite |

### Python API

```python
from data.stock_manager import StockManager

# 创建管理器（启用代理和防爬机制）
manager = StockManager(
    enable_proxy=True,      # 启用代理池
    min_delay=1.0,          # 最小延迟 1 秒
    max_delay=3.0           # 最大延迟 3 秒
)

# 获取数据（自动应用防爬机制）
df = manager.get_stocks_history(['000001', '000002'])
```

## 代理源

系统从以下免费代理源获取代理：

1. **free-proxy-list.net** - 提供免费 HTTP/HTTPS 代理
2. **sslproxies.org** - 专门提供 SSL 代理

> **注意**：免费代理不稳定，可能随时失效。建议：
> - 小批量数据获取时可不启用代理
> - 大批量获取时建议启用代理
> - 如遇连接问题，可增加延迟时间

## 防爬机制详情

### 1. 随机延迟

```python
# 每次请求前随机等待 1-3 秒
delay = random.uniform(1.0, 3.0)
time.sleep(delay)
```

### 2. 自动重试

```python
# 失败自动重试，最多 3 次
# 每次重试延迟递增：2s, 4s, 6s
for attempt in range(3):
    try:
        data = fetch_stock(code)
        break
    except:
        time.sleep((attempt + 1) * 2)
```

### 3. 批量延迟

```python
# 每处理 10 只股票，额外延迟 5-10 秒
if processed % 10 == 0:
    time.sleep(random.uniform(5, 10))
```

### 4. User-Agent 轮换

```python
# 每次请求随机选择 User-Agent
headers = {
    'User-Agent': random.choice(USER_AGENTS)
}
```

## 推荐配置

### 场景一：测试/小批量（< 50只股票）
```bash
# 不需要代理，使用默认延迟即可
python scripts/fetch_hs300_data.py --limit 50
```

### 场景二：中批量（50-200只股票）
```bash
# 建议启用代理，增加延迟
python scripts/fetch_hs300_data.py \
    --proxy \
    --min-delay 1.5 \
    --max-delay 4.0 \
    --limit 100
```

### 场景三：大批量（200+只股票）
```bash
# 必须启用代理，保守延迟
python scripts/fetch_hs300_data.py \
    --proxy \
    --min-delay 2.0 \
    --max-delay 5.0
```

### 场景四：遇到封禁/限速
```bash
# 大幅增加延迟
python scripts/fetch_hs300_data.py \
    --proxy \
    --min-delay 3.0 \
    --max-delay 8.0 \
    --limit 50
```

## 故障排查

### 问题：获取代理失败

**原因**：免费代理源可能被封锁或不可用

**解决**：
1. 检查网络连接
2. 稍后重试
3. 暂时不使用代理（`--proxy` 参数）

### 问题：大量请求失败

**原因**：请求频率过高被服务器限制

**解决**：
1. 增加延迟时间：`--min-delay 2.0 --max-delay 5.0`
2. 减少每批数量：`--limit 50`
3. 启用代理：`--proxy`

### 问题：代理验证通过但实际获取数据失败

**原因**：免费代理质量不稳定

**解决**：
1. 脚本会自动移除失败代理
2. 如可用代理太少，会提示重新获取
3. 考虑不使用代理，直接请求

## 注意事项

1. **免费代理不稳定**：免费代理随时可能失效，建议重要数据获取时增加重试次数
2. **延迟时间**：延迟越长，成功率越高，但获取时间也越长
3. **分批获取**：大量数据建议分批获取，避免一次性请求过多
4. **尊重服务器**：即使使用了防爬机制，也请合理控制请求频率

## 高级用法

### 自定义代理管理器

```python
from data.proxy_manager import ProxyManager

# 创建自定义代理管理器
proxy_manager = ProxyManager(
    enable_proxy=True,
    min_delay=2.0,
    max_delay=5.0,
    max_fail_count=2,      # 最大失败 2 次就移除
    timeout=15              # 代理验证超时 15 秒
)

# 获取代理
proxy_manager.fetch_proxies(max_proxies=50)
proxy_manager.verify_all_proxies()

# 使用代理发送请求
response = proxy_manager.request('http://example.com')
```

### 仅使用防爬机制（不使用代理）

```python
# 创建 StockManager，不启用代理
manager = StockManager(enable_proxy=False)

# 仍会应用随机延迟和重试机制
df = manager.get_stocks_history(codes)
```
