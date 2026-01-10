# BriefingAgent - 简报生成 Agent
import asyncio
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime
from pathlib import Path

# 尝试导入 OpenAgents
try:
    from openagents import WorkerAgent
    OPENAGENTS_AVAILABLE = True
except ImportError:
    logger.warning("OpenAgents SDK 未安装，使用模拟模式")
    OPENAGENTS_AVAILABLE = False
    WorkerAgent = object


class BriefingAgent(WorkerAgent if OPENAGENTS_AVAILABLE else object):
    """
    简报生成 Agent

    功能：
    1. 汇总游戏圈重要事件
    2. 生成每日简报
    3. 格式化展示
    """

    def __init__(self, live_monitor=None):
        self.name = "BriefingAgent"
        self.description = "生成游戏圈简报"

        # 依赖的 Agent
        self.live_monitor = live_monitor

        logger.info(f"{self.name} 初始化成功")

    async def generate_briefing(self, time_range: str = "today") -> str:
        """
        生成简报

        Args:
            time_range: 时间范围（today/recent）

        Returns:
            格式化的简报文本
        """
        try:
            logger.info(f"生成 {time_range} 简报")

            # 获取当前直播中的主播
            live_players = []
            if self.live_monitor:
                live_players = await self.live_monitor.get_live_players()

            # 构建简报
            briefing = self._format_briefing(live_players)

            return briefing

        except Exception as e:
            logger.error(f"生成简报失败: {e}")
            return f"抱歉，生成简报时出错：{str(e)}"

    def _format_briefing(self, live_players: List[Dict]) -> str:
        """格式化简报"""
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")

        briefing = f"""
📰 【小游探日报】{date_str}

{'='*50}

🔥 当前直播中 ({len(live_players)} 人)
"""

        if live_players:
            for i, player in enumerate(live_players[:10], 1):  # 最多显示10个
                briefing += f"\n{i}. {player['player_name']}"
                briefing += f"\n   💬 {player.get('title', '无标题')}"
                briefing += f"\n   👥 人气：{player['viewer_count']:,}"
                if player.get('live_url'):
                    briefing += f"\n   🔗 {player['live_url']}"
                briefing += "\n"
        else:
            briefing += "\n暂无主播直播\n"

        briefing += f"\n{'='*50}\n"
        briefing += f"💡 提示：你可以询问具体主播的直播状态\n"
        briefing += f"📊 生成时间：{now.strftime('%H:%M')}\n"

        return briefing

    async def generate_live_summary(self, player_name: str) -> str:
        """生成特定主播的直播摘要"""
        if not self.live_monitor:
            return f"暂无 {player_name} 的直播信息"

        status = await self.live_monitor.check_player_status(player_name)

        if not status.get("is_live"):
            return f"📺 {player_name} 当前未在直播"

        summary = f"""
🎮 {player_name} 直播中
{'='*30}
📝 直播标题：{status.get('title', '无标题')}
👥 当前人气：{status.get('viewer_count', 0):,}
🎮 游戏类型：{status.get('game_name', '未知')}
🔗 直播链接：{status.get('live_url', '')}
{'='*30}
"""

        return summary

    async def add_custom_event(self, title: str, content: str, importance: int = 5):
        """
        添加自定义事件（用于手动添加重要新闻）

        Args:
            title: 事件标题
            content: 事件内容
            importance: 重要性（1-10）
        """
        # TODO: 实现事件存储
        logger.info(f"添加自定义事件: {title} (重要性: {importance})")
        pass


# 测试代码
async def test_briefing_agent():
    """测试简报 Agent"""
    # 创建模拟的 LiveMonitor
    from unittest.mock import Mock

    mock_monitor = Mock()
    mock_monitor.get_live_players = asyncio.coroutine(
        lambda: [
            {"player_name": "Uzi", "viewer_count": 200000, "title": "深夜Rank训练", "live_url": "https://huya.com/995888"},
            {"player_name": "Faker", "viewer_count": 150000, "title": "T1训练赛", "live_url": "https://huya.com/123456"}
        ]
    )

    briefing_agent = BriefingAgent(live_monitor=mock_monitor)

    # 生成简报
    briefing = await briefing_agent.generate_briefing()
    print(briefing)


if __name__ == "__main__":
    asyncio.run(test_briefing_agent())
