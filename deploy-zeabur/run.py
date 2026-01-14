#!/usr/bin/env python3
"""
小游探启动脚本 - Zeabur 专用
"""
import sys
import os
from pathlib import Path

# 设置路径
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))
os.environ.setdefault("PYTHONPATH", str(ROOT_DIR))

# Zeabur 端口处理：如果 Zeabur 设置了 PORT，使用它；否则使用 8000
if os.getenv("PORT"):
    port = os.getenv("PORT")
    os.environ["OPENAGENTS_PORT"] = port
    print(f"[Zeabur] 检测到 PORT 环境变量: {port}")
else:
    os.environ.setdefault("OPENAGENTS_PORT", "8000")
    print(f"[默认] 使用默认端口: 8000")

os.environ.setdefault("OPENAGENTS_HOST", "0.0.0.0")

print(f"[配置] OPENAGENTS_HOST={os.getenv('OPENAGENTS_HOST')}")
print(f"[配置] OPENAGENTS_PORT={os.getenv('OPENAGENTS_PORT')}")
print(f"[启动] 开始初始化...")

if __name__ == "__main__":
    try:
        from src.main import main
        import asyncio

        # 添加 openagents 参数
        if "--openagents" not in sys.argv:
            sys.argv.append("--openagents")

        print("[启动] 启动小游探服务...")
        asyncio.run(main())
    except Exception as e:
        print(f"[错误] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
