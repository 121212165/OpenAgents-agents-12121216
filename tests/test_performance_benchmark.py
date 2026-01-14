# 性能基准测试
"""
性能基准测试 - 验证系统响应时间要求

测试目标：
1. 验证响应时间 < 3秒（需求4.2）
2. 建立性能基线
3. 检测性能回归
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime

# 导入系统组件
from src.agents.router_agent import RouterAgent, QueryContext
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent
from src.utils.performance_metrics import get_performance_tracker, format_performance_report


class TestPerformanceBenchmark:
    """性能基准测试套件"""
    
    @pytest.fixture
    async def setup_agents(self):
        """设置测试Agent"""
        # 创建Agent实例
        data_source_agent = DataSourceAgent()
        live_monitor = LiveMonitorAgent()
        briefing_agent = BriefingAgent()
        router = RouterAgent()
        
        # 注册Agent
        router.register_agent("live_monitor", live_monitor)
        router.register_agent("briefing_agent", briefing_agent)
        router.register_agent("data_source", data_source_agent)
        
        # 启动Agent
        await data_source_agent.on_startup()
        await live_monitor.on_startup()
        await briefing_agent.on_startup()
        await router.on_startup()
        
        yield router
        
        # 清理
        await router.on_shutdown()
        await briefing_agent.on_shutdown()
        await live_monitor.on_shutdown()
        await data_source_agent.on_startup()
    
    @pytest.mark.asyncio
    async def test_response_time_requirement(self, setup_agents):
        """
        Property 5: Performance Response Time
        Validates: Requirements 4.2
        
        测试：所有查询应在3秒内响应
        """
        router = setup_agents
        
        # 测试查询列表
        test_queries = [
            "你好",
            "Faker在直播吗？",
            "Uzi在直播吗？",
            "生成今日简报",
            "系统状态"
        ]
        
        max_response_time = 3.0  # 3秒要求
        results = []
        
        for query in test_queries:
            context = QueryContext(
                user_id="test_user",
                session_id=f"test_{datetime.now().timestamp()}",
                timestamp=datetime.now()
            )
            
            start_time = time.time()
            result = await router.smart_process(query, context)
            duration = time.time() - start_time
            
            results.append({
                "query": query,
                "duration": duration,
                "success": result.get("success", False),
                "from_cache": result.get("from_cache", False)
            })
            
            # 验证响应时间
            assert duration < max_response_time, \
                f"查询 '{query}' 响应时间 {duration:.2f}s 超过 {max_response_time}s"
            
            print(f"✓ {query}: {duration:.2f}s {'(缓存)' if result.get('from_cache') else ''}")
        
        # 打印统计
        avg_time = sum(r["duration"] for r in results) / len(results)
        max_time = max(r["duration"] for r in results)
        min_time = min(r["duration"] for r in results)
        
        print(f"\n性能统计:")
        print(f"  平均响应时间: {avg_time:.2f}s")
        print(f"  最大响应时间: {max_time:.2f}s")
        print(f"  最小响应时间: {min_time:.2f}s")
        print(f"  测试查询数: {len(results)}")
        
        # 所有查询都应成功
        assert all(r["success"] for r in results), "部分查询失败"
    
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, setup_agents):
        """
        测试：缓存应显著提升响应速度
        """
        router = setup_agents
        
        query = "Faker在直播吗？"
        context = QueryContext(
            user_id="test_user",
            session_id=f"test_{datetime.now().timestamp()}",
            timestamp=datetime.now()
        )
        
        # 第一次查询（无缓存）
        start_time = time.time()
        result1 = await router.smart_process(query, context)
        first_duration = time.time() - start_time
        
        # 第二次查询（有缓存）
        start_time = time.time()
        result2 = await router.smart_process(query, context)
        cached_duration = time.time() - start_time
        
        print(f"\n缓存性能测试:")
        print(f"  首次查询: {first_duration:.3f}s")
        print(f"  缓存查询: {cached_duration:.3f}s")
        print(f"  性能提升: {(first_duration / cached_duration):.1f}x")
        
        # 缓存查询应该更快
        assert cached_duration < first_duration, "缓存查询应该更快"
        assert result2.get("from_cache") == True, "第二次查询应该来自缓存"
        
        # 缓存查询应该非常快（< 0.1秒）
        assert cached_duration < 0.1, f"缓存查询过慢: {cached_duration:.3f}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, setup_agents):
        """
        测试：并发请求性能
        """
        router = setup_agents
        
        # 创建多个并发查询
        queries = [
            "你好",
            "Faker在直播吗？",
            "Uzi在直播吗？",
            "生成今日简报",
            "系统状态"
        ]
        
        async def execute_query(query: str) -> Dict[str, Any]:
            context = QueryContext(
                user_id="test_user",
                session_id=f"test_{datetime.now().timestamp()}",
                timestamp=datetime.now()
            )
            
            start_time = time.time()
            result = await router.smart_process(query, context)
            duration = time.time() - start_time
            
            return {
                "query": query,
                "duration": duration,
                "success": result.get("success", False)
            }
        
        # 并发执行
        start_time = time.time()
        results = await asyncio.gather(*[execute_query(q) for q in queries])
        total_duration = time.time() - start_time
        
        print(f"\n并发请求测试:")
        print(f"  并发数: {len(queries)}")
        print(f"  总耗时: {total_duration:.2f}s")
        print(f"  平均每个: {total_duration / len(queries):.2f}s")
        
        for result in results:
            print(f"  - {result['query']}: {result['duration']:.2f}s")
        
        # 所有请求都应成功
        assert all(r["success"] for r in results), "部分并发请求失败"
        
        # 并发执行应该比串行快
        # 串行执行时间估计 = 每个查询3秒 * 查询数
        # 并发应该显著快于串行
        assert total_duration < len(queries) * 3.0, "并发性能未达预期"
    
    @pytest.mark.asyncio
    async def test_performance_baseline(self, setup_agents):
        """
        建立性能基线
        """
        router = setup_agents
        
        # 执行一系列查询建立基线
        test_scenarios = [
            {"query": "你好", "expected_max": 1.0},
            {"query": "Faker在直播吗？", "expected_max": 3.0},
            {"query": "生成今日简报", "expected_max": 3.0},
            {"query": "系统状态", "expected_max": 1.0}
        ]
        
        baseline_results = []
        
        for scenario in test_scenarios:
            query = scenario["query"]
            expected_max = scenario["expected_max"]
            
            context = QueryContext(
                user_id="test_user",
                session_id=f"test_{datetime.now().timestamp()}",
                timestamp=datetime.now()
            )
            
            # 执行多次取平均
            durations = []
            for _ in range(3):
                start_time = time.time()
                result = await router.smart_process(query, context)
                duration = time.time() - start_time
                durations.append(duration)
                
                # 短暂延迟避免缓存影响
                await asyncio.sleep(0.1)
            
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            baseline_results.append({
                "query": query,
                "avg": avg_duration,
                "min": min_duration,
                "max": max_duration,
                "expected_max": expected_max
            })
            
            # 验证不超过预期最大值
            assert avg_duration < expected_max, \
                f"查询 '{query}' 平均响应时间 {avg_duration:.2f}s 超过预期 {expected_max}s"
        
        # 打印基线报告
        print("\n性能基线报告:")
        print("="*60)
        for result in baseline_results:
            print(f"查询: {result['query']}")
            print(f"  平均: {result['avg']:.3f}s")
            print(f"  最小: {result['min']:.3f}s")
            print(f"  最大: {result['max']:.3f}s")
            print(f"  预期最大: {result['expected_max']:.3f}s")
            print()
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, setup_agents):
        """
        测试：性能监控集成
        """
        router = setup_agents
        tracker = get_performance_tracker()
        
        # 执行一些查询
        queries = ["你好", "Faker在直播吗？", "系统状态"]
        
        for query in queries:
            context = QueryContext(
                user_id="test_user",
                session_id=f"test_{datetime.now().timestamp()}",
                timestamp=datetime.now()
            )
            await router.smart_process(query, context)
        
        # 获取性能统计
        stats = tracker.get_stats()
        summary = tracker.get_performance_summary()
        
        print("\n性能监控统计:")
        print(f"  总调用数: {summary['total_calls']}")
        print(f"  总耗时: {summary['total_time']:.2f}s")
        print(f"  平均耗时: {summary['avg_time']:.3f}s")
        print(f"  慢查询数: {summary['slow_queries_count']}")
        
        # 验证监控数据被正确记录
        assert summary['total_calls'] > 0, "性能监控未记录调用"
        assert summary['total_time'] > 0, "性能监控未记录时间"
        
        # 打印详细报告
        print("\n" + format_performance_report(detailed=False))


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
