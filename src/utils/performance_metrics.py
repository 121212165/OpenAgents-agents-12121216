# 性能监控和指标收集模块
"""
性能监控模块 - 集成Prometheus指标和性能追踪

功能：
1. Prometheus指标导出
2. 性能追踪和慢查询日志
3. 实时性能监控
4. 性能报告生成
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
from dataclasses import dataclass, field
from loguru import logger
import json

# 尝试导入Prometheus客户端
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus_client未安装，Prometheus指标功能将被禁用")
    PROMETHEUS_AVAILABLE = False


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


@dataclass
class SlowQuery:
    """慢查询记录"""
    name: str
    duration: float
    timestamp: datetime
    parameters: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None


class PrometheusMetrics:
    """Prometheus指标收集器"""
    
    def __init__(self, registry: Optional['CollectorRegistry'] = None):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus客户端不可用，指标收集将被禁用")
            self.enabled = False
            return
        
        self.enabled = True
        self.registry = registry or CollectorRegistry()
        
        # 定义指标
        self._init_metrics()
        
        logger.info("Prometheus指标收集器初始化成功")
    
    def _init_metrics(self):
        """初始化Prometheus指标"""
        if not self.enabled:
            return
        
        # 请求计数器
        self.request_counter = Counter(
            'yougame_requests_total',
            'Total number of requests',
            ['agent', 'method', 'status'],
            registry=self.registry
        )
        
        # 请求延迟直方图
        self.request_duration = Histogram(
            'yougame_request_duration_seconds',
            'Request duration in seconds',
            ['agent', 'method'],
            buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0),
            registry=self.registry
        )
        
        # Agent状态
        self.agent_status = Gauge(
            'yougame_agent_status',
            'Agent status (1=healthy, 0=unhealthy)',
            ['agent'],
            registry=self.registry
        )
        
        # 错误计数器
        self.error_counter = Counter(
            'yougame_errors_total',
            'Total number of errors',
            ['agent', 'error_type'],
            registry=self.registry
        )
        
        # LLM调用计数器
        self.llm_calls = Counter(
            'yougame_llm_calls_total',
            'Total number of LLM calls',
            ['provider', 'status'],
            registry=self.registry
        )
        
        # LLM调用延迟
        self.llm_duration = Histogram(
            'yougame_llm_duration_seconds',
            'LLM call duration in seconds',
            ['provider'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
            registry=self.registry
        )
        
        # 数据源查询计数器
        self.datasource_queries = Counter(
            'yougame_datasource_queries_total',
            'Total number of data source queries',
            ['source', 'status'],
            registry=self.registry
        )
        
        # 缓存命中率
        self.cache_hits = Counter(
            'yougame_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'yougame_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # 并发请求数
        self.concurrent_requests = Gauge(
            'yougame_concurrent_requests',
            'Number of concurrent requests',
            ['agent'],
            registry=self.registry
        )
    
    def record_request(self, agent: str, method: str, duration: float, success: bool):
        """记录请求"""
        if not self.enabled:
            return
        
        status = "success" if success else "error"
        self.request_counter.labels(agent=agent, method=method, status=status).inc()
        self.request_duration.labels(agent=agent, method=method).observe(duration)
    
    def record_error(self, agent: str, error_type: str):
        """记录错误"""
        if not self.enabled:
            return
        
        self.error_counter.labels(agent=agent, error_type=error_type).inc()
    
    def set_agent_status(self, agent: str, is_healthy: bool):
        """设置Agent状态"""
        if not self.enabled:
            return
        
        self.agent_status.labels(agent=agent).set(1 if is_healthy else 0)
    
    def record_llm_call(self, provider: str, duration: float, success: bool):
        """记录LLM调用"""
        if not self.enabled:
            return
        
        status = "success" if success else "error"
        self.llm_calls.labels(provider=provider, status=status).inc()
        self.llm_duration.labels(provider=provider).observe(duration)
    
    def record_datasource_query(self, source: str, success: bool):
        """记录数据源查询"""
        if not self.enabled:
            return
        
        status = "success" if success else "error"
        self.datasource_queries.labels(source=source, status=status).inc()
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """记录缓存访问"""
        if not self.enabled:
            return
        
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def set_concurrent_requests(self, agent: str, count: int):
        """设置并发请求数"""
        if not self.enabled:
            return
        
        self.concurrent_requests.labels(agent=agent).set(count)
    
    def get_metrics(self) -> bytes:
        """获取Prometheus格式的指标"""
        if not self.enabled:
            return b""
        
        return generate_latest(self.registry)


class PerformanceTracker:
    """性能追踪器 - 增强版"""
    
    def __init__(self, slow_query_threshold: float = 3.0, max_history: int = 1000):
        self.slow_query_threshold = slow_query_threshold
        self.max_history = max_history
        
        # 性能统计
        self.call_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0,
            "last_called": None,
            "recent_durations": deque(maxlen=100)  # 最近100次调用时长
        })
        
        # 慢查询日志
        self.slow_queries = deque(maxlen=max_history)
        
        # 实时性能指标
        self.current_metrics = {}
        
        # Prometheus集成
        self.prometheus = PrometheusMetrics()
        
        logger.info(f"性能追踪器初始化 - 慢查询阈值: {slow_query_threshold}s")
    
    def record_call(self, name: str, duration: float, success: bool = True,
                   labels: Optional[Dict[str, str]] = None, parameters: Optional[Dict] = None):
        """记录函数调用"""
        stats = self.call_stats[name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)
        stats["last_called"] = datetime.now()
        stats["recent_durations"].append(duration)
        
        if not success:
            stats["errors"] += 1
        
        # 记录到Prometheus
        agent = labels.get("agent", "unknown") if labels else "unknown"
        method = labels.get("method", name) if labels else name
        self.prometheus.record_request(agent, method, duration, success)
        
        # 检查慢查询
        if duration > self.slow_query_threshold:
            self._record_slow_query(name, duration, parameters)
            logger.warning(f"⚠️ 慢查询检测: {name} 耗时 {duration:.2f}s")
    
    def _record_slow_query(self, name: str, duration: float, parameters: Optional[Dict] = None):
        """记录慢查询"""
        slow_query = SlowQuery(
            name=name,
            duration=duration,
            timestamp=datetime.now(),
            parameters=parameters or {}
        )
        self.slow_queries.append(slow_query)
    
    def get_stats(self, name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能统计"""
        if name:
            if name in self.call_stats:
                return self._format_stats(name, self.call_stats[name])
            return {}
        
        return {
            name: self._format_stats(name, stats)
            for name, stats in self.call_stats.items()
        }
    
    def _format_stats(self, name: str, stats: Dict) -> Dict[str, Any]:
        """格式化统计信息"""
        count = stats["count"]
        if count == 0:
            return {"name": name, "count": 0}
        
        avg_time = stats["total_time"] / count
        error_rate = (stats["errors"] / count) * 100 if count > 0 else 0
        
        # 计算P50, P95, P99
        recent_durations = sorted(stats["recent_durations"])
        p50 = recent_durations[len(recent_durations) // 2] if recent_durations else 0
        p95_idx = int(len(recent_durations) * 0.95)
        p95 = recent_durations[p95_idx] if recent_durations and p95_idx < len(recent_durations) else 0
        p99_idx = int(len(recent_durations) * 0.99)
        p99 = recent_durations[p99_idx] if recent_durations and p99_idx < len(recent_durations) else 0
        
        return {
            "name": name,
            "count": count,
            "avg_time": round(avg_time, 3),
            "min_time": round(stats["min_time"], 3),
            "max_time": round(stats["max_time"], 3),
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "p99": round(p99, 3),
            "total_time": round(stats["total_time"], 3),
            "error_rate": round(error_rate, 2),
            "last_called": stats["last_called"].isoformat() if stats["last_called"] else None
        }
    
    def get_slow_queries(self, limit: int = 10, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        threshold = threshold or self.slow_query_threshold
        
        # 过滤和排序
        filtered_queries = [
            {
                "name": sq.name,
                "duration": round(sq.duration, 3),
                "timestamp": sq.timestamp.isoformat(),
                "parameters": str(sq.parameters)[:100] if sq.parameters else ""
            }
            for sq in self.slow_queries
            if sq.duration >= threshold
        ]
        
        # 按时间倒序排序
        filtered_queries.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return filtered_queries[:limit]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        stats = self.get_stats()
        
        if not stats:
            return {
                "total_calls": 0,
                "total_time": 0,
                "avg_time": 0,
                "slow_queries_count": 0
            }
        
        total_calls = sum(s["count"] for s in stats.values())
        total_time = sum(s["total_time"] for s in stats.values())
        avg_time = total_time / total_calls if total_calls > 0 else 0
        
        # 找出最慢的操作
        slowest_operations = sorted(
            [(name, s["avg_time"]) for name, s in stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 找出错误率最高的操作
        highest_error_rate = sorted(
            [(name, s["error_rate"]) for name, s in stats.items() if s["error_rate"] > 0],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_calls": total_calls,
            "total_time": round(total_time, 2),
            "avg_time": round(avg_time, 3),
            "slow_queries_count": len(self.slow_queries),
            "slowest_operations": [
                {"name": name, "avg_time": round(time, 3)}
                for name, time in slowest_operations
            ],
            "highest_error_rate": [
                {"name": name, "error_rate": round(rate, 2)}
                for name, rate in highest_error_rate
            ]
        }
    
    def reset(self, name: Optional[str] = None):
        """重置统计"""
        if name:
            if name in self.call_stats:
                del self.call_stats[name]
        else:
            self.call_stats.clear()
            self.slow_queries.clear()
    
    def get_prometheus_metrics(self) -> bytes:
        """获取Prometheus格式的指标"""
        return self.prometheus.get_metrics()


# 全局性能追踪器
global_performance_tracker = PerformanceTracker()


def get_performance_tracker() -> PerformanceTracker:
    """获取全局性能追踪器"""
    return global_performance_tracker


def track_performance(name: Optional[str] = None, labels: Optional[Dict[str, str]] = None):
    """
    性能追踪装饰器
    
    Args:
        name: 追踪名称，默认使用函数名
        labels: 标签字典，用于分类
    """
    def decorator(func: Callable) -> Callable:
        track_name = name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"性能追踪: {track_name} 执行失败: {e}")
                raise
            finally:
                duration = time.time() - start_time
                global_performance_tracker.record_call(
                    track_name, duration, success, labels
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"性能追踪: {track_name} 执行失败: {e}")
                raise
            finally:
                duration = time.time() - start_time
                global_performance_tracker.record_call(
                    track_name, duration, success, labels
                )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def format_performance_report(detailed: bool = False) -> str:
    """格式化性能报告"""
    tracker = get_performance_tracker()
    summary = tracker.get_performance_summary()
    
    if summary["total_calls"] == 0:
        return "📊 暂无性能数据"
    
    report = "📊 **性能监控报告**\n\n"
    
    # 总体统计
    report += f"📈 **总体统计**:\n"
    report += f"  总调用数: {summary['total_calls']}\n"
    report += f"  总耗时: {summary['total_time']:.2f}s\n"
    report += f"  平均耗时: {summary['avg_time']:.3f}s\n"
    report += f"  慢查询数: {summary['slow_queries_count']}\n\n"
    
    # 最慢操作
    if summary["slowest_operations"]:
        report += "⚠️ **最慢操作** (平均耗时):\n"
        for op in summary["slowest_operations"]:
            report += f"  • {op['name']}: {op['avg_time']:.3f}s\n"
        report += "\n"
    
    # 错误率最高
    if summary["highest_error_rate"]:
        report += "❌ **错误率最高**:\n"
        for op in summary["highest_error_rate"]:
            report += f"  • {op['name']}: {op['error_rate']:.2f}%\n"
        report += "\n"
    
    # 慢查询
    slow_queries = tracker.get_slow_queries(limit=5)
    if slow_queries:
        report += "🐌 **最近慢查询**:\n"
        for sq in slow_queries:
            report += f"  • {sq['name']}: {sq['duration']:.2f}s ({sq['timestamp']})\n"
        report += "\n"
    
    # 详细统计
    if detailed:
        stats = tracker.get_stats()
        report += "**详细统计**:\n"
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]["total_time"], reverse=True)
        
        for name, stat in sorted_stats[:10]:
            report += f"\n🔹 {name}:\n"
            report += f"   调用次数: {stat['count']}\n"
            report += f"   平均耗时: {stat['avg_time']}s\n"
            report += f"   P50/P95/P99: {stat['p50']}/{stat['p95']}/{stat['p99']}s\n"
            report += f"   最小/最大: {stat['min_time']}/{stat['max_time']}s\n"
            
            if stat['error_rate'] > 0:
                report += f"   ❌ 错误率: {stat['error_rate']}%\n"
    
    return report


# 测试代码
async def test_performance_tracking():
    """测试性能追踪"""
    
    @track_performance("test_fast_function", labels={"agent": "test", "method": "fast"})
    async def fast_function():
        await asyncio.sleep(0.1)
        return "fast"
    
    @track_performance("test_slow_function", labels={"agent": "test", "method": "slow"})
    async def slow_function():
        await asyncio.sleep(3.5)
        return "slow"
    
    @track_performance("test_error_function", labels={"agent": "test", "method": "error"})
    async def error_function():
        await asyncio.sleep(0.2)
        raise Exception("Test error")
    
    # 执行测试
    for i in range(5):
        await fast_function()
    
    for i in range(2):
        await slow_function()
    
    for i in range(3):
        try:
            await error_function()
        except:
            pass
    
    # 打印报告
    print("\n" + "="*60)
    print("性能追踪测试报告")
    print("="*60)
    print(format_performance_report(detailed=True))
    
    # 打印慢查询
    tracker = get_performance_tracker()
    slow_queries = tracker.get_slow_queries()
    print("\n慢查询详情:")
    print(json.dumps(slow_queries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_performance_tracking())
