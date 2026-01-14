# Twitch API 客户端
"""
Twitch API 客户端实现
支持获取直播流信息、游戏信息等
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass

@dataclass
class TwitchStream:
    """Twitch直播流信息"""
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    title: str
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    is_mature: bool

@dataclass
class TwitchGame:
    """Twitch游戏信息"""
    id: str
    name: str
    box_art_url: str
    igdb_id: Optional[str] = None

class TwitchAPIClient:
    """Twitch API 客户端"""
    
    BASE_URL = "https://api.twitch.tv/helix"
    
    def __init__(self, client_id: str, client_secret: str):
        """
        初始化Twitch API客户端
        
        Args:
            client_id: Twitch应用的Client ID
            client_secret: Twitch应用的Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self.session = None
        
        logger.info("Twitch API客户端初始化")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        await self._ensure_valid_token()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _ensure_valid_token(self):
        """确保访问令牌有效"""
        if not self.access_token or self._is_token_expired():
            await self._get_app_access_token()
    
    def _is_token_expired(self) -> bool:
        """检查令牌是否过期"""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at
    
    async def _get_app_access_token(self):
        """获取应用访问令牌"""
        url = "https://id.twitch.tv/oauth2/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        try:
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data["expires_in"]
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 提前5分钟刷新
                    logger.info("Twitch访问令牌获取成功")
                else:
                    error_text = await response.text()
                    logger.error(f"获取Twitch访问令牌失败: {response.status} - {error_text}")
                    raise Exception(f"Failed to get Twitch access token: {response.status}")
        except Exception as e:
            logger.error(f"Twitch令牌请求异常: {e}")
            raise
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发起API请求"""
        await self._ensure_valid_token()
        
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Twitch API请求失败: {response.status} - {error_text}")
                    raise Exception(f"Twitch API request failed: {response.status}")
        except Exception as e:
            logger.error(f"Twitch API请求异常: {e}")
            raise
    
    async def get_streams(self, 
                         user_login: List[str] = None,
                         user_id: List[str] = None,
                         game_id: List[str] = None,
                         language: List[str] = None,
                         first: int = 20) -> List[TwitchStream]:
        """
        获取直播流信息
        
        Args:
            user_login: 用户登录名列表
            user_id: 用户ID列表
            game_id: 游戏ID列表
            language: 语言列表
            first: 返回结果数量限制
            
        Returns:
            直播流信息列表
        """
        params = {"first": min(first, 100)}  # API限制最多100个
        
        if user_login:
            params["user_login"] = user_login
        if user_id:
            params["user_id"] = user_id
        if game_id:
            params["game_id"] = game_id
        if language:
            params["language"] = language
        
        try:
            response = await self._make_request("streams", params)
            streams = []
            
            for stream_data in response.get("data", []):
                stream = TwitchStream(
                    user_id=stream_data["user_id"],
                    user_login=stream_data["user_login"],
                    user_name=stream_data["user_name"],
                    game_id=stream_data["game_id"],
                    game_name=stream_data["game_name"],
                    title=stream_data["title"],
                    viewer_count=stream_data["viewer_count"],
                    started_at=stream_data["started_at"],
                    language=stream_data["language"],
                    thumbnail_url=stream_data["thumbnail_url"],
                    is_mature=stream_data["is_mature"]
                )
                streams.append(stream)
            
            logger.info(f"获取到 {len(streams)} 个直播流")
            return streams
            
        except Exception as e:
            logger.error(f"获取直播流失败: {e}")
            return []
    
    async def get_user_by_login(self, login: str) -> Optional[Dict[str, Any]]:
        """
        根据登录名获取用户信息
        
        Args:
            login: 用户登录名
            
        Returns:
            用户信息字典或None
        """
        try:
            response = await self._make_request("users", {"login": login})
            users = response.get("data", [])
            return users[0] if users else None
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    async def get_games(self, game_ids: List[str] = None, names: List[str] = None) -> List[TwitchGame]:
        """
        获取游戏信息
        
        Args:
            game_ids: 游戏ID列表
            names: 游戏名称列表
            
        Returns:
            游戏信息列表
        """
        params = {}
        if game_ids:
            params["id"] = game_ids
        if names:
            params["name"] = names
        
        try:
            response = await self._make_request("games", params)
            games = []
            
            for game_data in response.get("data", []):
                game = TwitchGame(
                    id=game_data["id"],
                    name=game_data["name"],
                    box_art_url=game_data["box_art_url"],
                    igdb_id=game_data.get("igdb_id")
                )
                games.append(game)
            
            logger.info(f"获取到 {len(games)} 个游戏信息")
            return games
            
        except Exception as e:
            logger.error(f"获取游戏信息失败: {e}")
            return []
    
    async def get_top_games(self, first: int = 20) -> List[TwitchGame]:
        """
        获取热门游戏
        
        Args:
            first: 返回结果数量
            
        Returns:
            热门游戏列表
        """
        params = {"first": min(first, 100)}
        
        try:
            response = await self._make_request("games/top", params)
            games = []
            
            for game_data in response.get("data", []):
                game = TwitchGame(
                    id=game_data["id"],
                    name=game_data["name"],
                    box_art_url=game_data["box_art_url"],
                    igdb_id=game_data.get("igdb_id")
                )
                games.append(game)
            
            logger.info(f"获取到 {len(games)} 个热门游戏")
            return games
            
        except Exception as e:
            logger.error(f"获取热门游戏失败: {e}")
            return []
    
    async def search_categories(self, query: str, first: int = 20) -> List[TwitchGame]:
        """
        搜索游戏分类
        
        Args:
            query: 搜索关键词
            first: 返回结果数量
            
        Returns:
            匹配的游戏列表
        """
        params = {
            "query": query,
            "first": min(first, 100)
        }
        
        try:
            response = await self._make_request("search/categories", params)
            games = []
            
            for game_data in response.get("data", []):
                game = TwitchGame(
                    id=game_data["id"],
                    name=game_data["name"],
                    box_art_url=game_data["box_art_url"]
                )
                games.append(game)
            
            logger.info(f"搜索到 {len(games)} 个游戏")
            return games
            
        except Exception as e:
            logger.error(f"搜索游戏失败: {e}")
            return []

# 测试代码
async def test_twitch_api():
    """测试Twitch API客户端"""
    # 注意：需要真实的Twitch API凭据才能测试
    # 这里使用模拟凭据进行基础测试
    
    client_id = "your_client_id"
    client_secret = "your_client_secret"
    
    try:
        async with TwitchAPIClient(client_id, client_secret) as client:
            # 测试获取热门游戏
            print("获取热门游戏...")
            top_games = await client.get_top_games(5)
            for game in top_games:
                print(f"- {game.name} (ID: {game.id})")
            
            # 测试搜索游戏
            print("\n搜索'League'相关游戏...")
            search_results = await client.search_categories("League", 3)
            for game in search_results:
                print(f"- {game.name}")
            
            # 测试获取直播流（需要真实用户名）
            print("\n获取直播流...")
            streams = await client.get_streams(user_login=["ninja", "shroud"], first=5)
            for stream in streams:
                print(f"- {stream.user_name}: {stream.title} ({stream.viewer_count} 观众)")
                
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_twitch_api())