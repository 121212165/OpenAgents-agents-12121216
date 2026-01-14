#!/usr/bin/env python3
"""
小游探 - Zeabur专用启动脚本
处理云端部署的特殊需求
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# 设置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """设置环境"""
    # 设置Python路径
    ROOT_DIR = Path(__file__).parent
    sys.path.insert(0, str(ROOT_DIR))
    os.environ.setdefault("PYTHONPATH", str(ROOT_DIR))
    
    # Zeabur会自动设置PORT环境变量，不需要手动设置
    # 只在本地测试时设置默认值
    if not os.getenv("PORT"):
        logger.info("未检测到PORT环境变量，设置默认值8000（本地测试模式）")
        os.environ.setdefault("PORT", "8000")
    
    # 设置LLM配置（如果没有设置）
    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "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"
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        os.environ["OPENAI_MODEL"] = "xiaomi/mimo-v2-flash:free"
    
    # 创建必要目录
    Path("logs").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)
    
    logger.info("环境设置完成")

def check_dependencies():
    """检查依赖"""
    try:
        import aiohttp
        import openagents
        logger.info("✅ 核心依赖检查通过")
        return True
    except ImportError as e:
        logger.error(f"❌ 依赖检查失败: {e}")
        return False

async def start_application():
    """启动应用"""
    try:
        logger.info("🚀 正在启动小游探...")
        
        # 导入主程序
        from src.main import main
        
        # 添加openagents参数
        if "--openagents" not in sys.argv:
            sys.argv.append("--openagents")
        
        # 启动主程序
        await main()
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """主函数"""
    try:
        logger.info("=" * 50)
        logger.info("小游探 Zeabur 部署版本启动")
        logger.info("=" * 50)
        
        # 1. 设置环境
        setup_environment()
        
        # 2. 检查依赖
        if not check_dependencies():
            sys.exit(1)
        
        # 3. 启动应用
        asyncio.run(start_application())
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()