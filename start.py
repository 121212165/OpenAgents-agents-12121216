#!/usr/bin/env python3
"""
小游探启动脚本 - Docker专用
"""
import sys
import os
from pathlib import Path

# 确保项目根目录在Python路径中
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# 设置环境变量
os.environ.setdefault('PYTHONPATH', str(ROOT_DIR))

if __name__ == "__main__":
    # 导入并运行主程序
    from src.main import main
    import asyncio
    
    # 添加--openagents参数
    if "--openagents" not in sys.argv:
        sys.argv.append("--openagents")
    
    # 运行主程序
    asyncio.run(main())