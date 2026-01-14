# 缓存优化模块
"""
缓存优化模块 - 提升系统响应速度

功能：
1. 智能查询缓存
2. LLM响应缓存
3. 数据源结果缓存
4. 缓存预热和失效策略
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Callable, Tuple, List
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
from loguru import logger


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0
        }
        
        logger.info(f"LRU缓存初始化 - 最大容量: {max_size}, 默认TTL: {default_ttl}s")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        
        # 检查是否过期
        if entry.expires_at and datetime.now() > entry.expires_at:
            self.stats["expired"] += 1
            self.stats["misses"] += 1
            del self.cache[key]
            return None
        
        # 更新访问信息
        entry.hit_count += 1
        entry.last_accessed = datetime.now()
        
        # 移到末尾（最近使用）
        self.cache.move_to_end(key)
        
        self.stats["hits"] += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        # 计算过期时间
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        # 计算大小（粗略估计）
        try:
            size_bytes = len(json.dumps(value, default=str).encode())
        except:
            size_bytes = 0
        
        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            size_bytes=size_bytes
        )
        
        # 如果键已存在，更新
        if key in self.cache:
            self.cache[key] = entry
            self.cache.move_to_end(key)
        else:
            # 检查容量
            if len(self.cache) >= self.max_size:
                # 移除最旧的条目
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats["evictions"] += 1
            
            self.cache[key] = entry
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        total_size = sum(entry.size_bytes for entry in self.cache.values())
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "evictions": self.stats["evictions"],
            "expired": self.stats["expired"],
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }
    
    def cleanup_expired(self):
        """清理过期条目"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.expires_at and now > entry.expires_at
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["expired"] += 1
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存条目")


class QueryCache:
    """查询缓存 - 针对用户查询优化"""
    
    def __init__(self, max_size: int = 500, default_ttl: int = 300):
        self.cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self.query_patterns = {}  # 查询模式统计
        
        logger.info("查询缓存初始化")
    
    def _normalize_query(self, query: str) -> str:
        """规范化查询"""
        # 转小写，去除多余空格
        normalized = query.lower().strip()
        normalized = " ".join(normalized.split())
        return normalized
    
    def _generate_query_key(self, query: str, context: Optional[Dict] = None) -> str:
        """生成查询缓存键"""
        normalized_query = self._normalize_query(query)
        
        key_data = {
            "query": normalized_query,
            "context": str(sorted(context.items())) if context else ""
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query: str, context: Optional[Dict] = None) -> Optional[Any]:
        """获取查询缓存"""
        key = self._generate_query_key(query, context)
        result = self.cache.get(key)
        
        if result:
            logger.debug(f"查询缓存命中: {query[:50]}")
        
        return result
    
    def set(self, query: str, result: Any, context: Optional[Dict] = None, ttl: Optional[int] = None):
        """设置查询缓存"""
        key = self._generate_query_key(query, context)
        self.cache.set(key, result, ttl)
        
        # 记录查询模式
        normalized = self._normalize_query(query)
        if normalized not in self.query_patterns:
            self.query_patterns[normalized] = 0
        self.query_patterns[normalized] += 1
        
        logger.debug(f"查询结果已缓存: {query[:50]}")
    
    def get_popular_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """获取热门查询"""
        sorted_queries = sorted(
            self.query_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self.cache.get_stats()
        cache_stats["unique_queries"] = len(self.query_patterns)
        cache_stats["popular_queries"] = self.get_popular_queries(5)
        return cache_stats


class DataSourceCache:
    """数据源缓存 - 针对外部API调用优化"""
    
    def __init__(self, max_size: int = 200, default_ttl: int = 60):
        self.cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
        
        logger.info("数据源缓存初始化")
    
    def _generate_datasource_key(self, source: str, query_type: str, parameters: Dict) -> str:
        """生成数据源缓存键"""
        key_data = {
            "source": source,
            "query_type": query_type,
            "parameters": str(sorted(parameters.items()))
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, source: str, query_type: str, parameters: Dict) -> Optional[Any]:
        """获取数据源缓存"""
        key = self._generate_datasource_key(source, query_type, parameters)
        result = self.cache.get(key)
        
        if result:
            logger.debug(f"数据源缓存命中: {source}.{query_type}")
        
        return result
    
    def set(self, source: str, query_type: str, parameters: Dict, result: Any, ttl: Optional[int] = None):
        """设置数据源缓存"""
        key = self._generate_datasource_key(source, query_type, parameters)
        self.cache.set(key, result, ttl)
        
        logger.debug(f"数据源结果已缓存: {source}.{query_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.cache.get_stats()


class CacheManager:
    """缓存管理器 - 统一管理所有缓存"""
    
    def __init__(self):
        self.query_cache = QueryCache(max_size=500, default_ttl=300)
        self.datasource_cache = DataSourceCache(max_size=200, default_ttl=60)
        self.llm_cache = LRUCache(max_size=300, default_ttl=600)
        
        # 启动后台清理任务
        self._cleanup_task = None
        
        logger.info("缓存管理器初始化完成")
    
    async def start_cleanup_task(self):
        """启动后台清理任务"""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("缓存清理任务已启动")
    
    async def _periodic_cleanup(self):
        """定期清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                
                self.query_cache.cache.cleanup_expired()
                self.datasource_cache.cache.cleanup_expired()
                self.llm_cache.cleanup_expired()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理任务异常: {e}")
    
    def stop_cleanup_task(self):
        """停止清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            logger.info("缓存清理任务已停止")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存统计"""
        return {
            "query_cache": self.query_cache.get_stats(),
            "datasource_cache": self.datasource_cache.get_stats(),
            "llm_cache": self.llm_cache.get_stats()
        }
    
    def clear_all(self):
        """清空所有缓存"""
        self.query_cache.cache.clear()
        self.datasource_cache.cache.clear()
        self.llm_cache.clear()
        logger.info("所有缓存已清空")


# 全局缓存管理器
global_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    return global_cache_manager


def cached_query(ttl: Optional[int] = None):
    """
    查询缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒），None使用默认值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # 尝试从缓存获取
            query = args[0] if args else kwargs.get('query', '')
            context = kwargs.get('context')
            
            cached_result = cache_manager.query_cache.get(query, context)
            if cached_result is not None:
                logger.debug(f"使用缓存结果: {query[:50]}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.query_cache.set(query, result, context, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # 尝试从缓存获取
            query = args[0] if args else kwargs.get('query', '')
            context = kwargs.get('context')
            
            cached_result = cache_manager.query_cache.get(query, context)
            if cached_result is not None:
                logger.debug(f"使用缓存结果: {query[:50]}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.query_cache.set(query, result, context, ttl)
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def cached_datasource(source: str, ttl: Optional[int] = None):
    """
    数据源缓存装饰器
    
    Args:
        source: 数据源名称
        ttl: 缓存过期时间（秒），None使用默认值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # 生成缓存键
            query_type = func.__name__
            parameters = {**kwargs}
            if args:
                parameters['args'] = str(args)
            
            # 尝试从缓存获取
            cached_result = cache_manager.datasource_cache.get(source, query_type, parameters)
            if cached_result is not None:
                logger.debug(f"使用数据源缓存: {source}.{query_type}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.datasource_cache.set(source, query_type, parameters, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # 生成缓存键
            query_type = func.__name__
            parameters = {**kwargs}
            if args:
                parameters['args'] = str(args)
            
            # 尝试从缓存获取
            cached_result = cache_manager.datasource_cache.get(source, query_type, parameters)
            if cached_result is not None:
                logger.debug(f"使用数据源缓存: {source}.{query_type}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.datasource_cache.set(source, query_type, parameters, result, ttl)
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 测试代码
async def test_cache():
    """测试缓存功能"""
    
    @cached_query(ttl=10)
    async def test_query(query: str, context: Optional[Dict] = None):
        await asyncio.sleep(1)  # 模拟慢查询
        return f"Result for: {query}"
    
    @cached_datasource("test_source", ttl=5)
    async def test_datasource_query(param1: str, param2: int):
        await asyncio.sleep(0.5)  # 模拟API调用
        return {"param1": param1, "param2": param2, "data": "test"}
    
    # 测试查询缓存
    print("测试查询缓存...")
    start = time.time()
    result1 = await test_query("test query 1")
    print(f"第一次查询耗时: {time.time() - start:.2f}s")
    
    start = time.time()
    result2 = await test_query("test query 1")  # 应该从缓存获取
    print(f"第二次查询耗时: {time.time() - start:.2f}s (缓存)")
    
    # 测试数据源缓存
    print("\n测试数据源缓存...")
    start = time.time()
    result3 = await test_datasource_query("value1", 123)
    print(f"第一次数据源查询耗时: {time.time() - start:.2f}s")
    
    start = time.time()
    result4 = await test_datasource_query("value1", 123)  # 应该从缓存获取
    print(f"第二次数据源查询耗时: {time.time() - start:.2f}s (缓存)")
    
    # 打印统计
    cache_manager = get_cache_manager()
    stats = cache_manager.get_all_stats()
    print("\n缓存统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_cache())
