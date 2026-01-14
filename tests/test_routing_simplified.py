# 简化的路由测试 - 实用版本
"""
简化的Agent路由测试，专注于核心功能验证
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.router_agent import RouterAgent, QueryContext
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent


@pytest.fixture
async def router_system():
    """创建完整的路由系统"""
    # 创建所有Agent
    data_source = DataSourceAgent()
    live_monitor = LiveMonitorAgent()
    briefing_agent = BriefingAgent()
    router = RouterAgent()
    
    # 注册Agent
    router.register_agent("live_monitor", live_monitor)
    router.register_agent("briefing_agent", briefing_agent)
    router.register_agent("data_source", data_source)
    
    # 启动Agent
    await data_source.on_startup()
    await live_monitor.on_startup()
    await briefing_agent.on_startup()
    await router.on_startup()
    
    yield {
        "router": router,
        "live_monitor": live_monitor,
        "briefing_agent": briefing_agent,
        "data_source": data_source
    }
    
    # 清理
    await router.on_shutdown()
    await briefing_agent.on_shutdown()
    await live_monitor.on_shutdown()
    await data_source.on_shutdown()


class TestRoutingBasics:
    """基础路由功能测试"""
    
    @pytest.mark.asyncio
    async def test_greeting_routing(self, router_system):
        """测试问候语路由"""
        router = router_system["router"]
        
        greetings = ["你好", "hi", "hello"]
        
        for greeting in greetings:
            context = QueryContext(
                user_id="test_user",
                session_id="test_session",
                timestamp=datetime.now()
            )
            
            result = await router.smart_process(greeting, context)
            
            assert result["success"] is True
            assert result["response"]
            assert len(result["response"]) > 0
            
            print(f"✅ 问候测试通过: {greeting}")
    
    @pytest.mark.asyncio
    async def test_live_query_routing(self, router_system):
        """测试直播查询路由"""
        router = router_system["router"]
        
        queries = ["Faker在直播吗", "Uzi开播了吗"]
        
        for query in queries:
            context = QueryContext(
                user_id="test_user",
                session_id="test_session",
                timestamp=datetime.now()
            )
            
            result = await router.smart_process(query, context)
            
            assert result["success"] is True
            assert result["response"]
            
            print(f"✅ 直播查询测试通过: {query}")
    
    @pytest.mark.asyncio
    async def test_briefing_routing(self, router_system):
        """测试简报路由"""
        router = router_system["router"]
        
        context = QueryContext(
            user_id="test_user",
            session_id="test_session",
            timestamp=datetime.now()
        )
        
        result = await router.smart_process("生成今日简报", context)
        
        assert result["success"] is True
        assert result["response"]
        assert len(result["response"]) > 50  # 简报应该有一定长度
        
        print("✅ 简报路由测试通过")
    
    @pytest.mark.asyncio
    async def test_response_time(self, router_system):
        """测试响应时间"""
        router = router_system["router"]
        
        queries = ["你好", "Faker在直播吗", "生成简报"]
        
        for query in queries:
            context = QueryContext(
                user_id="test_user",
                session_id="test_session",
                timestamp=datetime.now()
            )
            
            start = datetime.now()
            result = await router.smart_process(query, context)
            elapsed = (datetime.now() - start).total_seconds()
            
            assert result["success"] is True
            assert elapsed < 5.0, f"响应时间过长: {elapsed:.2f}s"
            
            print(f"✅ 响应时间测试通过: {query} - {elapsed:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
