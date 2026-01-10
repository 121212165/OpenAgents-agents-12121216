# 小游探 - 主启动文件
"""
小游探（YouGame Explorer）
为游戏圈粉丝打造的 AI 吃瓜助手

启动方式：
    python src/main.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.utils.common import setup_logger, load_env
from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent


class YouGameExplorer:
    """小游探主应用"""

    def __init__(self):
        # 设置日志
        setup_logger()

        # 加载环境变量
        load_env()

        logger.info("="*50)
        logger.info("小游探启动中...")
        logger.info("="*50)

        # 初始化 Agent
        self.router = None
        self.live_monitor = None
        self.briefing_agent = None

    async def initialize(self):
        """初始化所有 Agent"""
        try:
            logger.info("初始化 Agent...")

            # 1. 创建 LiveMonitor Agent
            self.live_monitor = LiveMonitorAgent()
            logger.info("✅ LiveMonitor Agent 就绪")

            # 2. 创建 BriefingAgent
            self.briefing_agent = BriefingAgent(live_monitor=self.live_monitor)
            logger.info("✅ BriefingAgent 就绪")

            # 3. 创建 Router Agent（注入依赖）
            self.router = RouterAgent()
            self.router.live_monitor = self.live_monitor
            self.router.briefing_agent = self.briefing_agent
            logger.info("✅ Router Agent 就绪")

            logger.info("所有 Agent 初始化完成！")

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    async def start_interactive_mode(self):
        """启动交互模式"""
        print("\n" + "="*50)
        print("小游探 - 游戏圈 AI 助手")
        print("="*50)
        print("\n你可以问我：")
        print("  * \"Uzi 直播了吗？\" - 查询直播状态")
        print("  * \"生成今日简报\" - 获取游戏圈动态")
        print("  * \"exit\" - 退出程序")
        print("\n" + "="*50 + "\n")

        while True:
            try:
                # 获取用户输入
                user_input = input("你: ").strip()

                if not user_input:
                    continue

                # 退出命令
                if user_input.lower() in ["exit", "quit", "退出", "q"]:
                    print("\n再见！")
                    break

                # 处理查询
                result = await self.router.process(user_input)

                print(f"\n小游探: {result['response']}\n")

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                logger.error(f"处理请求失败: {e}")
                print(f"\n小游探: 抱歉，出错了: {str(e)}\n")

    async def run_demo_queries(self):
        """运行演示查询"""
        print("\n运行演示查询...\n")

        demo_queries = [
            "你好",
            "Uzi 直播了吗",
            "生成今日简报"
        ]

        for query in demo_queries:
            print(f"用户: {query}")
            result = await self.router.process(query)
            print(f"小游探: {result['response']}\n")
            await asyncio.sleep(1)

    async def start_background_monitoring(self):
        """启动后台监控任务"""
        logger.info("启动后台监控...")

        # 创建监控任务
        monitor_task = asyncio.create_task(self.live_monitor.monitor_all_players())

        return monitor_task


async def main():
    """主函数"""
    app = YouGameExplorer()

    try:
        # 初始化
        await app.initialize()

        # 启动交互模式
        await app.start_interactive_mode()

    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)


def run():
    """同步入口"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
