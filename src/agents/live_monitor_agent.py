# LiveMonitor Agent - 直播监控 Agent
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime, timedelta

# 尝试导入 OpenAgents
try:
    from openagents import WorkerAgent
    OPENAGENTS_AVAILABLE = True
except ImportError:
    logger.warning("OpenAgents SDK 未安装，使用模拟模式")
    OPENAGENTS_AVAILABLE = False
    WorkerAgent = object

# 导入工具
from src.utils.huya_api import HuyaClient
from src.utils.common import load_yaml_config


class LiveMonitorAgent(WorkerAgent if OPENAGENTS_AVAILABLE else object):
    """
    直播监控 Agent

    功能：
    1. 监控虎牙平台主播直播状态
    2. 检测开播/下播事件
    3. 维护主播状态缓存
    4. 提供状态查询接口
    """

    def __init__(self, config_path: str = "config/players.yaml"):
        self.name = "LiveMonitor Agent"
        self.description = "监控游戏主播的直播状态"

        # 加载配置
        self.config = load_yaml_config(config_path)
        self.players = self.config.get("monitored_players", [])

        # 状态缓存
        self.status_cache: Dict[str, Dict[str, Any]] = {}
        self.last_checked: Dict[str, datetime] = {}

        # 监控配置
        self.polling_intervals = {
            "high": 60,      # 1分钟
            "medium": 300,   # 5分钟
            "low": 900       # 15分钟
        }

        logger.info(f"{self.name} 初始化成功，监控 {len(self.players)} 位主播")

    async def check_player_status(self, player_name: str) -> Dict[str, Any]:
        """
        查询指定主播的直播状态

        Args:
            player_name: 主播名称

        Returns:
            {
                "player_name": str,
                "platform": str,
                "is_live": bool,
                "room_url": str,
                "title": str,
                "viewer_count": int,
                "checked_at": datetime
            }
        """
        try:
            # 查找主播配置
            player = self._find_player(player_name)
            if not player:
                return {
                    "player_name": player_name,
                    "platform": "unknown",
                    "is_live": False,
                    "error": "未找到该主播"
                }

            # 检查缓存（如果距离上次检查不到1分钟，使用缓存）
            cached = self._get_cached_status(player_name)
            if cached:
                logger.info(f"使用缓存的 {player_name} 状态")
                return cached

            # 调用 API 获取最新状态
            logger.info(f"查询 {player_name} 的直播状态")
            status = await self._fetch_huya_status(player)

            # 更新缓存
            self._update_cache(player_name, status)

            return status

        except Exception as e:
            logger.error(f"查询主播状态失败: {e}")
            return {
                "player_name": player_name,
                "platform": "huya",
                "is_live": False,
                "error": str(e)
            }

    async def monitor_all_players(self):
        """监控所有主播（后台任务）"""
        logger.info("开始监控所有主播...")

        while True:
            try:
                for player in self.players:
                    player_name = player.get("name")

                    # 检查是否需要更新
                    if self._should_check(player_name):
                        logger.info(f"检查 {player_name} 的状态")
                        await self.check_player_status(player_name)

                # 等待下一次轮询
                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"监控任务出错: {e}")
                await asyncio.sleep(60)

    async def get_live_players(self) -> List[Dict[str, Any]]:
        """获取当前正在直播的主播列表"""
        live_players = []

        for player in self.players:
            player_name = player.get("name")
            status = self.status_cache.get(player_name, {})

            if status.get("is_live"):
                live_players.append({
                    "player_name": player_name,
                    "platform": "虎牙",
                    "viewer_count": status.get("viewer_count", 0),
                    "title": status.get("title", ""),
                    "live_url": status.get("live_url", "")
                })

        # 按人气排序
        live_players.sort(key=lambda x: x.get("viewer_count", 0), reverse=True)

        return live_players

    def _find_player(self, player_name: str) -> Optional[Dict]:
        """查找主播配置"""
        for player in self.players:
            if player.get("name") == player_name or player.get("english_name") == player_name:
                return player
        return None

    async def _fetch_huya_status(self, player: Dict) -> Dict[str, Any]:
        """从虎牙获取直播状态"""
        player_name = player.get("name")
        huya_id = player.get("huya_id")

        if not huya_id:
            return {
                "player_name": player_name,
                "platform": "虎牙",
                "is_live": False,
                "error": "未配置虎牙房间号"
            }

        try:
            async with HuyaClient() as client:
                result = await client.get_live_status(huya_id)

                # 补充主播信息
                result["player_name"] = player_name
                result["platform"] = "虎牙"

                return result

        except Exception as e:
            logger.error(f"获取虎牙状态失败: {e}")
            return {
                "player_name": player_name,
                "platform": "虎牙",
                "is_live": False,
                "error": str(e)
            }

    def _get_cached_status(self, player_name: str) -> Optional[Dict]:
        """获取缓存的状态"""
        cached = self.status_cache.get(player_name)
        if not cached:
            return None

        last_checked = self.last_checked.get(player_name)
        if not last_checked:
            return None

        # 缓存有效期1分钟
        if datetime.now() - last_checked > timedelta(minutes=1):
            return None

        return cached

    def _update_cache(self, player_name: str, status: Dict):
        """更新缓存"""
        self.status_cache[player_name] = status
        self.last_checked[player_name] = datetime.now()

    def _should_check(self, player_name: str) -> bool:
        """判断是否需要检查"""
        player = self._find_player(player_name)
        if not player:
            return False

        priority = player.get("priority", "medium")
        interval = self.polling_intervals.get(priority, 300)

        last_checked = self.last_checked.get(player_name)
        if not last_checked:
            return True

        return datetime.now() - last_checked > timedelta(seconds=interval)


# 测试代码
async def test_live_monitor():
    """测试直播监控"""
    monitor = LiveMonitorAgent()

    # 测试查询状态
    result = await monitor.check_player_status("Uzi")
    print(f"Uzi 状态: {result}")

    # 获取所有正在直播的主播
    live_players = await monitor.get_live_players()
    print(f"\n当前直播中: {len(live_players)} 人")
    for player in live_players:
        print(f"- {player['player_name']}: {player['viewer_count']} 人气")


if __name__ == "__main__":
    asyncio.run(test_live_monitor())
