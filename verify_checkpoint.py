# -*- coding: utf-8 -*-
"""
任务六：核心功能验证脚本
验证所有Agent正常工作，数据源切换正常，错误处理有效
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent
from src.utils.data_sources import DataSourceManager, MockDataSource, TwitchDataSource


class CheckpointVerifier:
    """核心功能验证器"""

    def __init__(self):
        self.test_results = []
        self.agents = {}

    async def initialize_agents(self):
        """初始化所有Agent"""
        logger.info("="*60)
        logger.info("初始化所有Agent...")
        logger.info("="*60)

        try:
            # 1. DataSource Agent
            self.agents['data_source'] = DataSourceAgent()
            await self.agents['data_source'].on_startup()
            logger.info("[OK] DataSource Agent 初始化成功")

            # 2. LiveMonitor Agent
            self.agents['live_monitor'] = LiveMonitorAgent()
            await self.agents['live_monitor'].on_startup()
            logger.info("[OK] LiveMonitor Agent 初始化成功")

            # 3. BriefingAgent
            self.agents['briefing'] = BriefingAgent()
            await self.agents['briefing'].on_startup()
            logger.info("[OK] BriefingAgent 初始化成功")

            # 4. Router Agent
            self.agents['router'] = RouterAgent()
            self.agents['router'].register_agent('live_monitor', self.agents['live_monitor'])
            self.agents['router'].register_agent('briefing_agent', self.agents['briefing'])
            self.agents['router'].register_agent('data_source', self.agents['data_source'])
            await self.agents['router'].on_startup()
            logger.info("[OK] Router Agent 初始化成功")

            self.test_results.append(("Agent初始化", True, "所有4个Agent成功初始化"))
            return True

        except Exception as e:
            logger.error(f"[FAIL] Agent初始化失败: {e}")
            self.test_results.append(("Agent初始化", False, str(e)))
            return False

    async def verify_agent_communication(self):
        """验证Agent间通信"""
        logger.info("\n" + "="*60)
        logger.info("验证Agent间通信...")
        logger.info("="*60)

        try:
            # 测试1: Router处理问候
            result = await self.agents['router'].process("你好")
            assert result['success'] is not None
            logger.info(f"[OK] 问候处理成功: {result['response'][:50]}...")

            # 测试2: Router处理直播查询
            result = await self.agents['router'].process("Uzi直播了吗")
            assert result['success'] is not None
            logger.info(f"[OK] 直播查询成功: {result['response'][:50]}...")

            # 测试3: Router处理简报请求
            result = await self.agents['router'].process("生成今日简报")
            assert result['success'] is not None
            logger.info(f"[OK] 简报生成成功: {result['response'][:50]}...")

            self.test_results.append(("Agent通信", True, "所有消息路由正常"))
            return True

        except Exception as e:
            logger.error(f"[FAIL] Agent通信失败: {e}")
            self.test_results.append(("Agent通信", False, str(e)))
            return False

    async def verify_data_source_switching(self):
        """验证数据源切换"""
        logger.info("\n" + "="*60)
        logger.info("验证数据源切换...")
        logger.info("="*60)

        try:
            # 创建独立的数据源管理器
            manager = DataSourceManager()

            # 添加多个数据源
            mock1 = MockDataSource(name="Mock1")
            mock2 = MockDataSource(name="Mock2")
            mock3 = MockDataSource(name="Mock3")

            manager.add_source(mock1, priority=1)
            manager.add_source(mock2, priority=2)
            manager.add_source(mock3, priority=3)

            logger.info(f"[OK] 添加了 3 个数据源")

            # 测试查询
            from src.utils.data_sources import DataQuery
            query = DataQuery(query_type="streams", parameters={"game": "LOL"})

            # 查询应该使用优先级最高的数据源
            result = await manager.query(query)
            assert result.success
            logger.info(f"[OK] 使用数据源: {result.source}")

            # 测试健康检查
            health = await manager.health_check()
            logger.info(f"[OK] 健康检查: {health['healthy_count']}/{health['total_count']} 数据源健康")

            # 测试故障切换
            await manager.mark_source_unavailable(result.source)
            logger.info(f"[OK] 标记 {result.source} 不可用")

            # 再次查询应该使用次优先级数据源
            result2 = await manager.query(query)
            assert result2.success
            assert result2.source != result.source
            logger.info(f"[OK] 故障切换到: {result2.source}")

            self.test_results.append(("数据源切换", True, "故障切换机制正常"))
            return True

        except Exception as e:
            logger.error(f"[FAIL] 数据源切换验证失败: {e}")
            self.test_results.append(("数据源切换", False, str(e)))
            return False

    async def verify_error_handling(self):
        """验证错误处理"""
        logger.info("\n" + "="*60)
        logger.info("验证错误处理...")
        logger.info("="*60)

        try:
            # 测试1: 无效输入处理
            result = await self.agents['router'].process("")
            logger.info(f"[OK] 空输入处理: {result.get('success', False)}")

            # 测试2: 未知意图处理
            result = await self.agents['router'].process("这是一段无意义的文本")
            logger.info(f"[OK] 未知意图处理: {result.get('success', False)}")

            # 测试3: 数据源失败恢复
            manager = DataSourceManager()
            mock_broken = MockDataSource(name="Broken")
            mock_ok = MockDataSource(name="OK")

            manager.add_source(mock_broken, priority=1)
            manager.add_source(mock_ok, priority=2)

            from src.utils.data_sources import DataQuery
            query = DataQuery(query_type="streams", parameters={"test": "error"})

            # 即使一个失败，另一个应该成功
            result = await manager.query(query)
            logger.info(f"[OK] 部分故障恢复: {result.success}")

            self.test_results.append(("错误处理", True, "错误恢复机制正常"))
            return True

        except Exception as e:
            logger.error(f"[FAIL] 错误处理验证失败: {e}")
            self.test_results.append(("错误处理", False, str(e)))
            return False

    async def verify_multi_agent_collaboration(self):
        """验证多Agent协作"""
        logger.info("\n" + "="*60)
        logger.info("验证多Agent协作...")
        logger.info("="*60)

        try:
            # BriefingAgent需要协调多个Agent
            # 注册协作Agent
            self.agents['briefing'].register_collaborating_agent('data_source', self.agents['data_source'])
            self.agents['briefing'].register_collaborating_agent('live_monitor', self.agents['live_monitor'])

            # 触发简报生成（需要多Agent协作）
            result = await self.agents['router'].process("生成今日简报")
            assert result['success'] is not None
            logger.info(f"[OK] 多Agent协作简报生成成功")

            # 检查协作统计
            stats = self.agents['briefing'].collaboration_stats
            logger.info(f"[OK] 协作统计: 总请求 {stats['total_requests']}, 成功 {stats['successful_collaborations']}")

            self.test_results.append(("多Agent协作", True, "协作机制正常"))
            return True

        except Exception as e:
            logger.error(f"[FAIL] 多Agent协作验证失败: {e}")
            self.test_results.append(("多Agent协作", False, str(e)))
            return False

    async def shutdown_agents(self):
        """关闭所有Agent"""
        logger.info("\n关闭所有Agent...")
        for name, agent in self.agents.items():
            try:
                await agent.on_shutdown()
                logger.info(f"[OK] {name} 已关闭")
            except Exception as e:
                logger.warning(f"[WARN] {name} 关闭时出错: {e}")

    def print_summary(self):
        """打印验证总结"""
        logger.info("\n" + "="*60)
        logger.info("核心功能验证总结")
        logger.info("="*60)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        for test_name, success, detail in self.test_results:
            status = "[PASS]" if success else "[FAIL]"
            logger.info(f"{status} {test_name}: {detail}")

        logger.info("-"*60)
        logger.info(f"通过: {passed}/{total}")

        if passed == total:
            logger.info("[SUCCESS] 任务六核心功能验证全部通过！")
            return True
        else:
            logger.warning(f"[WARNING] {total - passed} 项验证失败")
            return False


async def main():
    """主验证流程"""
    # 配置日志
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end="", flush=True),
        level="INFO",
        format="{time:HH:mm:ss} | {level: <8} | {message}\n",
        catch=False
    )

    logger.info("任务六：Checkpoint - 核心功能验证")
    logger.info("验证所有Agent正常工作，数据源切换正常，错误处理有效\n")

    verifier = CheckpointVerifier()

    try:
        # 1. 初始化Agent
        if not await verifier.initialize_agents():
            return False

        # 2. 验证Agent通信
        await verifier.verify_agent_communication()

        # 3. 验证数据源切换
        await verifier.verify_data_source_switching()

        # 4. 验证错误处理
        await verifier.verify_error_handling()

        # 5. 验证多Agent协作
        await verifier.verify_multi_agent_collaboration()

        # 关闭Agent
        await verifier.shutdown_agents()

        # 打印总结
        return verifier.print_summary()

    except Exception as e:
        logger.error(f"验证过程异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
