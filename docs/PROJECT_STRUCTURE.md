# Stock Analysis MVP - 项目结构文档

## 项目概述

基于 Playwright + CV + 数据库存储的"极致缩量"信号股票初筛系统。

## 技术栈

- **后端**: Python 3.10+
- **Web 框架**: Flask + Flask-CORS
- **数据源**: AKShare (推荐), Sina Finance, East Money
- **数据库**: SQLite (本地) / Supabase (云端)
- **数据处理**: Pandas, NumPy
- **前端**: HTML + CSS + JavaScript

## 文件结构

```
stock_analysis/
├── main.py                     # 主程序 - 命令行模式
├── app.py                      # Flask Web 应用
├── data_sources.py             # 数据源模块
├── analyze_relationships.py    # 股票关系分析模块
├── concept_index_to_sqlite.py  # 概念指数数据导入
├── stock_data_to_sqlite.py     # 股票数据导入SQLite
├── crawl_alibaba_concept.py    # 爬虫脚本
├── crawl_alibaba_concept_playwright.py
├── pyproject.toml              # Python 依赖管理
├── uv.lock                     # uv 锁文件
├── README.md                   # 项目说明
├── .env                        # 环境变量 (需手动创建)
├── .gitignore                  # Git 忽略配置
├── static/
│   ├── style.css              # Web 界面样式
│   └── app.js                 # Web 界面交互脚本
├── templates/
│   └── index.html             # Web 界面模板
└── supabase_schema.sql        # Supabase 数据库表结构
```

## 核心模块说明

### 1. main.py
**功能**: 命令行模式的股票扫描程序

**主要函数**:
- `init_sqlite_db()`: 初始化 SQLite 数据库
- `scrape_stock_data()`: 获取股票实时数据
- `detect_signal()`: 检测极致缩量信号
- `store_signal()`: 存储信号到数据库

**配置参数**:
- `THRESHOLD_VOLUME_RATIO`: 成交量比阈值 (默认 0.2)
- `THRESHOLD_PRICE_CHANGE`: 价格变动阈值 (默认 0.05)
- `LOOKBACK_DAYS`: 回溯天数 (默认 20)

### 2. app.py
**功能**: Web 服务，提供 HTTP API 和用户界面

**API 端点**:
- `GET /`: 主页
- `POST /api/scan/start`: 启动扫描
- `GET /api/scan/status`: 获取扫描状态
- `GET /api/signals`: 获取所有信号
- `GET /api/config`: 获取系统配置

### 3. data_sources.py
**功能**: 多数据源支持

**数据源类**:
- `AKShareDataSource`: AKShare (推荐，数据最全)
- `SinaFinanceDataSource`: 新浪财经
- `EastMoneyDataSource`: 东方财富

**工厂类**:
- `StockDataSourceFactory`: 根据名称创建数据源实例

### 4. analyze_relationships.py
**功能**: 股票关系分析

**分析功能**:
- 相关性分析
- K-means 聚类
- 关系网络构建
- 行业/概念相关性分析

## 使用方法

### 命令行模式

```bash
# 使用 SQLite (推荐本地开发)
uv run python main.py

# 使用 Supabase
SUPABASE_URL=xxx SUPABASE_KEY=xxx uv run python main.py
```

### Web 模式

```bash
# Windows
start_web.bat

# 或手动启动
uv run python app.py
```

然后访问 `http://localhost:5000`

## 环境变量配置

创建 `.env` 文件：

```env
# 数据库配置
USE_SQLITE=true
SQLITE_DB_PATH=stock_signals.db

# Supabase 配置 (如不使用 SQLite)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# 数据源配置
DEFAULT_DATA_SOURCE=akshare

# 信号检测参数
THRESHOLD_VOLUME_RATIO=0.2
THRESHOLD_PRICE_CHANGE=0.05
LOOKBACK_DAYS=20
```

## 安装步骤

1. **安装依赖**
   ```bash
   uv sync
   ```

2. **安装 Playwright 浏览器**
   ```bash
   uv run playwright install
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件配置数据库
   ```

4. **初始化数据库** (如果使用 SQLite)
   ```bash
   uv run python -c "from main import init_sqlite_db; init_sqlite_db('stock_signals.db')"
   ```

## 信号检测逻辑

系统检测"极致缩量"信号，判断条件：

1. **成交量条件**: `当前成交量 < 阈值 × 近期最大成交量`
   - 默认阈值: 20%
   - 表示成交量萎缩至近期高点的 20% 以下

2. **价格条件**: `|价格变动| < 阈值`
   - 默认阈值: 5%
   - 表示价格在回溯期内保持稳定，处于横盘整理状态

当两个条件同时满足时，产生信号。

## 数据库表结构

### signals 表

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,           -- 股票代码
    signal_date DATE NOT NULL,          -- 信号日期
    volume_ratio REAL NOT NULL,         -- 成交量比
    price_change REAL NOT NULL,         -- 价格变动
    max_volume_recent INTEGER NOT NULL, -- 近期最大成交量
    current_volume INTEGER NOT NULL,    -- 当前成交量
    current_price REAL NOT NULL,        -- 当前价格
    source TEXT NOT NULL,               -- 数据来源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 开发计划

### 已完成
- [x] 多数据源支持 (AKShare/Sina/EastMoney)
- [x] 双数据库支持 (SQLite/Supabase)
- [x] Web 界面
- [x] 信号检测算法
- [x] 股票关系分析

### 待完善
- [ ] 更丰富的数据源 (更多券商 API)
- [ ] 信号回测功能
- [ ] 邮件/微信通知
- [ ] 定时任务调度
- [ ] 可视化图表增强

## 注意事项

1. **数据获取频率**: 请控制请求频率，避免被封禁
2. **免责声明**: 本系统仅供学习研究，不构成投资建议
3. **数据准确性**: 历史数据仅供参考，请以官方数据为准
4. **API 限制**: 免费数据源可能有访问限制

## 贡献指南

欢迎提交 Issue 和 PR：
1. Fork 本仓库
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
