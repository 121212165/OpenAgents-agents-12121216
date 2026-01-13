# LiveMonitor Agent - 直播监控 Agent
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime, timedelta

# OpenAgents 导入
from openagents.agents import WorkerAgent

# 导入工具
from src.utils.huya_api import HuyaClient
from src.utils.common import load_yaml_config
from src.utils.data_sources import (
    DataSourceManager, TwitchDataSource, MockDataSource, 
    DataQuery, DataResult
)


class LiveMonitorAgent(WorkerAgent):
    """
    直播监控 Agent - OpenAgents 标准版本

    功能：
    1. 监控虎牙平台主播直播状态
    2. 检测开播/下播事件
    3. 维护主播状态缓存
    4. 提供状态查询接口
    """

    def __init__(self, config_path: str = "config/players.yaml"):
        super().__init__(agent_id="live-monitor-agent")
        
        self.description = "监控游戏主播的直播状态"

        # 加载配置
        self.config = load_yaml_config(config_path)
        self.players = self.config.get("monitored_players", [])

        # 初始化数据源管理器
        self.data_manager = DataSourceManager()
        
        # 添加模拟数据源（用于演示）
        mock_source = MockDataSource()
        self.data_manager.add_source(mock_source)
        
        # 如果有Twitch配置，添加Twitch数据源
        twitch_config = self.config.get("twitch", {})
        if twitch_config.get("client_id") and twitch_config.get("client_secret"):
            twitch_source = TwitchDataSource(
                twitch_config["client_id"],
                twitch_config["client_secret"]
            )
            self.data_manager.add_source(twitch_source)
            logger.info("已添加Twitch数据源")

        # 状态缓存
        self.status_cache: Dict[str, Dict[str, Any]] = {}
        self.last_checked: Dict[str, datetime] = {}

        # 监控配置
        self.polling_intervals = {
            "high": 60,      # 1分钟
            "medium": 300,   # 5分钟
            "low": 900       # 15分钟
        }

        # 后台监控任务
        self.monitor_task = None

        logger.info(f"{self.agent_id} 初始化成功，监控 {len(self.players)} 位主播")

    async def on_startup(self):
        """Agent 启动时调用"""
        logger.info(f"🚀 {self.agent_id} 启动")
        
        # 启动后台监控任务
        self.monitor_task = asyncio.create_task(self.monitor_all_players())
        logger.info("后台监控任务已启动")

    async def on_direct(self, message):
        """处理直接消息"""
        try:
            content = message.get('content', '').strip()
            sender = message.get('sender', '')
            
            if content.startswith('status'):
                # 查询状态命令
                parts = content.split()
                if len(parts) > 1:
                    player_name = parts[1]
                    result = await self.check_player_status(player_name)
                    
                    if result.get("is_live"):
                        response = self._format_live_status(result)
                    else:
                        response = f"📺 {player_name} 当前未在直播"
                else:
                    response = "请指定主播名称，例如：status Uzi"
                
                await self.send_direct(sender, response)
            
            elif content == 'list':
                # 列出所有正在直播的主播
                live_players = await self.get_live_players()
                if live_players:
                    response = "🔴 当前直播中的主播：\n"
                    for player in live_players:
                        response += f"- {player['user_name']}: {player['viewer_count']:,} 观众\n"
                        response += f"  游戏: {player['game_name']}\n"
                        response += f"  平台: {player['platform']}\n\n"
                else:
                    response = "📺 当前没有主播在直播"
                
                await self.send_direct(sender, response)
            
            elif content.startswith('search'):
                # 搜索直播流
                parts = content.split()
                if len(parts) > 1:
                    game_name = ' '.join(parts[1:])
                    streams = await self.search_streams(game_name=game_name)
                    
                    if streams:
                        response = f"🎮 {game_name} 相关直播：\n"
                        for stream in streams[:5]:  # 显示前5个
                            response += f"- {stream['user_name']}: {stream['title']}\n"
                            response += f"  观众: {stream['viewer_count']:,} | 平台: {stream['platform']}\n\n"
                    else:
                        response = f"未找到 {game_name} 相关的直播"
                else:
                    response = "请指定游戏名称，例如：search 英雄联盟"
                
                await self.send_direct(sender, response)
            
            else:
                await self.send_direct(sender, 
                    "可用命令：\n"
                    "- status <主播名>: 查询直播状态\n"
                    "- list: 列出所有直播中的主播\n"
                    "- search <游戏名>: 搜索游戏相关直播"
                )
                
        except Exception as e:
            logger.error(f"处理直接消息失败: {e}")
            await self.send_direct(message.get('sender', ''), f"处理请求时出错：{str(e)}")

    def _format_live_status(self, status: Dict) -> str:
        """格式化直播状态"""
        user_name = status.get("user_name", "未知")
        platform = status.get("platform", "未知平台")
        title = status.get("title", "无标题")
        viewers = status.get("viewer_count", 0)
        game_name = status.get("game_name", "")

        response = f"🔴 {user_name} 正在 {platform} 直播！\n"
        response += f"📝 标题：{title}\n"
        if game_name:
            response += f"🎮 游戏：{game_name}\n"
        response += f"👥 观众：{viewers:,}\n"

        if status.get("live_url"):
            response += f"🔗 直播间：{status['live_url']}"

        return response

    async def check_player_status(self, player_name: str) -> Dict[str, Any]:
        """
        查询指定主播的直播状态

        Args:
            player_name: 主播名称

        Returns:
            {
                "user_name": str,
                "platform": str,
                "is_live": bool,
                "live_url": str,
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
                    "user_name": player_name,
                    "platform": "unknown",
                    "is_live": False,
                    "error": "未找到该主播"
                }

            # 检查缓存（如果距离上次检查不到1分钟，使用缓存）
            cached = self._get_cached_status(player_name)
            if cached:
                logger.info(f"使用缓存的 {player_name} 状态")
                return cached

            # 使用数据源管理器查询
            logger.info(f"查询 {player_name} 的直播状态")
            
            # 尝试通过登录名查询
            login_name = player.get("twitch_login") or player.get("english_name", "").lower()
            if login_name:
                streams = await self.search_streams(user_login=login_name, first=1)
                if streams:
                    status = streams[0]
                    status["checked_at"] = datetime.now()
                    
                    # 更新缓存
                    self._update_cache(player_name, status)
                    return status
            
            # 如果没有找到，尝试使用虎牙API（向后兼容）
            status = await self._fetch_huya_status(player)
            
            # 更新缓存
            self._update_cache(player_name, status)
            return status

        except Exception as e:
            logger.error(f"查询主播状态失败: {e}")
            return {
                "user_name": player_name,
                "platform": "unknown",
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

    async def search_streams(self, game_name: str = None, user_login: str = None, 
                           first: int = 10) -> List[Dict[str, Any]]:
        """
        搜索直播流
        
        Args:
            game_name: 游戏名称
            user_login: 主播登录名
            first: 返回数量
            
        Returns:
            直播流列表
        """
        try:
            # 构建查询参数
            parameters = {"first": first}
            if game_name:
                parameters["game_name"] = game_name
            if user_login:
                parameters["user_login"] = user_login
            
            # 创建查询
            query = DataQuery(
                query_type="streams",
                parameters=parameters,
                cache_ttl=300  # 5分钟缓存
            )
            
            # 执行查询
            result = await self.data_manager.fetch(query)
            
            if result.success:
                logger.info(f"搜索到 {len(result.data)} 个直播流 (来源: {result.source})")
                return [self._convert_stream_data(stream) for stream in result.data]
            else:
                logger.warning(f"搜索直播流失败: {result.error}")
                return []
                
        except Exception as e:
            logger.error(f"搜索直播流异常: {e}")
            return []
    
    def _convert_stream_data(self, stream_data) -> Dict[str, Any]:
        """转换流数据格式"""
        if hasattr(stream_data, '__dict__'):
            # StreamData 对象
            return {
                "user_id": stream_data.user_id,
                "user_name": stream_data.user_name,
                "user_login": stream_data.user_login,
                "title": stream_data.title,
                "game_name": stream_data.game_name,
                "viewer_count": stream_data.viewer_count,
                "is_live": stream_data.is_live,
                "platform": stream_data.platform,
                "live_url": stream_data.live_url,
                "thumbnail_url": stream_data.thumbnail_url,
                "language": stream_data.language,
                "started_at": stream_data.started_at,
                "tags": stream_data.tags
            }
        else:
            # 字典格式
            return stream_data

    async def get_live_players(self) -> List[Dict[str, Any]]:
        """获取当前正在直播的主播列表"""
        try:
            # 获取配置中的主播列表
            player_logins = [player.get("twitch_login") or player.get("english_name", "").lower() 
                           for player in self.players if player.get("twitch_login") or player.get("english_name")]
            
            if not player_logins:
                # 如果没有配置特定主播，获取热门直播
                streams = await self.search_streams(first=20)
                return streams
            
            # 查询特定主播
            streams = await self.search_streams(user_login=player_logins, first=50)
            
            # 按观众数排序
            streams.sort(key=lambda x: x.get("viewer_count", 0), reverse=True)
            
            return streams
            
        except Exception as e:
            logger.error(f"获取直播主播列表失败: {e}")
            return []

    def _find_player(self, player_name: str) -> Optional[Dict]:
        """查找主播配置"""
        for player in self.players:
            if player.get("name") == player_name or player.get("english_name") == player_name:
                return player
        return None

    async def _fetch_huya_status(self, player: Dict) -> Dict[str, Any]:
        """从虎牙获取直播状态（向后兼容）"""
        player_name = player.get("name")
        huya_id = player.get("huya_id")

        if not huya_id:
            return {
                "user_name": player_name,
                "platform": "虎牙",
                "is_live": False,
                "error": "未配置虎牙房间号"
            }

        try:
            async with HuyaClient() as client:
                result = await client.get_live_status(huya_id)

                # 转换为新格式
                return {
                    "user_name": player_name,
                    "user_login": player_name.lower(),
                    "platform": "虎牙",
                    "is_live": result.get("is_live", False),
                    "title": result.get("title", ""),
                    "viewer_count": result.get("viewer_count", 0),
                    "live_url": result.get("live_url", ""),
                    "game_name": result.get("game_name", ""),
                    "checked_at": datetime.now()
                }

        except Exception as e:
            logger.error(f"获取虎牙状态失败: {e}")
            return {
                "user_name": player_name,
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

    async def on_shutdown(self):
        """Agent 关闭时调用"""
        logger.info(f"🛑 {self.agent_id} 关闭")
        
        # 取消后台监控任务
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                logger.info("后台监控任务已取消")


# 测试代码
async def test_live_monitor():
    """测试直播监控"""
    monitor = LiveMonitorAgent()
    
    await monitor.on_startup()

    # 测试查询状态
    result = await monitor.check_player_status("Uzi")
    print(f"Uzi 状态: {result}")

    # 获取所有正在直播的主播
    live_players = await monitor.get_live_players()
    print(f"\n当前直播中: {len(live_players)} 人")
    for player in live_players[:3]:  # 只显示前3个
        print(f"- {player['user_name']}: {player['viewer_count']:,} 观众")
        print(f"  游戏: {player['game_name']} | 平台: {player['platform']}")
    
    # 测试搜索功能
    print(f"\n搜索英雄联盟相关直播:")
    lol_streams = await monitor.search_streams(game_name="英雄联盟", first=3)
    for stream in lol_streams:
        print(f"- {stream['user_name']}: {stream['title']}")
        print(f"  观众: {stream['viewer_count']:,} | 平台: {stream['platform']}")
    
    await monitor.on_shutdown()


if __name__ == "__main__":
    asyncio.run(test_live_monitor())
