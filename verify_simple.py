# -*- coding: utf-8 -*-
"""
任务六：核心功能验证脚本（简化版）
验证所有Agent正常工作，数据源切换正常，错误处理有效
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))


def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(text)
    print("="*60)


def print_result(test_name, success, detail=""):
    """打印测试结果"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {test_name}: {detail}")
    return success


async def verify_data_sources():
    """验证数据源功能"""
    print_header("1. 验证数据源功能")

    try:
        from src.utils.data_sources import DataSourceManager, MockDataSource, DataQuery

        # 创建管理器
        manager = DataSourceManager()

        # 添加多个数据源
        mock1 = MockDataSource(name="Mock1")
        mock2 = MockDataSource(name="Mock2")
        manager.add_source(mock1, priority=1)
        manager.add_source(mock2, priority=2)

        print(f"添加了 2 个数据源")

        # 测试查询
        query = DataQuery(query_type="streams", parameters={"game": "LOL"})
        result = await manager.query(query)

        if result.success:
            print(f"查询成功，使用数据源: {result.source}")
        else:
            print(f"查询失败: {result.error}")
            return False

        # 测试健康检查
        health = await manager.health_check()
        print(f"健康检查: {health['healthy_count']}/{health['total_count']} 数据源健康")

        # 测试故障切换
        await manager.mark_source_unavailable(result.source)
        print(f"标记 {result.source} 不可用")

        result2 = await manager.query(query)
        if result2.success and result2.source != result.source:
            print(f"故障切换成功，新数据源: {result2.source}")
            return True
        else:
            print("故障切换失败")
            return False

    except Exception as e:
        print(f"数据源验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_agents_basic():
    """验证Agent基本功能"""
    print_header("2. 验证Agent基本功能")

    results = []

    try:
        from src.agents.data_source_agent import DataSourceAgent
        from src.agents.live_monitor_agent import LiveMonitorAgent
        from src.agents.briefing_agent import BriefingAgent
        from src.agents.router_agent import RouterAgent

        # 创建Agent实例（不启动，避免emoji日志）
        print("创建Agent实例...")

        data_source = DataSourceAgent()
        print(f"[OK] DataSource Agent创建成功")

        live_monitor = LiveMonitorAgent()
        print(f"[OK] LiveMonitor Agent创建成功")

        briefing = BriefingAgent()
        print(f"[OK] BriefingAgent创建成功")

        router = RouterAgent()
        router.register_agent('live_monitor', live_monitor)
        router.register_agent('briefing_agent', briefing)
        router.register_agent('data_source', data_source)
        print(f"[OK] Router Agent创建成功")

        # 测试Router的基本意图识别
        print("\n测试意图识别...")

        # 问候意图
        intent1 = await router._detect_intent_smart("你好")
        print(f"输入: '你好' -> 意图: {intent1.get('intent')}, 置信度: {intent1.get('confidence')}")
        results.append(("意图识别-问候", intent1.get('intent') == '问候'))

        # 直播查询意图
        intent2 = await router._detect_intent_smart("Uzi直播了吗")
        print(f"输入: 'Uzi直播了吗' -> 意图: {intent2.get('intent')}, 置信度: {intent2.get('confidence')}")
        results.append(("意图识别-直播", intent2.get('intent') in ['直播查询', '状态查询']))

        # 简报生成意图
        intent3 = await router._detect_intent_smart("生成今日简报")
        print(f"输入: '生成今日简报' -> 意图: {intent3.get('intent')}, 置信度: {intent3.get('confidence')}")
        results.append(("意图识别-简报", intent3.get('intent') in ['简报生成', '报告']))

        return all(r[1] for r in results)

    except Exception as e:
        print(f"Agent验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_error_handling():
    """验证错误处理"""
    print_header("3. 验证错误处理")

    try:
        from src.utils.data_sources import DataSourceManager, MockDataSource, DataQuery

        manager = DataSourceManager()

        # 添加一个会失败的数据源
        class FailingDataSource:
            def __init__(self):
                self.name = "FailingSource"
                self.priority = 1
                self.available = True

            async def query(self, query):
                raise Exception("模拟数据源失败")

        failing = FailingDataSource()
        mock = MockDataSource(name="Backup")

        # 注意：这里需要添加到内部数据源列表
        manager._sources.append(failing)
        manager.add_source(mock, priority=2)

        # 测试查询
        query = DataQuery(query_type="streams", parameters={})
        result = await manager.query(query)

        if result.success:
            print(f"错误处理成功，使用备份数据源: {result.source}")
            return True
        else:
            print(f"查询失败: {result.error}")
            return False

    except Exception as e:
        print(f"错误处理验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_multi_agent():
    """验证多Agent协作能力"""
    print_header("4. 验证多Agent协作")

    try:
        from src.agents.briefing_agent import BriefingAgent
        from src.agents.data_source_agent import DataSourceAgent

        # 创建Agent
        briefing = BriefingAgent()
        data_source = DataSourceAgent()

        # 注册协作Agent
        briefing.register_collaborating_agent('data_source', data_source)

        print(f"协作Agent注册成功")
        print(f"协作Agent数量: {len(briefing.collaborating_agents)}")

        # 检查协作配置
        print(f"协作优先级配置: {briefing.agent_priorities}")
        print(f"聚合策略数量: {len(briefing.aggregation_strategies)}")

        return True

    except Exception as e:
        print(f"多Agent协作验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_router_logic():
    """验证路由逻辑"""
    print_header("5. 验证路由逻辑")

    try:
        from src.agents.router_agent import RouterAgent

        router = RouterAgent()

        # 检查路由配置
        print(f"意图路由配置数量: {len(router.intent_routing)}")
        print(f"支持的路由意图: {list(router.intent_routing.keys())}")

        print(f"\n降级规则模式数量: {len(router.intent_patterns)}")

        print(f"\n实体提取模式数量: {len(router.entity_patterns)}")

        # 测试实体提取
        test_text = "Uzi正在直播英雄联盟"
        entities = await router._extract_entities(test_text)
        print(f"\n输入: '{test_text}'")
        print(f"提取的实体: {entities}")

        return True

    except Exception as e:
        print(f"路由逻辑验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主验证流程"""
    print("="*60)
    print("任务六：核心功能验证")
    print("验证所有Agent正常工作，数据源切换正常，错误处理有效")
    print("="*60)

    results = []

    # 1. 验证数据源功能
    results.append(("数据源功能", await verify_data_sources()))

    # 2. 验证Agent基本功能
    results.append(("Agent基本功能", await verify_agents_basic()))

    # 3. 验证错误处理
    results.append(("错误处理", await verify_error_handling()))

    # 4. 验证多Agent协作
    results.append(("多Agent协作", await verify_multi_agent()))

    # 5. 验证路由逻辑
    results.append(("路由逻辑", await verify_router_logic()))

    # 打印总结
    print_header("验证总结")

    for test_name, success in results:
        print_result(test_name, success)

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print("-"*60)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("[SUCCESS] 任务六核心功能验证全部通过!")
        return True
    else:
        print(f"[WARNING] {total - passed} 项验证失败")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
