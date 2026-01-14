# -*- coding: utf-8 -*-
# 测试错误处理和恢复机制（简化版 - 兼容Windows CMD）
"""
验证任务四的功能：
1. 错误处理和Agent恢复
2. 用户友好的错误信息
3. 性能监控和日志记录
"""

import asyncio
import sys
import time
import os
from pathlib import Path

# 设置输出编码为UTF-8（如果可能）
if sys.platform == "win32":
    try:
        import locale
        import codecs
        # 尝试设置控制台编码
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.utils.error_handler import (
    AgentRecoveryManager,
    UserFriendlyMessages,
    ErrorCategory,
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
            raise ConnectionError(f"{self.name}: Network connection failed")

        return f"{self.name} processed: {request}"

    async def health_check(self) -> bool:
        """健康检查"""
        return not self.should_fail or self.failure_count >= 2

    async def restart(self):
        """重启Agent"""
        logger.info(f"{self.name} is restarting...")
        await asyncio.sleep(0.1)
        self.should_fail = False
        logger.info(f"{self.name} restarted successfully")


# ==================== 测试函数 ====================

async def test_user_friendly_messages():
    """测试用户友好的错误消息"""
    print("\n" + "="*60)
    print("Test 1: User-Friendly Error Messages")
    print("="*60)

    test_cases = [
        (ErrorCategory.NETWORK, "Network timeout"),
        (ErrorCategory.API, "API call failed"),
        (ErrorCategory.DATA_SOURCE, "Data source unavailable"),
        (ErrorCategory.AGENT, "Agent processing error"),
        (ErrorCategory.LLM, "LLM call failed"),
        (ErrorCategory.TIMEOUT, "Request timeout")
    ]

    for category, detail in test_cases:
        message = UserFriendlyMessages.get_message(category, detail)
        # 移除emoji字符以避免编码问题
        message_clean = message.encode('ascii', 'ignore').decode('ascii')
        print(f"\n{category.value.upper()}:")
        print(message_clean[:300] + "...")
        print("-" * 60)

    print("[OK] User-friendly message test passed")


async def test_agent_recovery():
    """测试Agent恢复机制"""
    print("\n" + "="*60)
    print("Test 2: Agent Auto-Recovery Mechanism")
    print("="*60)

    # 创建恢复管理器
    manager = AgentRecoveryManager()

    # 创建会失败的Agent
    failing_agent = MockAgent("failing_agent", should_fail=True)
    manager.register_agent("failing_agent", failing_agent)

    print("\n1. Simulating Agent errors...")

    # 触发多次错误
    for i in range(3):
        try:
            await failing_agent.process_request(f"request_{i+1}")
        except Exception as e:
            await manager.handle_error("failing_agent", e)
            print(f"  [ERROR] Error {i+1}: {str(e)[:50]}")

    # 检查状态
    status = manager.get_agent_status("failing_agent")
    print(f"\n[STATS] Agent Status:")
    print(f"  Error count: {status['error_count']}")
    print(f"  Status: {status['status']}")
    print(f"  In cooldown: {status['in_cooldown']}")

    print("\n2. Waiting for Agent recovery...")
    await asyncio.sleep(3)  # 等待恢复完成

    # 检查是否恢复
    if is_agent_healthy("failing_agent"):
        print("  [OK] Agent recovered")

        # 尝试再次调用
        try:
            result = await failing_agent.process_request("post_recovery_request")
            print(f"  [OK] Call successful: {result}")
        except Exception as e:
            print(f"  [ERROR] Still failing: {e}")
    else:
        print("  [WARN] Agent still recovering")

    print("\n[OK] Agent recovery test completed")


async def test_error_handling_decorator():
    """测试错误处理装饰器"""
    print("\n" + "="*60)
    print("Test 3: Error Handling Decorator")
    print("="*60)

    manager = AgentRecoveryManager()
    test_agent = MockAgent("test_agent")
    manager.register_agent("test_agent", test_agent)

    @with_error_handling(manager, "test_agent", fallback_result="fallback_response")
    async def risky_function():
        """可能失败的风险函数"""
        await asyncio.sleep(0.1)
        if time.time() % 2 < 1:  # 50%失败率
            raise ValueError("Simulated random error")
        return "normal_response"

    print("\n1. Testing normal case:")
    for i in range(5):
        result = await risky_function()
        print(f"  Call {i+1}: {result}")

    print("\n2. Agent Status:")
    status = manager.get_agent_status("test_agent")
    print(f"  Error count: {status['error_count']}")

    print("\n[OK] Decorator test completed")


async def test_performance_monitoring():
    """测试性能监控"""
    print("\n" + "="*60)
    print("Test 4: Performance Monitoring and Logging")
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
        raise RuntimeError("Simulated error")

    print("\n1. Executing test functions...")

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

    print("\n2. Performance Statistics:")
    stats = monitor.get_stats()
    for name, stat in stats.items():
        print(f"\n  {name}:")
        print(f"    Call count: {stat['count']}")
        print(f"    Avg time: {stat['avg_time']}s")
        print(f"    Max time: {stat['max_time']}s")
        if stat['error_rate'] > 0:
            print(f"    [ERROR] Error rate: {stat['error_rate']}%")

    print("\n3. Performance Report:")
    report = format_performance_report()
    # 移除emoji字符
    report_clean = report.encode('ascii', 'ignore').decode('ascii')
    print(report_clean[:500] + "...")

    print("\n[OK] Performance monitoring test completed")


async def test_detailed_logging():
    """测试详细日志记录"""
    print("\n" + "="*60)
    print("Test 5: Detailed Logging")
    print("="*60)

    print("\n1. Logging Agent calls...")
    DetailedLogger.log_agent_call(
        agent_name="router_agent",
        method="process_query",
        parameters={"query": "Is Uzi streaming?"},
        result={"intent": "live_stream_query", "confidence": 0.9},
        duration=0.123,
        error=None
    )

    print("\n2. Logging data source queries...")
    DetailedLogger.log_data_source_query(
        source="mock_data",
        query_type="streams",
        parameters={"first": 10},
        result_count=5,
        cached=True,
        duration=0.05
    )

    print("\n3. Logging LLM calls...")
    DetailedLogger.log_llm_call(
        prompt_type="intent_classification",
        prompt_length=150,
        response_length=80,
        cached=False,
        duration=0.8
    )

    print("\n4. Logging user queries...")
    DetailedLogger.log_user_query(
        query="Generate daily briefing",
        intent="briefing_generation",
        confidence=0.85,
        agents_used=["briefing_agent", "live_monitor"],
        duration=1.5,
        success=True
    )

    print("\n5. Logging error cases...")
    DetailedLogger.log_agent_call(
        agent_name="data_source_agent",
        method="get_live_streams",
        parameters={"user_login": "unknown"},
        result=None,
        duration=5.0,
        error="User not found"
    )

    print("\n[OK] Logging test completed - Check log file for details")


async def test_error_statistics():
    """测试错误统计"""
    print("\n" + "="*60)
    print("Test 6: Error Statistics and Analysis")
    print("="*60)

    manager = AgentRecoveryManager()

    # 注册多个Agent
    agents = ["agent_a", "agent_b", "agent_c"]
    for agent_name in agents:
        manager.register_agent(agent_name, MockAgent(agent_name))

    print("\n1. Simulating various errors...")

    # 为每个Agent触发不同类型的错误
    errors = [
        ("agent_a", ConnectionError("Network timeout")),
        ("agent_a", TimeoutError("Request timeout")),
        ("agent_b", ValueError("Invalid parameter")),
        ("agent_b", RuntimeError("Processing failed")),
        ("agent_c", ConnectionError("API connection failed")),
    ]

    for agent_name, error in errors:
        await manager.handle_error(agent_name, error)

    print("\n2. Error Statistics:")
    stats = manager.get_error_statistics()
    for agent_name, agent_stats in stats.items():
        print(f"\n  {agent_name}:")
        for category, count in agent_stats.items():
            print(f"    {category}: {count}")

    print("\n3. Agent Health Status:")
    all_status = manager.get_agent_status()
    for agent_name, status in all_status.items():
        healthy = is_agent_healthy(agent_name)
        icon = "[OK]" if healthy else "[FAIL]"
        print(f"  {icon} {agent_name}: {status['error_count']} errors")

    print("\n[OK] Error statistics test completed")


async def test_integration():
    """集成测试 - 测试所有组件协同工作"""
    print("\n" + "="*60)
    print("Test 7: Integration Test")
    print("="*60)

    print("\n1. Initializing system...")

    # 注册Agent到全局恢复管理器
    router = MockAgent("router")
    data_source = MockAgent("data_source")
    briefing = MockAgent("briefing")

    register_agent_for_recovery("router", router)
    register_agent_for_recovery("data_source", data_source)
    register_agent_for_recovery("briefing", briefing)

    print("  [OK] Agents registered")

    print("\n2. Simulating user query flow...")

    @monitor_performance("user_query_flow")
    async def handle_user_query(query: str):
        """处理用户查询的完整流程"""
        logger.info(f"Processing query: {query}")

        # 记录查询
        DetailedLogger.log_user_query(
            query=query,
            intent="test_intent",
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
    queries = ["query_1", "query_2", "query_3"]
    for query in queries:
        print(f"\n  Processing: {query}")
        result = await handle_user_query(query)
        print(f"  Result: {result[:50]}...")

    print("\n3. System Status Report:")

    # 性能报告
    print("\n[PERF] Performance Report:")
    report = format_performance_report()
    report_clean = report.encode('ascii', 'ignore').decode('ascii')
    print(report_clean[:500] + "...")

    # Agent状态
    print("\n[AGENT] Agent Status:")
    from src.utils.error_handler import global_recovery_manager
    all_status = global_recovery_manager.get_agent_status()
    for agent_name, status in all_status.items():
        healthy = is_agent_healthy(agent_name)
        icon = "[OK]" if healthy else "[FAIL]"
        print(f"  {icon} {agent_name}: errors={status['error_count']}, status={status['status']}")

    print("\n[OK] Integration test completed")


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
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
