"""
小游探增强版主程序
集成了缓存优化、响应格式化和性能改进
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.utils.common import setup_logger, load_env
from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent

# 导入性能监控
from src.utils.cache_manager import global_cache


class YouGameExplorerEnhanced:
    """小游探增强版 - 性能优化版本"""
    
    def __init__(self):
        setup_logger()
        load_env()
        
        logger.info("="*60)
        logger.info("小游探启动中... (增强版)")
        logger.info("⚡ 性能优化特性:")
        logger.info("   • Agent并发处理")
        logger.info("   • 智能缓存系统")
        logger.info("   • 丰富响应格式")
        logger.info("   • 媒体内容展示")
        logger.info("="*60)
        
        self.agents = {}
    
    async def initialize(self):
        """初始化所有Agent"""
        try:
            logger.info("初始化Agent...")
            
            # 启动缓存管理器
            await global_cache.start()
            logger.info("✅ 缓存管理器已启动")
            
            # 创建Agent实例
            self.agents["data_source"] = DataSourceAgent()
            self.agents["live_monitor"] = LiveMonitorAgent()
            self.agents["briefing_agent"] = BriefingAgent()
            self.agents["router"] = RouterAgent()
            
            # 注册Agent到Router
            for name, agent in self.agents.items():
                if name != "router":
                    self.agents["router"].register_agent(name, agent)
                logger.info(f"✅ {name} Agent已创建")
            
            # 启动所有Agent
            for agent in self.agents.values():
                await agent.on_startup()
            
            logger.info("✅ 所有Agent初始化完成")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    async def start_interactive_mode(self):
        """启动交互模式"""
        print("\n" + "="*60)
        print("小游探 - 游戏圈AI助手 (增强版)")
        print("="*60)
        print("\n你可以问我：")
        print("  • \"Uzi直播了吗？\" - 查询直播状态")
        print("  • \"生成今日简报\" - 获取游戏圈动态")
        print("  • \"热门游戏\" - 查看热门游戏")
        print("  • \"系统状态\" - 查看系统状态")
        print("  • \"性能测试\" - 运行性能测试")
        print("  • \"exit\" - 退出程序")
        print("\n" + "="*60 + "\n")
        
        router = self.agents["router"]
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "退出", "q"]:
                    print("\n👋 再见！")
                    break
                
                if user_input == "性能测试":
                    # 运行性能测试
                    from tests.test_performance import run_performance_tests
                    await run_performance_tests(router)
                    continue
                
                # 处理查询
                result = await router.process(user_input)
                print(f"\n小游探: {result['response']}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                logger.error(f"处理请求失败: {e}")
                print(f"\n小游探: 抱歉，出错了: {str(e)}\n")
    
    async def shutdown(self):
        """关闭系统"""
        logger.info("正在关闭系统...")
        
        # 停止缓存管理器
        await global_cache.stop()
        
        logger.info("✅ 系统已关闭")


async def main():
    """主函数"""
    app = YouGameExplorerEnhanced()
    
    try:
        await app.initialize()
        await app.start_interactive_mode()
    except KeyboardInterrupt:
        print("\n\n程序被中断")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
