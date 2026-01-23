# Stock Analysis MVP - README

## 项目概述
基于 Playwright 自动截图 + CV 初筛 + Supabase 存储的"极致缩量"信号股票初筛与策略验证系统。

## 功能特性
- 自动扫描指定股票池
- 识别极致缩量信号（低成交量 + 价格横盘）
- 数据存储到 Supabase 云数据库
- 支持结构化数据提取和 OCR 备选方案

## 安装步骤
1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 安装 Playwright 浏览器：`playwright install`
4. 配置 Supabase：在 `.env` 文件中设置 URL 和 API Key
5. 在 Supabase 中执行 `supabase_schema.sql` 创建表

## 使用方法
运行主脚本：`python main.py`

## 配置说明
- `THRESHOLD_VOLUME_RATIO`: 成交量比阈值 (默认 0.2)
- `THRESHOLD_PRICE_CHANGE`: 价格变动阈值 (默认 0.05)
- `LOOKBACK_DAYS`: 回溯天数 (默认 20)

## 注意事项
- 当前历史数据使用模拟数据，实际部署需实现真实数据获取
- OCR 功能需要训练模型以准确识别价格和成交量区域
- 请遵守网站使用条款，避免高频请求

## 技术栈
- Playwright: 网页自动化和截图
- Supabase: 云数据库存储
- Pandas: 数据处理
- OpenCV + Tesseract: 图像处理和 OCR