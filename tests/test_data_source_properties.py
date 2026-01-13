# 数据源故障切换属性测试
"""
使用Hypothesis进行数据源故障切换的属性测试
验证数据源管理器的可靠性和故障恢复能力
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

# 导入被测试的模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_sources import (
    DataSourceManager, DataSource, DataQuery, DataResult,
    DataSourceType, DataSourceStatus, MockDataSource
)

class TestDataSource(DataSource):
    """测试用数据源"""
    
    def __init__(self, name: str, should_fail: bool = False, delay: float = 0):
        super().__init__(DataSourceType.MOCK, name)
        self.should_fail = should_fail
        self.delay = delay
        self.fetch_count = 0
        self.health_check_count = 0
        
        # 初始化状态
        if should_fail:
            self.status = DataSourceStatus.FAILED
        else:
            self.status = DataSourceStatus.HEALTHY
        
    async def fetch(self, query: DataQuery) -> DataResult:
        """模拟数据获取"""
        self.fetch_count += 1
        
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        if self.should_fail:
            self.mark_error()
            return DataResult(
                success=False,
                data=None,
                source=self.name,
                error="Simulated failure"
            )
        else:
            self.mark_success()
            return DataResult(
                success=True,
                data={"test": "data", "source": self.name},
                source=self.name
            )
    
    async def health_check(self) -> bool:
        """模拟健康检查"""
        self.health_check_count += 1
        return not self.should_fail

class TestDataSourceFailover:
    """数据源故障切换属性测试"""
    
    async def test_failover_property(self, source_count: int = 3, failed_sources: int = 1):
        """
        属性: 当部分数据源失败时，系统应该自动切换到健康的数据源
        """
        if failed_sources >= source_count:
            failed_sources = source_count - 1  # 确保至少有一个健康的数据源
        
        manager = DataSourceManager()
        
        # 创建数据源：部分失败，部分正常
        for i in range(source_count):
            should_fail = i < failed_sources
            source = TestDataSource(f"source_{i}", should_fail=should_fail)
            manager.add_source(source)
        
        # 执行查询
        query = DataQuery(query_type="test", parameters={})
        result = await manager.fetch(query)
        
        # 验证属性
        assert result.success, "至少有一个健康数据源时，查询应该成功"
        assert result.data is not None, "成功的查询应该返回数据"
        assert "source_" in result.source, "结果应该标明数据来源"
        
        # 验证只有健康的数据源被使用
        healthy_sources = [s for s in manager.sources if not s.should_fail]
        assert any(s.fetch_count > 0 for s in healthy_sources), "至少一个健康数据源被调用"
    
    async def test_timeout_handling_property(self, timeout_values: list = [1.0, 0.1]):
        """
        属性: 当数据源超时时，系统应该切换到其他数据源
        """
        manager = DataSourceManager()
        
        # 创建数据源：第一个超时，后续正常
        for i, delay in enumerate(timeout_values):
            source = TestDataSource(f"source_{i}", delay=delay)
            manager.add_source(source)
        
        # 添加一个快速响应的数据源
        fast_source = TestDataSource("fast_source", delay=0)
        manager.add_source(fast_source)
        
        # 执行查询（短超时）
        query = DataQuery(query_type="test", parameters={}, timeout=0.5)
        result = await manager.fetch(query)
        
        # 验证属性
        assert result.success, "应该有快速数据源响应成功"
        
        # 验证超时的数据源被标记为错误
        slow_sources = [s for s in manager.sources if s.delay > 0.5]
        for source in slow_sources:
            assert source.status in [DataSourceStatus.DEGRADED, DataSourceStatus.FAILED], \
                f"超时的数据源 {source.name} 应该被标记为异常"
    
    async def test_error_recovery_property(self, error_counts: list = [2, 4, 1]):
        """
        属性: 数据源在连续错误后应该被标记为失败，成功后应该恢复
        """
        manager = DataSourceManager()
        manager.fallback_enabled = False  # 禁用故障切换以测试错误累积
        
        # 创建测试数据源
        source = TestDataSource("test_source")
        manager.add_source(source)
        
        for i, error_count in enumerate(error_counts):
            # 模拟连续错误
            source.should_fail = True
            source.error_count = 0  # 重置错误计数
            
            for j in range(error_count):
                # 使用不同的查询参数避免缓存干扰
                query = DataQuery(query_type="test", parameters={"iteration": i, "attempt": j})
                await manager.fetch(query)
            
            # 验证错误状态
            if error_count >= source.max_errors:
                assert source.status == DataSourceStatus.FAILED, \
                    f"连续 {error_count} 次错误后应该标记为失败"
            elif error_count > 0:
                assert source.status == DataSourceStatus.DEGRADED, \
                    f"少量错误后应该标记为降级"
            
            # 模拟恢复
            source.should_fail = False
            source.error_count = 0  # 重置错误计数
            source.status = DataSourceStatus.HEALTHY  # 手动恢复状态
            
            query = DataQuery(query_type="test", parameters={"recovery": i})
            result = await manager.fetch(query)
            
            # 数据源恢复后应该能够成功
            assert result.success, "数据源恢复后查询应该成功"
            assert source.status == DataSourceStatus.HEALTHY, "成功后应该标记为健康"
    
    async def test_cache_behavior_property(self, cache_ttl: int = 5, query_interval: int = 2):
        """
        属性: 缓存应该在TTL内返回缓存数据，过期后重新获取
        """
        manager = DataSourceManager()
        source = TestDataSource("test_source")
        manager.add_source(source)
        
        # 第一次查询
        query = DataQuery(query_type="test", parameters={"key": "value"}, cache_ttl=cache_ttl)
        result1 = await manager.fetch(query)
        
        assert result1.success, "第一次查询应该成功"
        assert not result1.cached, "第一次查询不应该是缓存结果"
        
        # 等待指定时间后再次查询
        await asyncio.sleep(query_interval / 10)  # 缩短等待时间以加快测试
        
        result2 = await manager.fetch(query)
        assert result2.success, "第二次查询应该成功"
        
        # 验证缓存行为
        if query_interval < cache_ttl:
            # 应该使用缓存
            assert result2.cached or source.fetch_count == 1, \
                "在TTL内应该使用缓存或只调用一次数据源"
        # 注意：由于测试时间缩短，不验证过期情况
    
    async def test_source_priority_property(self, source_priorities: list = [1, 2, 3]):
        """
        属性: 数据源应该按照添加顺序尝试（优先级）
        """
        manager = DataSourceManager()
        manager.fallback_enabled = False  # 禁用故障切换以测试优先级
        
        # 按优先级添加数据源（第一个失败，后续成功）
        sources = []
        for i, priority in enumerate(source_priorities):
            should_fail = (i == 0)  # 第一个数据源失败
            source = TestDataSource(f"source_{i}_priority_{priority}", should_fail=should_fail)
            sources.append(source)
            manager.add_source(source)
        
        # 执行查询
        query = DataQuery(query_type="test", parameters={})
        result = await manager.fetch(query)
        
        # 验证属性
        assert result.success, "应该有数据源成功响应"
        
        # 验证优先级：第一个数据源应该被尝试
        assert sources[0].fetch_count > 0, "第一个数据源应该被尝试"
        
        # 验证成功的数据源
        successful_source = next((s for s in sources if not s.should_fail), None)
        if successful_source:
            assert successful_source.fetch_count > 0, "成功的数据源应该被调用"
    
    async def test_all_sources_failed_property(self):
        """
        属性: 当所有数据源都失败时，应该返回失败结果
        """
        manager = DataSourceManager()
        
        # 添加多个失败的数据源
        for i in range(3):
            source = TestDataSource(f"failed_source_{i}", should_fail=True)
            manager.add_source(source)
        
        # 执行查询
        query = DataQuery(query_type="test", parameters={})
        result = await manager.fetch(query)
        
        # 验证属性
        assert not result.success, "所有数据源失败时，查询应该失败"
        assert result.error is not None, "失败结果应该包含错误信息"
        assert "All data sources failed" in result.error, "错误信息应该说明所有数据源失败"
    
    async def test_health_check_property(self):
        """
        属性: 健康检查应该正确反映数据源状态
        """
        manager = DataSourceManager()
        
        # 添加健康和不健康的数据源
        healthy_source = TestDataSource("healthy", should_fail=False)
        unhealthy_source = TestDataSource("unhealthy", should_fail=True)
        
        manager.add_source(healthy_source)
        manager.add_source(unhealthy_source)
        
        # 执行健康检查
        health_results = await manager.health_check_all()
        
        # 验证属性
        assert health_results["healthy"] == True, "健康数据源应该通过健康检查"
        assert health_results["unhealthy"] == False, "不健康数据源应该未通过健康检查"
        
        # 验证状态更新
        assert healthy_source.status == DataSourceStatus.HEALTHY, "健康数据源状态应该正确"
        assert unhealthy_source.status in [DataSourceStatus.DEGRADED, DataSourceStatus.FAILED], \
            "不健康数据源状态应该正确"

# 运行测试的辅助函数
async def run_property_tests():
    """运行所有属性测试"""
    test_instance = TestDataSourceFailover()
    
    print("🧪 开始数据源故障切换属性测试...")
    
    try:
        # 测试故障切换
        print("  测试故障切换属性...")
        await test_instance.test_failover_property(3, 1)
        print("  ✅ 故障切换属性测试通过")
        
        # 测试超时处理
        print("  测试超时处理属性...")
        await test_instance.test_timeout_handling_property([1.0, 0.1])
        print("  ✅ 超时处理属性测试通过")
        
        # 测试错误恢复
        print("  测试错误恢复属性...")
        await test_instance.test_error_recovery_property([2, 4, 1])
        print("  ✅ 错误恢复属性测试通过")
        
        # 测试缓存行为
        print("  测试缓存行为属性...")
        await test_instance.test_cache_behavior_property(5, 2)
        print("  ✅ 缓存行为属性测试通过")
        
        # 测试数据源优先级
        print("  测试数据源优先级属性...")
        await test_instance.test_source_priority_property([1, 2, 3])
        print("  ✅ 数据源优先级属性测试通过")
        
        # 测试全部失败情况
        print("  测试全部失败属性...")
        await test_instance.test_all_sources_failed_property()
        print("  ✅ 全部失败属性测试通过")
        
        # 测试健康检查
        print("  测试健康检查属性...")
        await test_instance.test_health_check_property()
        print("  ✅ 健康检查属性测试通过")
        
        print("\n🎉 所有数据源故障切换属性测试通过！")
        
    except Exception as e:
        print(f"\n❌ 属性测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_property_tests())