#!/usr/bin/env python3
"""
股票分析系统入口脚本 - 命令行模式

用法:
    python run.py                    # 运行默认扫描
    python run.py --web             # 启动 Web 服务
    python run.py --analysis        # 运行股票关系分析
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--web':
            # Run web app
            from src.web.app import app
            app.run(debug=True, host='0.0.0.0', port=5000)
        elif sys.argv[1] == '--analysis':
            # Run analysis
            from src.analysis.relationships import main as analysis_main
            analysis_main()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python run.py [--web|--analysis]")
    else:
        # Run CLI mode
        import asyncio
        from src.core.main import main
        asyncio.run(main())
