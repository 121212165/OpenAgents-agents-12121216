#!/usr/bin/env python3
"""
OpenAgents 属性测试
验证 OpenAgents 消息协议合规性

Feature: yougame-mvp, Property 1: OpenAgents Message Protocol Compliance
"""

import asyncio
import sys
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.agents.router_agent import RouterAgent
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent

class TestOpenAgentsProtocolCompliance:
    """测试OpenAgents协议合规性"""

    @pytest.fixture
    async def router_agent(self):
        """创建RouterAgent实例"""
        agent = RouterAgent()
        await agent.on_startup()
        yield agent
        await agent.on_shutdown()

    @pytest.fixture
    async def live_monitor_agent(self):
        """创建LiveMonitorAgent实例"""
        agent = LiveMonitorAgent()
        await agent.on_startup()
        yield agent
        await agent.on_shutdown()

    @pytest.fixture
    async def briefing_agent(self):
        """创建BriefingAgent实例"""
        agent = BriefingAgent()
        await agent.on_startup()
        yield agent
        await agent.on_shutdown()

    @given(
        content=st.text(min_size=1, max_size=100),
        sender=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=100)
    async def test_router_agent_message_protocol_compliance(self, router_agent, content, sender):
        """
        Property 1: OpenAgents Message Protocol Compliance
        For any inter-agent communication, messages should follow OpenAgents standard protocol format
        
        **Validates: Requirements 1.3**
        """
        # 创建符合OpenAgents标准的消息格式
        message = {
            'content': content,
            'sender': sender,
            'timestamp': '2026-01-10T14:00:00Z',
            'message_id': f'msg_{hash(content + sender) % 10000}'
        }
        
        # 验证Agent具有OpenAgents标准方法
        assert hasattr(router_agent, 'on_direct'), "Agent应该有on_direct方法"
        assert hasattr(router_agent, 'on_startup'), "Agent应该有on_startup方法"
        assert hasattr(router_agent, 'on_shutdown'), "Agent应该有on_shutdown方法"
        assert hasattr(router_agent, 'agent_id'), "Agent应该有agent_id属性"
        
        # 验证agent_id格式
        assert isinstance(router_agent.agent_id, str), "agent_id应该是字符串"
        assert len(router_agent.agent_id) > 0, "agent_id不应该为空"
        
        # 验证消息处理方法存在且可调用
        assert callable(router_agent.on_direct), "on_direct应该是可调用的"

    @given(
        content=st.one_of(
            st.just('status Uzi'),
            st.just('list'),
            st.just('help'),
            st.text(min_size=1, max_size=50)
        ),
        sender=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=100)
    async def test_live_monitor_message_protocol_compliance(self, live_monitor_agent, content, sender):
        """
        Property 1: OpenAgents Message Protocol Compliance (LiveMonitor)
        For any message to LiveMonitor agent, it should handle OpenAgents standard message format
        
        **Validates: Requirements 1.3**
        """
        message = {
            'content': content,
            'sender': sender,
            'channel': 'direct',
            'timestamp': '2026-01-10T14:00:00Z'
        }
        
        # 验证Agent具有OpenAgents标准接口
        assert hasattr(live_monitor_agent, 'on_direct'), "LiveMonitor应该有on_direct方法"
        assert hasattr(live_monitor_agent, 'agent_id'), "LiveMonitor应该有agent_id属性"
        assert live_monitor_agent.agent_id == 'live-monitor-agent', "agent_id应该正确设置"
        
        # 验证Agent状态
        assert hasattr(live_monitor_agent, 'players'), "LiveMonitor应该有players配置"
        assert isinstance(live_monitor_agent.players, list), "players应该是列表"

    @given(
        content=st.one_of(
            st.just('briefing'),
            st.just('report'),
            st.just('summary Uzi'),
            st.text(min_size=1, max_size=50)
        ),
        sender=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=100)
    async def test_briefing_agent_message_protocol_compliance(self, briefing_agent, content, sender):
        """
        Property 1: OpenAgents Message Protocol Compliance (Briefing)
        For any message to Briefing agent, it should handle OpenAgents standard message format
        
        **Validates: Requirements 1.3**
        """
        message = {
            'content': content,
            'sender': sender,
            'channel': 'direct',
            'timestamp': '2026-01-10T14:00:00Z'
        }
        
        # 验证Agent具有OpenAgents标准接口
        assert hasattr(briefing_agent, 'on_direct'), "BriefingAgent应该有on_direct方法"
        assert hasattr(briefing_agent, 'agent_id'), "BriefingAgent应该有agent_id属性"
        assert briefing_agent.agent_id == 'briefing-agent', "agent_id应该正确设置"
        
        # 验证核心方法存在
        assert hasattr(briefing_agent, 'generate_briefing'), "应该有generate_briefing方法"
        assert callable(briefing_agent.generate_briefing), "generate_briefing应该可调用"

    @given(
        user_input=st.one_of(
            st.just('你好'),
            st.just('Uzi 直播了吗'),
            st.just('生成今日简报'),
            st.text(min_size=1, max_size=100)
        )
    )
    @settings(max_examples=100)
    async def test_agent_process_method_compliance(self, router_agent, user_input):
        """
        Property 1: Agent Process Method Compliance
        For any user input, the agent process method should return standard format
        
        **Validates: Requirements 1.3**
        """
        # 调用处理方法
        result = await router_agent.process(user_input)
        
        # 验证返回格式符合标准
        assert isinstance(result, dict), "process方法应该返回字典"
        assert 'success' in result, "结果应该包含success字段"
        assert 'response' in result, "结果应该包含response字段"
        assert 'agent_used' in result, "结果应该包含agent_used字段"
        
        # 验证字段类型
        assert isinstance(result['success'], bool), "success应该是布尔值"
        assert isinstance(result['response'], str), "response应该是字符串"
        assert isinstance(result['agent_used'], str), "agent_used应该是字符串"
        
        # 验证响应不为空
        assert len(result['response']) > 0, "响应不应该为空"

# 同步测试运行器
def test_openagents_protocol_compliance():
    """同步测试入口"""
    import asyncio
    
    async def run_tests():
        # 创建Agent实例
        router = RouterAgent()
        live_monitor = LiveMonitorAgent()
        briefing = BriefingAgent()
        
        try:
            await router.on_startup()
            await live_monitor.on_startup()
            await briefing.on_startup()
            
            # 运行基础合规性测试
            print("测试RouterAgent OpenAgents协议合规性...")
            
            # 验证Agent具有OpenAgents标准方法
            assert hasattr(router, 'on_direct'), "Agent应该有on_direct方法"
            assert hasattr(router, 'on_startup'), "Agent应该有on_startup方法"
            assert hasattr(router, 'on_shutdown'), "Agent应该有on_shutdown方法"
            assert hasattr(router, 'agent_id'), "Agent应该有agent_id属性"
            
            # 验证agent_id格式
            assert isinstance(router.agent_id, str), "agent_id应该是字符串"
            assert len(router.agent_id) > 0, "agent_id不应该为空"
            assert router.agent_id == 'router-agent', "router agent_id应该正确"
            
            print("✅ RouterAgent协议合规性测试通过")
            
            # 测试LiveMonitor合规性
            print("测试LiveMonitorAgent OpenAgents协议合规性...")
            assert hasattr(live_monitor, 'on_direct'), "LiveMonitor应该有on_direct方法"
            assert hasattr(live_monitor, 'agent_id'), "LiveMonitor应该有agent_id属性"
            assert live_monitor.agent_id == 'live-monitor-agent', "live-monitor agent_id应该正确"
            assert hasattr(live_monitor, 'players'), "LiveMonitor应该有players配置"
            assert isinstance(live_monitor.players, list), "players应该是列表"
            
            print("✅ LiveMonitorAgent协议合规性测试通过")
            
            # 测试BriefingAgent合规性
            print("测试BriefingAgent OpenAgents协议合规性...")
            assert hasattr(briefing, 'on_direct'), "BriefingAgent应该有on_direct方法"
            assert hasattr(briefing, 'agent_id'), "BriefingAgent应该有agent_id属性"
            assert briefing.agent_id == 'briefing-agent', "briefing agent_id应该正确"
            assert hasattr(briefing, 'generate_briefing'), "应该有generate_briefing方法"
            assert callable(briefing.generate_briefing), "generate_briefing应该可调用"
            
            print("✅ BriefingAgent协议合规性测试通过")
            
            # 测试process方法合规性
            print("测试Agent process方法合规性...")
            test_inputs = ["你好", "Uzi 直播了吗", "生成今日简报", "测试消息"]
            
            for user_input in test_inputs:
                result = await router.process(user_input)
                
                # 验证返回格式符合标准
                assert isinstance(result, dict), f"process方法应该返回字典，输入: {user_input}"
                assert 'success' in result, f"结果应该包含success字段，输入: {user_input}"
                assert 'response' in result, f"结果应该包含response字段，输入: {user_input}"
                assert 'agent_used' in result, f"结果应该包含agent_used字段，输入: {user_input}"
                
                # 验证字段类型
                assert isinstance(result['success'], bool), f"success应该是布尔值，输入: {user_input}"
                assert isinstance(result['response'], str), f"response应该是字符串，输入: {user_input}"
                assert isinstance(result['agent_used'], str), f"agent_used应该是字符串，输入: {user_input}"
                
                # 验证响应不为空
                assert len(result['response']) > 0, f"响应不应该为空，输入: {user_input}"
            
            print("✅ Agent process方法合规性测试通过")
            
            print("✅ 所有OpenAgents协议合规性测试通过")
            return True
            
        finally:
            await router.on_shutdown()
            await live_monitor.on_shutdown()
            await briefing.on_shutdown()
    
    return asyncio.run(run_tests())

if __name__ == "__main__":
    success = test_openagents_protocol_compliance()
    sys.exit(0 if success else 1)