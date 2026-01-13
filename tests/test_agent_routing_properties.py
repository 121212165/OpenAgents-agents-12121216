# 测试Agent路由智能性 - Property Tests
"""
Task 3.2: 测试Agent路由智能性
验证RouterAgent的智能路由和意图识别能力
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from typing import Dict, Any, List
from loguru import logger

# 导入被测试的组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.utils.data_sources import DataSourceManager, MockDataSource


class TestAgentRoutingProperties:
    """Agent路由智能性属性测试"""
    
    @pytest.fixture
    async def setup_router_system(self):
        """设置完整的路由系统"""
        # 创建数据源管理器
        data_manager = DataSourceManager()
        mock_source = MockDataSource()
        data_manager.add_source(mock_source)
        
        # 创建LiveMonitor Agent
        live_monitor = LiveMonitorAgent()
        live_monitor.data_manager = data_manager
        
        # 创建Briefing Agent
        briefing_agent = BriefingAgent(live_monitor=live_monitor)
        
        # 创建Router Agent并注入依赖
        router = RouterAgent()
        router.live_monitor = live_monitor
        router.briefing_agent = briefing_agent
        
        # 启动所有Agent
        await router.on_startup()
        await live_monitor.on_startup()
        await briefing_agent.on_startup()
        
        yield {
            "router": router,
            "live_monitor": live_monitor,
            "briefing_agent": briefing_agent
        }
        
        # 清理
        await router.on_shutdown()
        await live_monitor.on_shutdown()
        await briefing_agent.on_shutdown()
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50, deadline=5000)
    async def test_property_intent_classification_consistency(self, query_text, setup_router_system):
        """
        Property 3.1: 意图分类一致性
        相同的查询应该产生一致的意图分类结果
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            # 多次执行相同查询
            results = []
            for _ in range(3):
                result = await router._detect_intent_smart(query_text)
                results.append(result)
            
            # 验证一致性
            if len(results) > 1:
                first_intent = results[0].get("intent")
                for result in results[1:]:
                    assert result.get("intent") == first_intent, \
                        f"意图分类不一致: {query_text} -> {[r.get('intent') for r in results]}"
            
            logger.info(f"✅ 意图分类一致性测试通过: {query_text} -> {results[0].get('intent')}")
            
        except Exception as e:
            logger.error(f"❌ 意图分类一致性测试失败: {query_text} -> {e}")
            # 对于无效输入，允许失败
            if len(query_text.strip()) == 0:
                pytest.skip("空查询跳过")
            raise
    
    @given(st.sampled_from([
        "Faker在直播吗",
        "Uzi开播了吗", 
        "查看TheShy的直播状态",
        "大司马在线吗",
        "直播中的主播有哪些"
    ]))
    @settings(max_examples=20, deadline=10000)
    async def test_property_live_query_routing(self, live_query, setup_router_system):
        """
        Property 3.2: 直播查询路由正确性
        直播相关查询应该正确路由到LiveMonitor Agent
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            result = await router.process(live_query)
            
            # 验证路由正确性
            assert result["success"] is not None, "结果应该有success字段"
            assert "agent_used" in result, "结果应该包含使用的agent信息"
            
            # 对于直播查询，应该使用live_monitor或router
            used_agent = result["agent_used"]
            assert used_agent in ["live_monitor", "router"], \
                f"直播查询应该路由到live_monitor或router，实际: {used_agent}"
            
            # 响应应该包含直播相关信息
            response = result["response"]
            assert isinstance(response, str), "响应应该是字符串"
            assert len(response) > 0, "响应不应该为空"
            
            logger.info(f"✅ 直播查询路由测试通过: {live_query} -> {used_agent}")
            
        except Exception as e:
            logger.error(f"❌ 直播查询路由测试失败: {live_query} -> {e}")
            raise
    
    @given(st.sampled_from([
        "生成今日简报",
        "简报",
        "汇总游戏圈动态", 
        "日报",
        "briefing"
    ]))
    @settings(max_examples=15, deadline=10000)
    async def test_property_briefing_query_routing(self, briefing_query, setup_router_system):
        """
        Property 3.3: 简报查询路由正确性
        简报相关查询应该正确路由到Briefing Agent
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            result = await router.process(briefing_query)
            
            # 验证路由正确性
            assert result["success"] is not None, "结果应该有success字段"
            assert "agent_used" in result, "结果应该包含使用的agent信息"
            
            # 对于简报查询，应该使用briefing agent
            used_agent = result["agent_used"]
            assert used_agent == "briefing", \
                f"简报查询应该路由到briefing agent，实际: {used_agent}"
            
            # 响应应该包含简报内容
            response = result["response"]
            assert isinstance(response, str), "响应应该是字符串"
            assert len(response) > 0, "响应不应该为空"
            assert "简报" in response or "直播" in response, "响应应该包含简报相关内容"
            
            logger.info(f"✅ 简报查询路由测试通过: {briefing_query} -> {used_agent}")
            
        except Exception as e:
            logger.error(f"❌ 简报查询路由测试失败: {briefing_query} -> {e}")
            raise
    
    @given(st.sampled_from([
        "你好",
        "hi", 
        "hello",
        "嗨",
        "您好"
    ]))
    @settings(max_examples=10, deadline=5000)
    async def test_property_greeting_handling(self, greeting, setup_router_system):
        """
        Property 3.4: 问候处理正确性
        问候语应该得到适当的响应
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            result = await router.process(greeting)
            
            # 验证问候处理
            assert result["success"] == True, "问候应该成功处理"
            assert result["agent_used"] == "router", "问候应该由router处理"
            
            response = result["response"]
            assert isinstance(response, str), "响应应该是字符串"
            assert len(response) > 0, "响应不应该为空"
            assert any(word in response for word in ["你好", "助手", "帮助"]), \
                "问候响应应该包含友好内容"
            
            logger.info(f"✅ 问候处理测试通过: {greeting}")
            
        except Exception as e:
            logger.error(f"❌ 问候处理测试失败: {greeting} -> {e}")
            raise
    
    @given(st.text(min_size=1, max_size=50).filter(
        lambda x: not any(keyword in x.lower() for keyword in 
                         ["直播", "简报", "你好", "hi", "hello", "嗨", "live", "briefing"])
    ))
    @settings(max_examples=30, deadline=5000)
    async def test_property_unknown_intent_handling(self, unknown_query, setup_router_system):
        """
        Property 3.5: 未知意图处理
        未知查询应该得到合理的降级响应
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            result = await router.process(unknown_query)
            
            # 验证未知意图处理
            assert "success" in result, "结果应该有success字段"
            assert "response" in result, "结果应该有response字段"
            assert "agent_used" in result, "结果应该有agent_used字段"
            
            response = result["response"]
            assert isinstance(response, str), "响应应该是字符串"
            assert len(response) > 0, "响应不应该为空"
            
            # 未知查询的响应应该包含帮助信息
            help_indicators = ["可以", "尝试", "查询", "帮助", "例如"]
            assert any(indicator in response for indicator in help_indicators), \
                f"未知查询响应应该包含帮助信息: {response}"
            
            logger.info(f"✅ 未知意图处理测试通过: {unknown_query}")
            
        except Exception as e:
            logger.error(f"❌ 未知意图处理测试失败: {unknown_query} -> {e}")
            # 对于特殊字符或无效输入，允许失败
            if not unknown_query.strip() or len(unknown_query.strip()) < 2:
                pytest.skip("无效查询跳过")
            raise
    
    async def test_property_response_time_reasonable(self, setup_router_system):
        """
        Property 3.6: 响应时间合理性
        所有查询的响应时间应该在合理范围内
        """
        system = await setup_router_system
        router = system["router"]
        
        test_queries = [
            "你好",
            "Faker在直播吗",
            "生成简报",
            "未知查询测试"
        ]
        
        import time
        
        for query in test_queries:
            try:
                start_time = time.time()
                result = await router.process(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # 响应时间应该在合理范围内（10秒内）
                assert response_time < 10.0, \
                    f"响应时间过长: {query} -> {response_time:.2f}s"
                
                # 结果应该有效
                assert "response" in result, "结果应该包含响应"
                assert isinstance(result["response"], str), "响应应该是字符串"
                
                logger.info(f"✅ 响应时间测试通过: {query} -> {response_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ 响应时间测试失败: {query} -> {e}")
                raise


# 运行测试
async def run_routing_property_tests():
    """运行路由智能性属性测试"""
    logger.info("🧪 开始Agent路由智能性属性测试...")
    
    test_instance = TestAgentRoutingProperties()
    
    # 设置测试系统
    async for system in test_instance.setup_router_system():
        try:
            # 测试基本功能
            logger.info("测试基本路由功能...")
            
            # 测试直播查询
            await test_instance.test_property_live_query_routing("Faker在直播吗", system)
            
            # 测试简报查询  
            await test_instance.test_property_briefing_query_routing("生成简报", system)
            
            # 测试问候
            await test_instance.test_property_greeting_handling("你好", system)
            
            # 测试响应时间
            await test_instance.test_property_response_time_reasonable(system)
            
            logger.info("✅ Agent路由智能性属性测试完成")
            
        except Exception as e:
            logger.error(f"❌ 路由属性测试失败: {e}")
            raise
        
        break  # 只运行一次


if __name__ == "__main__":
    asyncio.run(run_routing_property_tests())