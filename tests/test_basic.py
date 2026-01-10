# 基础测试
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def test_imports():
    """测试基础导入"""
    # 测试工具导入
    from src.utils.common import setup_logger, load_yaml_config
    from src.utils.huya_api import HuyaClient

    # 测试 Agent 导入
    from src.agents.router_agent import RouterAgent
    from src.agents.live_monitor_agent import LiveMonitorAgent
    from src.agents.briefing_agent import BriefingAgent

    assert True


@pytest.mark.asyncio
async def test_router_agent():
    """测试 Router Agent"""
    from src.agents.router_agent import RouterAgent

    router = RouterAgent()

    # 测试问候
    result = await router.process("你好")
    assert result["success"] == True
    assert "小游探" in result["response"]

    # 测试未知意图
    result = await router.process("随便说点什么")
    assert result["success"] == False


@pytest.mark.asyncio
async def test_huya_client():
    """测试虎牙客户端"""
    from src.utils.huya_api import HuyaClient

    async with HuyaClient() as client:
        # 测试状态检测（使用示例房间号）
        result = await client.check_live_status("995888")

        assert "is_live" in result
        assert "room_id" in result
        assert "checked_at" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
