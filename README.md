# Stock Analysis MVP - README

## 项目概述

基于 Playwright + CV + 数据库存储的"极致缩量"信号股票初筛与策略验证系统。

## 功能特性

- **多数据源支持**: AKShare (推荐)、新浪财经、东方财富
- **双数据库支持**: SQLite (本地) / Supabase (云端)
- **信号检测**: 自动识别极致缩量信号（低成交量 + 价格横盘）
- **Web 界面**: 友好的可视化界面，支持一键扫描
- **关系分析**: 股票相关性分析、聚类分析、网络分析

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv 安装依赖 (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和数据源
```

### 3. 运行程序

**命令行模式**:
```bash
uv run python run.py
```

**Web 界面**:
```bash
# Windows
start_web.bat

# 或手动启动
uv run python run.py --web
```

访问 `http://localhost:5000`

**股票关系分析**:
```bash
uv run python run.py --analysis
```

## 信号检测逻辑

系统检测"极致缩量"信号，当以下条件同时满足时触发：

1. **成交量条件**: `当前成交量 < 20% × 近期最大成交量`
2. **价格条件**: `|价格变动| < 5%`

## 技术栈

- **后端**: Python 3.10+, Flask, Pandas
- **数据源**: AKShare, Sina Finance, East Money
- **数据库**: SQLite / Supabase
- **前端**: HTML5, CSS3, JavaScript
- **分析**: scikit-learn, NetworkX, Matplotlib

## 项目结构

```
stock_analysis/
├── run.py                      # 统一入口脚本
├── start_web.bat              # Windows 启动脚本
├── pyproject.toml             # Python 依赖配置
├── README.md                  # 项目说明
├── .gitignore                 # Git 忽略配置
│
├── config/                    # 配置文件目录
│   ├── .env.example          # 环境变量模板
│   └── supabase_schema.sql   # 数据库表结构
│
├── data/                      # 数据目录（存放生成的数据文件）
│   └── .gitkeep              # 保持目录存在
│
├── docs/                      # 文档目录
│   └── PROJECT_STRUCTURE.md  # 详细项目文档
│
├── scripts/                   # 独立脚本目录
│   ├── crawl_alibaba_concept.py
│   ├── crawl_alibaba_concept_playwright.py
│   ├── concept_index_to_sqlite.py
│   └── stock_data_to_sqlite.py
│
├── src/                       # 源代码目录
│   ├── __init__.py
│   │
│   ├── core/                 # 核心模块
│   │   ├── __init__.py
│   │   └── main.py          # 信号检测主程序
│   │
│   ├── data/                 # 数据模块
│   │   ├── __init__.py
│   │   └── sources.py       # 数据源实现
│   │
│   ├── analysis/             # 分析模块
│   │   ├── __init__.py
│   │   └── relationships.py # 股票关系分析
│   │
│   └── web/                  # Web 应用
│       ├── __init__.py
│       ├── app.py           # Flask 应用
│       ├── static/          # 前端资源
│       │   ├── style.css
│       │   └── app.js
│       └── templates/       # HTML 模板
│           └── index.html
│
└── tests/                     # 测试文件目录
```

**说明**: `data/` 目录用于存放运行时生成的数据文件（SQLite 数据库、CSV、图表等），这些文件不会被 Git 跟踪。
stock_analysis/
├── run.py                      # 统一入口脚本
├── start_web.bat              # Windows 启动脚本
├── pyproject.toml             # Python 依赖配置
├── README.md                  # 项目说明
├── config/                    # 配置文件
│   ├── .env.example          # 环境变量模板
│   └── supabase_schema.sql   # 数据库表结构
├── docs/                      # 文档
│   └── PROJECT_STRUCTURE.md  # 详细项目文档
├── scripts/                   # 独立脚本
│   ├── crawl_alibaba_concept.py
│   ├── concept_index_to_sqlite.py
│   └── stock_data_to_sqlite.py
├── src/                       # 源代码
│   ├── core/                 # 核心模块
│   │   └── main.py          # 信号检测主程序
│   ├── data/                 # 数据模块
│   │   └── sources.py       # 数据源实现
│   ├── analysis/             # 分析模块
│   │   └── relationships.py # 股票关系分析
│   └── web/                  # Web 应用
│       ├── app.py           # Flask 应用
│       ├── static/          # 前端资源
│       │   ├── style.css
│       │   └── app.js
│       └── templates/       # HTML 模板
│           └── index.html
└── tests/                     # 测试文件
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `USE_SQLITE` | 使用 SQLite 数据库 | `true` |
| `SQLITE_DB_PATH` | SQLite 数据库路径 | `stock_signals.db` |
| `SUPABASE_URL` | Supabase URL | - |
| `SUPABASE_KEY` | Supabase API Key | - |
| `DEFAULT_DATA_SOURCE` | 默认数据源 | `akshare` |
| `THRESHOLD_VOLUME_RATIO` | 成交量比阈值 | `0.2` |
| `THRESHOLD_PRICE_CHANGE` | 价格变动阈值 | `0.05` |
| `LOOKBACK_DAYS` | 回溯天数 | `20` |

### 数据源选择

编辑 `.env` 文件切换数据源：

```env
# AKShare (推荐，数据最全)
DEFAULT_DATA_SOURCE=akshare

# 新浪财经
DEFAULT_DATA_SOURCE=sina_finance

# 东方财富
DEFAULT_DATA_SOURCE=eastmoney
```

## API 接口

### Web API

- `GET /` - 主页
- `POST /api/scan/start` - 启动扫描
- `GET /api/scan/status` - 获取扫描状态
- `GET /api/signals` - 获取所有信号
- `GET /api/config` - 获取系统配置

## 使用示例

### 扫描指定股票

```python
import asyncio
import sys
sys.path.insert(0, 'src')

from src.core.main import main

# 扫描指定股票
stock_codes = ['000001', '000002', '600000']
signals = asyncio.run(main(stock_codes))

print(f"检测到 {len(signals)} 个信号")
```

### 分析股票关系

```python
import sys
sys.path.insert(0, 'src')

from src.analysis.relationships import StockRelationshipAnalyzer

analyzer = StockRelationshipAnalyzer('stock_history.db')

# 计算相关性
corr = analyzer.calculate_correlation()
print(corr)

# 聚类分析
clusters = analyzer.cluster_stocks(n_clusters=5)
print(clusters)

analyzer.close()
```

## 注意事项

1. **数据获取频率**: 请控制请求频率，避免被封禁
2. **免责声明**: 本系统仅供学习研究，不构成投资建议
3. **数据准确性**: 历史数据仅供参考，请以官方数据为准

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 PR！
