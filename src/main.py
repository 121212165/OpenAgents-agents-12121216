# 小游探 - 主启动文件（OpenAgents版本）
"""
小游探（YouGame Explorer）- OpenAgents 标准版本
为游戏圈粉丝打造的 AI 吃瓜助手

启动方式：
    python src/main.py
"""

import asyncio
import sys
from pathlib import Path
import os

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.utils.common import setup_logger, load_env
from src.utils.performance_metrics import get_performance_tracker, format_performance_report
from src.utils.resource_optimizer import get_resource_optimizer
from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent
from src.utils.error_handler import global_recovery_manager
from src.utils.server_config import get_server_config

# 动态导入aiohttp（处理云端部署问题）
try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    logger.warning("aiohttp不可用，健康检查功能将被禁用")
    AIOHTTP_AVAILABLE = False


class YouGameExplorer:
    """小游探主应用 - OpenAgents 版本"""

    def __init__(self):
        # 设置日志
        setup_logger()

        # 加载环境变量
        load_env()

        logger.info("="*50)
        logger.info("小游探启动中... (OpenAgents版本)")
        logger.info("="*50)

        # 初始化 Agent
        self.router = None
        self.live_monitor = None
        self.briefing_agent = None
        self.data_source_agent = None

    async def initialize(self):
        """初始化所有 Agent"""
        try:
            logger.info("初始化 OpenAgents Agent...")

            # 启动资源优化器监控
            resource_optimizer = get_resource_optimizer()
            await resource_optimizer.start_monitoring()
            logger.info("✅ 资源优化器已启动")

            # 1. 创建 DataSource Agent
            self.data_source_agent = DataSourceAgent()
            logger.info("✅ DataSource Agent 就绪")

            # 2. 创建 LiveMonitor Agent
            self.live_monitor = LiveMonitorAgent()
            logger.info("✅ LiveMonitor Agent 就绪")

            # 3. 创建 BriefingAgent
            self.briefing_agent = BriefingAgent()
            logger.info("✅ BriefingAgent 就绪")

            # 4. 创建 Router Agent（使用新的注册机制）
            self.router = RouterAgent()
            
            # 注册其他Agent到Router
            self.router.register_agent("live_monitor", self.live_monitor)
            self.router.register_agent("briefing_agent", self.briefing_agent)
            self.router.register_agent("data_source", self.data_source_agent)
            
            logger.info("✅ Router Agent 就绪")

            # 5. 启动所有 Agent
            await self.data_source_agent.on_startup()
            await self.live_monitor.on_startup()
            await self.briefing_agent.on_startup()
            await self.router.on_startup()

            logger.info("所有 OpenAgents Agent 初始化完成！")

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    async def start_interactive_mode(self):
        """启动交互模式"""
        print("\n" + "="*50)
        print("小游探 - 游戏圈 AI 助手 (OpenAgents版本)")
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

    async def start_openagents_mode(self):
        """启动OpenAgents模式（等待外部连接）"""
        logger.info("OpenAgents模式启动...")
        logger.info("等待OpenAgents Studio连接...")
        
        # 获取配置（使用新的配置模块）
        host, port = get_server_config()
        
        if AIOHTTP_AVAILABLE:
            # 创建健康检查服务器
            app = web.Application()
            app.router.add_get('/health', self.health_check)
            app.router.add_get('/metrics', self.metrics_endpoint)
            app.router.add_get('/performance', self.performance_report_endpoint)
            
            # 启动HTTP服务器
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()
            
            logger.info(f"健康检查服务器启动在 http://{host}:{port}")
            logger.info(f"  - 健康检查: http://{host}:{port}/health")
            logger.info(f"  - Prometheus指标: http://{host}:{port}/metrics")
            logger.info(f"  - 性能报告: http://{host}:{port}/performance")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号，准备关闭...")
            finally:
                await runner.cleanup()
        else:
            # 简化模式，不启动HTTP服务器
            logger.info(f"简化模式启动在端口 {port}")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号，准备关闭...")

    async def health_check(self, request):
        """健康检查端点"""
        try:
            # 检查所有Agent状态
            status = {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "agents": {
                    "router": self.router is not None,
                    "live_monitor": self.live_monitor is not None,
                    "briefing_agent": self.briefing_agent is not None,
                    "data_source_agent": self.data_source_agent is not None
                }
            }
            if AIOHTTP_AVAILABLE:
                return web.json_response(status)
            else:
                return status
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            if AIOHTTP_AVAILABLE:
                return web.json_response(
                    {"status": "unhealthy", "error": str(e)}, 
                    status=500
                )
            else:
                return {"status": "unhealthy", "error": str(e)}
    
    async def metrics_endpoint(self, request):
        """Prometheus指标端点"""
        try:
            tracker = get_performance_tracker()
            metrics = tracker.get_prometheus_metrics()
            
            if AIOHTTP_AVAILABLE:
                return web.Response(
                    body=metrics,
                    content_type='text/plain; version=0.0.4'
                )
            else:
                return metrics
        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            if AIOHTTP_AVAILABLE:
                return web.Response(
                    text=f"Error: {str(e)}",
                    status=500
                )
            else:
                return b""
    
    async def performance_report_endpoint(self, request):
        """性能报告端点"""
        try:
            tracker = get_performance_tracker()
            
            # 获取查询参数
            detailed = request.rel_url.query.get('detailed', 'false').lower() == 'true'
            format_type = request.rel_url.query.get('format', 'text')
            
            if format_type == 'json':
                # JSON格式
                summary = tracker.get_performance_summary()
                stats = tracker.get_stats()
                slow_queries = tracker.get_slow_queries(limit=10)
                
                report_data = {
                    "summary": summary,
                    "stats": stats if detailed else {},
                    "slow_queries": slow_queries
                }
                
                if AIOHTTP_AVAILABLE:
                    return web.json_response(report_data)
                else:
                    return report_data
            else:
                # 文本格式
                report = format_performance_report(detailed=detailed)
                
                if AIOHTTP_AVAILABLE:
                    return web.Response(text=report, content_type='text/plain')
                else:
                    return report
                    
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            if AIOHTTP_AVAILABLE:
                return web.Response(
                    text=f"Error: {str(e)}",
                    status=500
                )
            else:
                return f"Error: {str(e)}"

    async def shutdown(self):
        """关闭所有Agent"""
        logger.info("关闭所有Agent...")

        # 输出性能报告
        logger.info("\n" + "="*60)
        logger.info("性能监控报告")
        logger.info("="*60)
        logger.info(format_performance_report())

        # 输出资源统计
        logger.info("\n" + "="*60)
        logger.info("资源使用报告")
        logger.info("="*60)
        resource_optimizer = get_resource_optimizer()
        resource_stats = resource_optimizer.get_all_stats()
        import json
        logger.info(json.dumps(resource_stats, indent=2, ensure_ascii=False))

        # 输出Agent状态
        logger.info("\n" + "="*60)
        logger.info("Agent状态报告")
        logger.info("="*60)
        agent_status = global_recovery_manager.get_agent_status()
        for agent_name, status in agent_status.items():
            logger.info(f"{agent_name}: errors={status['error_count']}, status={status['status']}")

        logger.info("\n" + "="*60)

        try:
            # 停止资源监控
            resource_optimizer.stop_monitoring()
            
            if self.router:
                await self.router.on_shutdown()
            if self.briefing_agent:
                await self.briefing_agent.on_shutdown()
            if self.live_monitor:
                await self.live_monitor.on_shutdown()
            if self.data_source_agent:
                await self.data_source_agent.on_shutdown()

            logger.info("所有Agent已关闭")
        except Exception as e:
            logger.error(f"关闭Agent时出错: {e}")


async def main():
    """主函数"""
    app = YouGameExplorer()

    try:
        # 初始化
        await app.initialize()

        # 检查启动模式
        if len(sys.argv) > 1 and sys.argv[1] == "--openagents":
            # OpenAgents模式
            await app.start_openagents_mode()
        elif len(sys.argv) > 1 and sys.argv[1] == "--demo":
            # 演示模式
            await app.run_demo_queries()
        else:
            # 交互模式
            await app.start_interactive_mode()

    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
    finally:
        # 确保清理资源
        await app.shutdown()


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
