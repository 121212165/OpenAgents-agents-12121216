# DataSource Agent - 带缓存支持的数据源代理
"""
增强版DataSource Agent，集成了缓存管理器以优化性能
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from datetime import datetime
from dataclasses import dataclass
import hashlib

# OpenAgents 导入
from openagents.agents import WorkerAgent

# 导入数据源管理器
try:
    from src.utils.data_sources import DataSourceManager, DataQuery, DataResult
    from src.utils.llm_client import llm_client
    from src.utils.cache_manager import global_cache, CACHE_CONFIG
except ImportError:
    from utils.data_sources import DataSourceManager, DataQuery, DataResult
    from utils.llm_client import llm_client
    from utils.cache_manager import global_cache, CACHE_CONFIG


@dataclass
class QueryRequest:
    """查询请求"""
    query_type: str
    parameters: Dict[str, Any]
    requester: str
    priority: int = 1
    timeout: float = 10.0


@dataclass
class QueryResponse:
    """查询响应"""
    success: bool
    data: Any
    source: str
    cached: bool = False
    processing_time: float = 0.0
    error: Optional[str] = None


class DataSourceAgentCached(WorkerAgent):
    """
    带缓存的数据源代理
    
    在原DataSourceAgent基础上增加了：
    1. 智能缓存管理
    2. 缓存命中率统计
    3. 自动缓存失效
    """
    
    def __init__(self):
        super().__init__(agent_id="datasource-agent-cached")
        
        self.description = "带缓存优化的统一数据源管理服务"
        self.capabilities = [
            "data_query",
            "cached_queries",
            "source_management",
            "performance_monitoring"
        ]
        
        # 初始化数据源管理器
        self.data_manager = DataSourceManager()
        
        # 缓存统计
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
        
        logger.info(f"{self.agent_id} 初始化成功 - 缓存优化版")
    
    async def on_startup(self):
        """Agent启动"""
        await global_cache.start()
        logger.info(f"{self.agent_id} 启动 - 缓存管理器已就绪")
    
    async def on_shutdown(self):
        """Agent关闭"""
        await global_cache.stop()
        logger.info(f"{self.agent_id} 关闭 - 缓存管理器已停止")
    
    def _generate_cache_key(self, query_type: str, **params) -> str:
        """生成缓存键"""
        key_data = f"{query_type}:{sorted(params.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _get_cached_or_query(self, cache_key: str, query_func, ttl: int = 300) -> Any:
        """从缓存获取或执行查询"""
        self.cache_stats["total_requests"] += 1
        
        # 尝试从缓存获取
        cached_value = global_cache.get(cache_key)
        if cached_value is not None:
            self.cache_stats["hits"] += 1
            logger.debug(f"缓存命中: {cache_key}")
            return cached_value, True
        
        # 缓存未命中，执行查询
        self.cache_stats["misses"] += 1
        result = await query_func()
        
        # 存入缓存
        await global_cache.set(cache_key, result, ttl)
        logger.debug(f"查询完成并缓存: {cache_key}")
        
        return result, False
    
    async def get_live_streams(self, game_name: str = None, user_login: str = None, 
                               first: int = 10) -> QueryResponse:
        """
        获取直播流列表（带缓存）
        
        Args:
            game_name: 游戏名称
            user_login: 用户登录名
            first: 返回数量
        """
        start_time = datetime.now()
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                "live_streams",
                game=game_name,
                user=user_login,
                count=first
            )
            
            # 定义查询函数
            async def query_func():
                return await self.data_manager.query_streams(
                    game_name=game_name,
                    user_login=user_login,
                    first=first
                )
            
            # 从缓存获取或查询（60秒TTL）
            data, was_cached = await self._get_cached_or_query(
                cache_key,
                query_func,
                ttl=60  # 直播数据缓存60秒
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResponse(
                success=True,
                data=data,
                source=data.get('source', 'unknown') if isinstance(data, dict) else 'cached',
                cached=was_cached,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"获取直播流失败: {e}")
            
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                cached=False,
                processing_time=processing_time,
                error=str(e)
            )
    
    async def get_trending_data(self) -> QueryResponse:
        """
        获取热门数据（带缓存）
        """
        start_time = datetime.now()
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key("trending")
            
            # 定义查询函数
            async def query_func():
                return await self.data_manager.query_trending()
            
            # 从缓存获取或查询（300秒TTL = 5分钟）
            data, was_cached = await self._get_cached_or_query(
                cache_key,
                query_func,
                ttl=300  # 趋势数据缓存5分钟
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResponse(
                success=True,
                data=data,
                source=data.get('source', 'unknown') if isinstance(data, dict) else 'cached',
                cached=was_cached,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"获取热门数据失败: {e}")
            
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                cached=False,
                processing_time=processing_time,
                error=str(e)
            )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        stats = self.cache_stats.copy()
        if stats["total_requests"] > 0:
            stats["hit_rate"] = f"{stats['hits'] / stats['total_requests']:.2%}"
        else:
            stats["hit_rate"] = "0%"
        return stats
    
    async def clear_cache(self):
        """清空缓存"""
        global_cache.clear()
        logger.info("缓存已清空")


# 使用示例
if __name__ == "__main__":
    async def test():
        agent = DataSourceAgentCached()
        await agent.on_startup()
        
        # 第一次查询（会访问数据源）
        result1 = await agent.get_live_streams(game_name="英雄联盟")
        print(f"第一次查询: cached={result1.cached}, time={result1.processing_time:.3f}s")
        
        # 第二次查询（会使用缓存）
        result2 = await agent.get_live_streams(game_name="英雄联盟")
        print(f"第二次查询: cached={result2.cached}, time={result2.processing_time:.3f}s")
        
        print(f"\n缓存统计: {agent.get_cache_stats()}")
        
        await agent.on_shutdown()
    
    asyncio.run(test())
