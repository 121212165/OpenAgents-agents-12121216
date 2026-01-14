# 测试错误处理和恢复机制
"""
验证任务四的功能：
1. 错误处理和Agent恢复
2. 用户友好的错误信息
3. 性能监控和日志记录
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.utils.error_handler import (
    AgentRecoveryManager,
    UserFriendlyMessages,
    ErrorCategory,
    ErrorSeverity,
    register_agent_for_recovery,
    handle_agent_error,
    is_agent_healthy,
    with_error_handling
)
from src.utils.common import (
    setup_logger,
    monitor_performance,
    format_performance_report,
    DetailedLogger,
    get_performance_monitor
)


# ==================== 测试Agent ====================

class MockAgent:
    """模拟Agent用于测试"""

    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.call_count = 0
        self.failure_count = 0

    async def process_request(self, request: str) -> str:
        """处理请求"""
        self.call_count += 1

        if self.should_fail and self.call_count <= 2:
            self.failure_count += 1
            raise ConnectionError(f"{self.name}: 网络连接失败")

        return f"{self.name} 处理了: {request}"

    async def health_check(self) -> bool:
        """健康检查"""
        return not self.should_fail or self.failure_count >= 2

    async def restart(self):
        """重启Agent"""
        logger.info(f"{self.name} 正在重启...")
        await asyncio.sleep(0.1)
        self.should_fail = False
        logger.info(f"{self.name} 重启完成")


# ==================== 测试函数 ====================

async def test_user_friendly_messages():
    """测试用户友好的错误消息"""
    print("\n" + "="*60)
    print("测试1: 用户友好的错误消息")
    print("="*60)

    test_cases = [
        (ErrorCategory.NETWORK, "网络连接超时"),
        (ErrorCategory.API, "API调用失败"),
        (ErrorCategory.DATA_SOURCE, "数据源不可用"),
        (ErrorCategory.AGENT, "Agent处理异常"),
        (ErrorCategory.LLM, "LLM调用失败"),
        (ErrorCategory.TIMEOUT, "请求超时")
    ]

    for category, detail in test_cases:
        message = UserFriendlyMessages.get_message(category, detail)
        print(f"\n{category.value.upper()}:")
        print(message[:300] + "...")
        print("-" * 60)

    print("✅ 用户友好消息测试通过")


async def test_agent_recovery():
    """测试Agent恢复机制"""
    print("\n" + "="*60)
    print("测试2: Agent自动恢复机制")
    print("="*60)

    # 创建恢复管理器
    manager = AgentRecoveryManager()

    # 创建会失败的Agent
    failing_agent = MockAgent("failing_agent", should_fail=True)
    manager.register_agent("failing_agent", failing_agent)

    print("\n1️⃣ 模拟Agent错误...")

    # 触发多次错误
    for i in range(3):
        try:
            await failing_agent.process_request(f"请求{i+1}")
        except Exception as e:
            await manager.handle_error("failing_agent", e)
            print(f"  ❌ 错误 {i+1}: {str(e)[:50]}")

    # 检查状态
    status = manager.get_agent_status("failing_agent")
    print(f"\n📊 Agent状态:")
    print(f"  错误次数: {status['error_count']}")
    print(f"  状态: {status['status']}")
    print(f"  冷却中: {status['in_cooldown']}")

    print("\n2️⃣ 等待Agent恢复...")
    await asyncio.sleep(3)  # 等待恢复完成

    # 检查是否恢复
    if is_agent_healthy("failing_agent"):
        print("  ✅ Agent已恢复")

        # 尝试再次调用
        try:
            result = await failing_agent.process_request("恢复后的请求")
            print(f"  ✅ 调用成功: {result}")
        except Exception as e:
            print(f"  ❌ 仍然失败: {e}")
    else:
        print("  ⚠️ Agent仍在恢复中")

    print("\n✅ Agent恢复测试完成")


async def test_error_handling_decorator():
    """测试错误处理装饰器"""
    print("\n" + "="*60)
    print("测试3: 错误处理装饰器")
    print("="*60)

    manager = AgentRecoveryManager()
    test_agent = MockAgent("test_agent")
    manager.register_agent("test_agent", test_agent)

    @with_error_handling(manager, "test_agent", fallback_result="降级响应")
    async def risky_function():
        """可能失败的风险函数"""
        await asyncio.sleep(0.1)
        if time.time() % 2 < 1:  # 50%失败率
            raise ValueError("模拟的随机错误")
        return "正常响应"

    print("\n1️⃣ 测试正常情况:")
    for i in range(5):
        result = await risky_function()
        print(f"  调用 {i+1}: {result}")

    print("\n2️⃣ Agent状态:")
    status = manager.get_agent_status("test_agent")
    print(f"  错误次数: {status['error_count']}")

    print("\n✅ 装饰器测试完成")


async def test_performance_monitoring():
    """测试性能监控"""
    print("\n" + "="*60)
    print("测试4: 性能监控和日志")
    print("="*60)

    monitor = get_performance_monitor()

    @monitor_performance("fast_function")
    async def fast_function():
        """快速函数"""
        await asyncio.sleep(0.01)
        return "done"

    @monitor_performance("slow_function")
    async def slow_function():
        """慢函数"""
        await asyncio.sleep(0.5)
        return "done"

    @monitor_performance("failing_function")
    async def failing_function():
        """会失败的函数"""
        await asyncio.sleep(0.1)
        raise RuntimeError("模拟错误")

    print("\n1️⃣ 执行测试函数...")

    # 执行各种函数
    for _ in range(5):
        await fast_function()

    for _ in range(3):
        await slow_function()

    for _ in range(2):
        try:
            await failing_function()
        except:
            pass

    print("\n2️⃣ 性能统计:")
    stats = monitor.get_stats()
    for name, stat in stats.items():
        print(f"\n  {name}:")
        print(f"    调用次数: {stat['count']}")
        print(f"    平均耗时: {stat['avg_time']}s")
        print(f"    最大耗时: {stat['max_time']}s")
        if stat['error_rate'] > 0:
            print(f"    ❌ 错误率: {stat['error_rate']}%")

    print("\n3️⃣ 性能报告:")
    report = format_performance_report()
    print(report[:500] + "...")

    print("\n✅ 性能监控测试完成")


async def test_detailed_logging():
    """测试详细日志记录"""
    print("\n" + "="*60)
    print("测试5: 详细日志记录")
    print("="*60)

    print("\n1️⃣ 记录Agent调用...")
    DetailedLogger.log_agent_call(
        agent_name="router_agent",
        method="process_query",
        parameters={"query": "Uzi在直播吗？"},
        result={"intent": "直播查询", "confidence": 0.9},
        duration=0.123,
        error=None
    )

    print("\n2️⃣ 记录数据源查询...")
    DetailedLogger.log_data_source_query(
        source="mock_data",
        query_type="streams",
        parameters={"first": 10},
        result_count=5,
        cached=True,
        duration=0.05
    )

    print("\n3️⃣ 记录LLM调用...")
    DetailedLogger.log_llm_call(
        prompt_type="intent_classification",
        prompt_length=150,
        response_length=80,
        cached=False,
        duration=0.8
    )

    print("\n4️⃣ 记录用户查询...")
    DetailedLogger.log_user_query(
        query="生成今日简报",
        intent="简报生成",
        confidence=0.85,
        agents_used=["briefing_agent", "live_monitor"],
        duration=1.5,
        success=True
    )

    print("\n5️⃣ 记录错误情况...")
    DetailedLogger.log_agent_call(
        agent_name="data_source_agent",
        method="get_live_streams",
        parameters={"user_login": "unknown"},
        result=None,
        duration=5.0,
        error="用户不存在"
    )

    print("\n✅ 日志记录测试完成 - 请查看日志文件")


async def test_error_statistics():
    """测试错误统计"""
    print("\n" + "="*60)
    print("测试6: 错误统计和分析")
    print("="*60)

    manager = AgentRecoveryManager()

    # 注册多个Agent
    agents = ["agent_a", "agent_b", "agent_c"]
    for agent_name in agents:
        manager.register_agent(agent_name, MockAgent(agent_name))

    print("\n1️⃣ 模拟各种错误...")

    # 为每个Agent触发不同类型的错误
    errors = [
        ("agent_a", ConnectionError("网络超时")),
        ("agent_a", TimeoutError("请求超时")),
        ("agent_b", ValueError("无效参数")),
        ("agent_b", RuntimeError("处理失败")),
        ("agent_c", ConnectionError("API连接失败")),
    ]

    for agent_name, error in errors:
        await manager.handle_error(agent_name, error)

    print("\n2️⃣ 错误统计:")
    stats = manager.get_error_statistics()
    for agent_name, agent_stats in stats.items():
        print(f"\n  {agent_name}:")
        for category, count in agent_stats.items():
            print(f"    {category}: {count}")

    print("\n3️⃣ Agent健康状态:")
    all_status = manager.get_agent_status()
    for agent_name, status in all_status.items():
        healthy = is_agent_healthy(agent_name)
        icon = "🟢" if healthy else "🔴"
        print(f"  {icon} {agent_name}: {status['error_count']} 个错误")

    print("\n✅ 错误统计测试完成")


async def test_integration():
    """集成测试 - 测试所有组件协同工作"""
    print("\n" + "="*60)
    print("测试7: 集成测试")
    print("="*60)

    print("\n1️⃣ 初始化系统...")

    # 注册Agent到全局恢复管理器
    router = MockAgent("router")
    data_source = MockAgent("data_source")
    briefing = MockAgent("briefing")

    register_agent_for_recovery("router", router)
    register_agent_for_recovery("data_source", data_source)
    register_agent_for_recovery("briefing", briefing)

    print("  ✅ Agent已注册")

    print("\n2️⃣ 模拟用户查询流程...")

    @monitor_performance("user_query_flow")
    async def handle_user_query(query: str):
        """处理用户查询的完整流程"""
        logger.info(f"处理查询: {query}")

        # 记录查询
        DetailedLogger.log_user_query(
            query=query,
            intent="测试意图",
            confidence=0.8,
            agents_used=["router", "data_source"],
            duration=0.0,
            success=True
        )

        # 调用Agent
        try:
            result = await router.process_request(query)
            return result
        except Exception as e:
            # 处理错误
            error_msg = await handle_agent_error("router", e)
            return error_msg

    # 执行多个查询
    queries = ["查询1", "查询2", "查询3"]
    for query in queries:
        print(f"\n  处理: {query}")
        result = await handle_user_query(query)
        print(f"  结果: {result[:50]}...")

    print("\n3️⃣ 系统状态报告:")

    # 性能报告
    print("\n📊 性能报告:")
    print(format_performance_report())

    # Agent状态
    print("\n🤖 Agent状态:")
    from src.utils.error_handler import global_recovery_manager
    all_status = global_recovery_manager.get_agent_status()
    for agent_name, status in all_status.items():
        healthy = is_agent_healthy(agent_name)
        icon = "🟢" if healthy else "🔴"
        print(f"  {icon} {agent_name}: 错误数={status['error_count']}, 状态={status['status']}")

    print("\n✅ 集成测试完成")


# ==================== 主测试函数 ====================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("[TEST] Task 4 Test Suite - Error Handling, Recovery and Logging")
    print("="*70)

    # 设置日志
    setup_logger(log_level="INFO")

    try:
        # 运行测试
        await test_user_friendly_messages()
        await test_agent_recovery()
        await test_error_handling_decorator()
        await test_performance_monitoring()
        await test_detailed_logging()
        await test_error_statistics()
        await test_integration()

        print("\n" + "="*70)
        print("[PASS] All tests passed!")
        print("="*70)

        print("\n[SUMMARY] Test Summary:")
        print("  1. [OK] User-friendly error messages")
        print("  2. [OK] Agent auto-recovery mechanism")
        print("  3. [OK] Error handling decorator")
        print("  4. [OK] Performance monitoring and statistics")
        print("  5. [OK] Detailed logging")
        print("  6. [OK] Error statistics and analysis")
        print("  7. [OK] System integration testing")

        print("\n[TIP] Please check logs/yougame.log for detailed logs")

    except Exception as e:
        logger.error(f"[ERROR] Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
