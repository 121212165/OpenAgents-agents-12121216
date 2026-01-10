# Router Agent - 路由中枢
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

# 尝试导入 OpenAgents
try:
    from openagents import WorkerAgent, AgentContext
    OPENAGENTS_AVAILABLE = True
except ImportError:
    logger.warning("OpenAgents SDK 未安装，使用模拟模式")
    OPENAGENTS_AVAILABLE = False
    WorkerAgent = object


class RouterAgent(WorkerAgent if OPENAGENTS_AVAILABLE else object):
    """
    路由中枢 Agent

    功能：
    1. 接收用户查询
    2. 识别查询意图
    3. 分发任务给相应的 Agent
    4. 整合结果并返回
    """

    def __init__(self):
        self.name = "Router Agent"
        self.description = "小游探的路由中枢，负责任务分发和协调"

        # 依赖的 Agent（后续会注入）
        self.live_monitor = None
        self.briefing_agent = None

        # 意图识别模式
        self.intent_patterns = {
            "直播查询": ["直播", "开播", "在播", "在线吗", "直播了吗"],
            "生成简报": ["简报", "日报", "汇总", "总结"],
            "查询状态": ["状态", "怎么样", "最近"],
            "问候": ["你好", "嗨", "hello", "hi"]
        }

        logger.info(f"{self.name} 初始化成功")

    async def process(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户输入

        Args:
            user_input: 用户查询
            context: 上下文信息

        Returns:
            {
                "success": bool,
                "response": str,
                "data": Any,
                "agent_used": str
            }
        """
        try:
            logger.info(f"处理用户查询: {user_input}")

            # 1. 识别意图
            intent = self._detect_intent(user_input)
            logger.info(f"识别到意图: {intent}")

            # 2. 提取实体（主播名等）
            entities = self._extract_entities(user_input)
            logger.info(f"提取实体: {entities}")

            # 3. 路由到相应的 Agent
            if intent == "直播查询":
                return await self._handle_live_query(user_input, entities)

            elif intent == "生成简报":
                return await self._handle_briefing(user_input, entities)

            elif intent == "问候":
                return self._greeting()

            else:
                return self._unknown_intent()

        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            return {
                "success": False,
                "response": f"抱歉，处理您的请求时出错了：{str(e)}",
                "data": None,
                "agent_used": "router"
            }

    def _detect_intent(self, text: str) -> str:
        """识别用户意图"""
        text_lower = text.lower()

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent

        return "未知"

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体（主播名、时间等）"""
        entities = {
            "player_name": None,
            "time_range": None,
            "platform": None
        }

        # 从配置中加载主播列表（简化版）
        # TODO: 实际应该从 players.yaml 读取
        known_players = ["Uzi", "Faker", "大司马", "TheShy", "Rookie"]

        for player in known_players:
            if player in text:
                entities["player_name"] = player
                break

        # 识别时间范围
        if "今天" in text:
            entities["time_range"] = "today"
        elif "最近" in text or "几天" in text:
            entities["time_range"] = "recent"

        # 识别平台
        if "虎牙" in text:
            entities["platform"] = "huya"

        return entities

    async def _handle_live_query(self, query: str, entities: Dict) -> Dict[str, Any]:
        """处理直播查询"""
        player_name = entities.get("player_name")

        if not player_name:
            return {
                "success": False,
                "response": "请问你要查询哪位主播的直播状态？",
                "data": None,
                "agent_used": "router"
            }

        if not self.live_monitor:
            return {
                "success": False,
                "response": "直播监控 Agent 未就绪",
                "data": None,
                "agent_used": "router"
            }

        # 调用 LiveMonitor Agent
        logger.info(f"查询 {player_name} 的直播状态")
        result = await self.live_monitor.check_player_status(player_name)

        if result.get("is_live"):
            response = self._format_live_status(result)
        else:
            response = f"📺 {player_name} 当前未在直播"

        return {
            "success": True,
            "response": response,
            "data": result,
            "agent_used": "live_monitor"
        }

    def _format_live_status(self, status: Dict) -> str:
        """格式化直播状态"""
        player = status.get("player_name", "未知")
        platform = status.get("platform", "虎牙")
        title = status.get("title", "无标题")
        viewers = status.get("viewer_count", 0)

        response = f"🔴 {player} 正在 {platform} 直播！\n"
        response += f"📝 标题：{title}\n"
        response += f"👥 人气：{viewers:,}\n"

        if status.get("live_url"):
            response += f"🔗 直播间：{status['live_url']}"

        return response

    async def _handle_briefing(self, query: str, entities: Dict) -> Dict[str, Any]:
        """处理简报生成请求"""
        if not self.briefing_agent:
            return {
                "success": False,
                "response": "简报 Agent 未就绪",
                "data": None,
                "agent_used": "router"
            }

        logger.info("生成简报")
        briefing = await self.briefing_agent.generate_briefing()

        return {
            "success": True,
            "response": briefing,
            "data": {"briefing": briefing},
            "agent_used": "briefing"
        }

    def _greeting(self) -> Dict[str, Any]:
        """问候"""
        return {
            "success": True,
            "response": "你好！我是小游探，你的游戏圈 AI 助手 🎮\n\n我可以帮你：\n- 查询主播直播状态（如：Uzi 直播了吗？）\n- 生成游戏圈简报（如：生成今日简报）\n- 分析游戏圈动态\n\n请问有什么可以帮助你的？",
            "data": None,
            "agent_used": "router"
        }

    def _unknown_intent(self) -> Dict[str, Any]:
        """未知意图"""
        return {
            "success": False,
            "response": "抱歉，我不太理解你的请求。可以尝试：\n- \"Uzi 直播了吗？\"\n- \"生成今日简报\"\n- \"最近有什么热点？\"",
            "data": None,
            "agent_used": "router"
        }


# 测试代码
async def test_router_agent():
    """测试 Router Agent"""
    router = RouterAgent()

    # 测试用例
    test_cases = [
        "你好",
        "Uzi 直播了吗",
        "生成今日简报",
        "Faker 在直播吗"
    ]

    for query in test_cases:
        print(f"\n用户: {query}")
        result = await router.process(query)
        print(f"小游探: {result['response']}")


if __name__ == "__main__":
    asyncio.run(test_router_agent())
