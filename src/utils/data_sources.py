# 数据源抽象层
"""
数据源抽象层实现
支持多数据源管理、故障切换、缓存等功能
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger

class DataSourceType(Enum):
    """数据源类型"""
    TWITCH = "twitch"
    HUYA = "huya"
    MOCK = "mock"
    CACHE = "cache"

class DataSourceStatus(Enum):
    """数据源状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class StreamData:
    """统一的直播流数据格式"""
    user_id: str
    user_name: str
    user_login: str
    title: str
    game_name: str
    viewer_count: int
    is_live: bool
    platform: str
    live_url: str
    thumbnail_url: str = ""
    language: str = "zh"
    started_at: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class DataQuery:
    """数据查询请求"""
    query_type: str  # "streams", "user", "game", etc.
    parameters: Dict[str, Any]
    cache_ttl: int = 300  # 缓存时间（秒）
    timeout: int = 10     # 请求超时（秒）

@dataclass
class DataResult:
    """数据查询结果"""
    success: bool
    data: Any
    source: str
    cached: bool = False
    timestamp: datetime = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, source_type: DataSourceType, name: str):
        self.source_type = source_type
        self.name = name
        self.status = DataSourceStatus.UNKNOWN
        self.last_check = None
        self.error_count = 0
        self.max_errors = 3
        
    @abstractmethod
    async def fetch(self, query: DataQuery) -> DataResult:
        """获取数据"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    def is_healthy(self) -> bool:
        """检查数据源是否健康"""
        return self.status == DataSourceStatus.HEALTHY
    
    def mark_error(self):
        """标记错误"""
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.status = DataSourceStatus.FAILED
        else:
            self.status = DataSourceStatus.DEGRADED
    
    def mark_success(self):
        """标记成功"""
        self.error_count = 0
        self.status = DataSourceStatus.HEALTHY

class TwitchDataSource(DataSource):
    """Twitch数据源"""
    
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(DataSourceType.TWITCH, "Twitch API")
        self.client_id = client_id
        self.client_secret = client_secret
        self.client = None
    
    async def _get_client(self):
        """获取Twitch客户端"""
        if not self.client:
            try:
                from .twitch_api import TwitchAPIClient
            except ImportError:
                from src.utils.twitch_api import TwitchAPIClient
            self.client = TwitchAPIClient(self.client_id, self.client_secret)
        return self.client
    
    async def fetch(self, query: DataQuery) -> DataResult:
        """获取Twitch数据"""
        try:
            client = await self._get_client()
            
            if query.query_type == "streams":
                async with client:
                    streams = await client.get_streams(**query.parameters)
                    
                    # 转换为统一格式
                    stream_data = []
                    for stream in streams:
                        data = StreamData(
                            user_id=stream.user_id,
                            user_name=stream.user_name,
                            user_login=stream.user_login,
                            title=stream.title,
                            game_name=stream.game_name,
                            viewer_count=stream.viewer_count,
                            is_live=True,
                            platform="Twitch",
                            live_url=f"https://twitch.tv/{stream.user_login}",
                            thumbnail_url=stream.thumbnail_url,
                            language=stream.language,
                            started_at=stream.started_at
                        )
                        stream_data.append(data)
                    
                    self.mark_success()
                    return DataResult(
                        success=True,
                        data=stream_data,
                        source=self.name
                    )
            
            elif query.query_type == "user":
                async with client:
                    user = await client.get_user_by_login(query.parameters.get("login"))
                    self.mark_success()
                    return DataResult(
                        success=True,
                        data=user,
                        source=self.name
                    )
            
            else:
                return DataResult(
                    success=False,
                    data=None,
                    source=self.name,
                    error=f"Unsupported query type: {query.query_type}"
                )
                
        except Exception as e:
            self.mark_error()
            logger.error(f"Twitch数据源错误: {e}")
            return DataResult(
                success=False,
                data=None,
                source=self.name,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """Twitch健康检查"""
        try:
            query = DataQuery(
                query_type="streams",
                parameters={"first": 1}
            )
            result = await self.fetch(query)
            return result.success
        except Exception:
            return False

class MockDataSource(DataSource):
    """模拟数据源"""
    
    def __init__(self):
        super().__init__(DataSourceType.MOCK, "Mock Data")
        self.status = DataSourceStatus.HEALTHY  # 模拟数据源总是健康的
        
        # 使用新的模拟数据生成器
        try:
            from .mock_data import mock_generator
            self.generator = mock_generator
        except ImportError:
            try:
                # 尝试绝对导入
                from src.utils.mock_data import mock_generator
                self.generator = mock_generator
            except ImportError:
                # 如果无法导入，使用简单的模拟数据
                logger.warning("无法导入mock_data模块，使用简单模拟数据")
                self.generator = None
        
    async def fetch(self, query: DataQuery) -> DataResult:
        """获取模拟数据"""
        try:
            if query.query_type == "streams":
                # 根据查询参数生成数据
                params = query.parameters
                
                if self.generator:
                    # 使用高级模拟数据生成器
                    user_logins = params.get("user_login", [])
                    if isinstance(user_logins, str):
                        user_logins = [user_logins]
                    
                    game_names = params.get("game_name", [])
                    if isinstance(game_names, str):
                        game_names = [game_names]
                    
                    first = params.get("first", 10)
                    
                    # 生成直播流数据
                    mock_streams = self.generator.generate_live_streams(
                        count=first,
                        specific_streamers=user_logins if user_logins else None,
                        specific_games=game_names if game_names else None
                    )
                    
                    # 转换为StreamData格式
                    stream_data = []
                    for stream in mock_streams:
                        data = StreamData(
                            user_id=stream["user_id"],
                            user_name=stream["user_name"],
                            user_login=stream["user_login"],
                            title=stream["title"],
                            game_name=stream["game_name"],
                            viewer_count=stream["viewer_count"],
                            is_live=stream["is_live"],
                            platform=stream["platform"],
                            live_url=stream["live_url"],
                            thumbnail_url=stream["thumbnail_url"],
                            language=stream["language"],
                            started_at=stream["started_at"],
                            tags=stream["tags"]
                        )
                        stream_data.append(data)
                else:
                    # 使用简单的模拟数据
                    stream_data = [
                        StreamData(
                            user_id="mock_1",
                            user_name="Faker",
                            user_login="faker",
                            title="T1 Faker - Solo Queue Climb",
                            game_name="League of Legends",
                            viewer_count=45000,
                            is_live=True,
                            platform="Twitch",
                            live_url="https://twitch.tv/faker",
                            language="ko",
                            started_at="2026-01-10T10:00:00Z"
                        ),
                        StreamData(
                            user_id="mock_2",
                            user_name="Doublelift",
                            user_login="doublelift",
                            title="ADC Gameplay and Commentary",
                            game_name="League of Legends",
                            viewer_count=12000,
                            is_live=True,
                            platform="Twitch",
                            live_url="https://twitch.tv/doublelift",
                            language="en",
                            started_at="2026-01-10T11:30:00Z"
                        )
                    ]
                
                return DataResult(
                    success=True,
                    data=stream_data,
                    source=self.name
                )
            
            elif query.query_type == "user":
                login = query.parameters.get("login")
                
                if self.generator:
                    streamer = self.generator.get_streamer_by_login(login)
                    if streamer:
                        user_data = {
                            "id": streamer.user_id,
                            "login": streamer.user_login,
                            "display_name": streamer.user_name,
                            "description": streamer.description,
                            "profile_image_url": streamer.profile_image_url,
                            "follower_count": streamer.follower_count,
                            "is_partner": streamer.is_partner
                        }
                        return DataResult(
                            success=True,
                            data=user_data,
                            source=self.name
                        )
                
                # 简单模拟数据
                if login in ["faker", "doublelift"]:
                    user_data = {
                        "id": f"mock_{login}",
                        "login": login,
                        "display_name": login.title(),
                        "description": f"Mock user {login}"
                    }
                    return DataResult(
                        success=True,
                        data=user_data,
                        source=self.name
                    )
                
                return DataResult(
                    success=False,
                    data=None,
                    source=self.name,
                    error="User not found"
                )
            
            elif query.query_type == "trending":
                if self.generator:
                    # 生成热门话题
                    topics = self.generator.generate_trending_topics()
                    return DataResult(
                        success=True,
                        data=topics,
                        source=self.name
                    )
                else:
                    # 简单热门话题
                    topics = [
                        {"topic": "世界赛决赛", "mentions": 45000},
                        {"topic": "新英雄上线", "mentions": 28000}
                    ]
                    return DataResult(
                        success=True,
                        data=topics,
                        source=self.name
                    )
            
            else:
                return DataResult(
                    success=False,
                    data=None,
                    source=self.name,
                    error=f"Unsupported query type: {query.query_type}"
                )
                
        except Exception as e:
            logger.error(f"模拟数据源错误: {e}")
            return DataResult(
                success=False,
                data=None,
                source=self.name,
                error=str(e)
            )
    
    async def health_check(self) -> bool:
        """模拟数据源健康检查"""
        return True  # 模拟数据源总是健康的

class CacheDataSource(DataSource):
    """缓存数据源"""
    
    def __init__(self):
        super().__init__(DataSourceType.CACHE, "Cache")
        self.cache: Dict[str, Dict] = {}
        self.status = DataSourceStatus.HEALTHY
    
    def _get_cache_key(self, query: DataQuery) -> str:
        """生成缓存键"""
        return f"{query.query_type}:{hash(json.dumps(query.parameters, sort_keys=True))}"
    
    async def fetch(self, query: DataQuery) -> DataResult:
        """从缓存获取数据"""
        cache_key = self._get_cache_key(query)
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            
            # 检查是否过期
            if datetime.now() - cached_item["timestamp"] < timedelta(seconds=query.cache_ttl):
                return DataResult(
                    success=True,
                    data=cached_item["data"],
                    source=self.name,
                    cached=True,
                    timestamp=cached_item["timestamp"]
                )
            else:
                # 清理过期缓存
                del self.cache[cache_key]
        
        return DataResult(
            success=False,
            data=None,
            source=self.name,
            error="Cache miss"
        )
    
    async def store(self, query: DataQuery, data: Any):
        """存储数据到缓存"""
        cache_key = self._get_cache_key(query)
        self.cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }
        logger.debug(f"数据已缓存: {cache_key}")
    
    async def health_check(self) -> bool:
        """缓存健康检查"""
        return True

class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.sources: List[DataSource] = []
        self.cache_source = CacheDataSource()
        self.fallback_enabled = True
        
    def add_source(self, source: DataSource):
        """添加数据源"""
        self.sources.append(source)
        logger.info(f"添加数据源: {source.name}")
    
    def remove_source(self, source: DataSource):
        """移除数据源"""
        if source in self.sources:
            self.sources.remove(source)
            logger.info(f"移除数据源: {source.name}")
    
    async def fetch(self, query: DataQuery) -> DataResult:
        """获取数据（支持故障切换）"""
        # 1. 尝试从缓存获取
        cache_result = await self.cache_source.fetch(query)
        if cache_result.success:
            logger.debug(f"缓存命中: {query.query_type}")
            return cache_result
        
        # 2. 尝试从各个数据源获取
        for source in self.sources:
            if not source.is_healthy() and self.fallback_enabled:
                logger.warning(f"跳过不健康的数据源: {source.name}")
                continue
            
            try:
                logger.debug(f"尝试数据源: {source.name}")
                result = await asyncio.wait_for(
                    source.fetch(query), 
                    timeout=query.timeout
                )
                
                if result.success:
                    # 缓存成功的结果
                    await self.cache_source.store(query, result.data)
                    logger.info(f"数据获取成功: {source.name}")
                    return result
                else:
                    logger.warning(f"数据源返回失败: {source.name} - {result.error}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"数据源超时: {source.name}")
                source.mark_error()
            except Exception as e:
                logger.error(f"数据源异常: {source.name} - {e}")
                source.mark_error()
        
        # 3. 所有数据源都失败，返回失败结果
        return DataResult(
            success=False,
            data=None,
            source="None",
            error="All data sources failed"
        )
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有数据源健康状态"""
        results = {}
        
        for source in self.sources:
            try:
                is_healthy = await source.health_check()
                results[source.name] = is_healthy
                
                if is_healthy:
                    source.mark_success()
                else:
                    source.mark_error()
                    
            except Exception as e:
                logger.error(f"健康检查失败: {source.name} - {e}")
                results[source.name] = False
                source.mark_error()
        
        return results
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据源状态"""
        status = {}
        
        for source in self.sources:
            status[source.name] = {
                "type": source.source_type.value,
                "status": source.status.value,
                "error_count": source.error_count,
                "last_check": source.last_check.isoformat() if source.last_check else None
            }
        
        return status

# 测试代码
async def test_data_sources():
    """测试数据源管理器"""
    manager = DataSourceManager()
    
    # 添加模拟数据源
    mock_source = MockDataSource()
    manager.add_source(mock_source)
    
    # 测试查询
    query = DataQuery(
        query_type="streams",
        parameters={"user_login": ["faker", "doublelift"], "first": 5}
    )
    
    print("测试数据源管理器...")
    result = await manager.fetch(query)
    
    if result.success:
        print(f"✅ 数据获取成功 (来源: {result.source})")
        print(f"   获取到 {len(result.data)} 条直播数据")
        for stream in result.data[:3]:
            print(f"   - {stream.user_name}: {stream.title} ({stream.viewer_count} 观众)")
    else:
        print(f"❌ 数据获取失败: {result.error}")
    
    # 测试健康检查
    print("\n健康检查结果:")
    health_status = await manager.health_check_all()
    for source_name, is_healthy in health_status.items():
        status = "✅ 健康" if is_healthy else "❌ 异常"
        print(f"   {source_name}: {status}")

if __name__ == "__main__":
    asyncio.run(test_data_sources())