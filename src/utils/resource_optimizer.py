# 资源优化模块
"""
资源优化模块 - 优化内存、连接池和并发控制

功能：
1. 内存使用监控和优化
2. 连接池管理
3. 并发控制和限流
4. 资源清理和回收
"""

import asyncio
import psutil
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
from loguru import logger
import gc


@dataclass
class ResourceMetrics:
    """资源指标"""
    timestamp: datetime
    memory_mb: float
    cpu_percent: float
    active_tasks: int
    pending_requests: int


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, warning_threshold_mb: float = 500, critical_threshold_mb: float = 1000):
        self.warning_threshold = warning_threshold_mb
        self.critical_threshold = critical_threshold_mb
        self.process = psutil.Process()
        self.metrics_history = deque(maxlen=100)
        
        logger.info(f"内存监控器初始化 - 警告阈值: {warning_threshold_mb}MB, 严重阈值: {critical_threshold_mb}MB")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        memory_info = self.process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
            "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
            "percent": self.process.memory_percent()
        }
    
    def check_memory(self) -> Dict[str, Any]:
        """检查内存状态"""
        usage = self.get_memory_usage()
        rss_mb = usage["rss_mb"]
        
        status = "normal"
        if rss_mb > self.critical_threshold:
            status = "critical"
            logger.error(f"🔴 内存使用严重: {rss_mb:.1f}MB (阈值: {self.critical_threshold}MB)")
        elif rss_mb > self.warning_threshold:
            status = "warning"
            logger.warning(f"⚠️ 内存使用警告: {rss_mb:.1f}MB (阈值: {self.warning_threshold}MB)")
        
        # 记录指标
        metric = ResourceMetrics(
            timestamp=datetime.now(),
            memory_mb=rss_mb,
            cpu_percent=self.process.cpu_percent(),
            active_tasks=len(asyncio.all_tasks()),
            pending_requests=0  # 需要从其他地方获取
        )
        self.metrics_history.append(metric)
        
        return {
            "status": status,
            "usage": usage,
            "threshold_warning": self.warning_threshold,
            "threshold_critical": self.critical_threshold
        }
    
    def trigger_gc(self):
        """触发垃圾回收"""
        before = self.get_memory_usage()["rss_mb"]
        
        gc.collect()
        
        after = self.get_memory_usage()["rss_mb"]
        freed = before - after
        
        logger.info(f"垃圾回收完成 - 释放: {freed:.1f}MB (前: {before:.1f}MB, 后: {after:.1f}MB)")
        
        return {
            "before_mb": before,
            "after_mb": after,
            "freed_mb": freed
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics_history:
            return {}
        
        memory_values = [m.memory_mb for m in self.metrics_history]
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        
        return {
            "memory": {
                "current": memory_values[-1],
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "cpu": {
                "current": cpu_values[-1],
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "samples": len(self.metrics_history)
        }


class ConnectionPool:
    """连接池管理器"""
    
    def __init__(self, max_connections: int = 10, timeout: float = 30.0):
        self.max_connections = max_connections
        self.timeout = timeout
        self.active_connections = 0
        self.waiting_queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_connections)
        self.stats = {
            "total_acquired": 0,
            "total_released": 0,
            "total_timeouts": 0,
            "peak_usage": 0
        }
        
        logger.info(f"连接池初始化 - 最大连接数: {max_connections}, 超时: {timeout}s")
    
    async def acquire(self) -> bool:
        """获取连接"""
        try:
            await asyncio.wait_for(
                self.semaphore.acquire(),
                timeout=self.timeout
            )
            
            self.active_connections += 1
            self.stats["total_acquired"] += 1
            self.stats["peak_usage"] = max(self.stats["peak_usage"], self.active_connections)
            
            logger.debug(f"连接已获取 - 活跃: {self.active_connections}/{self.max_connections}")
            return True
            
        except asyncio.TimeoutError:
            self.stats["total_timeouts"] += 1
            logger.warning(f"连接获取超时 - 活跃: {self.active_connections}/{self.max_connections}")
            return False
    
    def release(self):
        """释放连接"""
        if self.active_connections > 0:
            self.active_connections -= 1
            self.stats["total_released"] += 1
            self.semaphore.release()
            
            logger.debug(f"连接已释放 - 活跃: {self.active_connections}/{self.max_connections}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "max_connections": self.max_connections,
            "active_connections": self.active_connections,
            "available_connections": self.max_connections - self.active_connections,
            "utilization": (self.active_connections / self.max_connections * 100) if self.max_connections > 0 else 0,
            **self.stats
        }


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = 100, time_window: float = 60.0):
        """
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.rejected_count = 0
        
        logger.info(f"速率限制器初始化 - {max_requests}请求/{time_window}秒")
    
    async def acquire(self) -> bool:
        """尝试获取请求许可"""
        now = time.time()
        
        # 清理过期请求
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # 检查是否超过限制
        if len(self.requests) >= self.max_requests:
            self.rejected_count += 1
            logger.warning(f"请求被限流 - 当前: {len(self.requests)}/{self.max_requests}")
            return False
        
        # 记录请求
        self.requests.append(now)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        now = time.time()
        
        # 清理过期请求
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return {
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "current_requests": len(self.requests),
            "available_requests": self.max_requests - len(self.requests),
            "rejected_count": self.rejected_count,
            "utilization": (len(self.requests) / self.max_requests * 100) if self.max_requests > 0 else 0
        }


class ConcurrencyController:
    """并发控制器"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = 0
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        logger.info(f"并发控制器初始化 - 最大并发: {max_concurrent}")
    
    async def execute(self, coro):
        """执行协程（带并发控制）"""
        async with self.semaphore:
            self.active_tasks += 1
            self.total_tasks += 1
            
            try:
                result = await coro
                self.completed_tasks += 1
                return result
            except Exception as e:
                self.failed_tasks += 1
                logger.error(f"并发任务失败: {e}")
                raise
            finally:
                self.active_tasks -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": self.active_tasks,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0
        }


class ResourceOptimizer:
    """资源优化器 - 统一管理所有资源优化"""
    
    def __init__(self):
        self.memory_monitor = MemoryMonitor(
            warning_threshold_mb=500,
            critical_threshold_mb=1000
        )
        self.connection_pool = ConnectionPool(max_connections=10, timeout=30.0)
        self.rate_limiter = RateLimiter(max_requests=100, time_window=60.0)
        self.concurrency_controller = ConcurrencyController(max_concurrent=5)
        
        # 后台监控任务
        self._monitor_task = None
        
        logger.info("资源优化器初始化完成")
    
    async def start_monitoring(self):
        """启动后台监控"""
        self._monitor_task = asyncio.create_task(self._periodic_monitoring())
        logger.info("资源监控任务已启动")
    
    async def _periodic_monitoring(self):
        """定期监控资源"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查内存
                memory_status = self.memory_monitor.check_memory()
                
                # 如果内存严重，触发垃圾回收
                if memory_status["status"] == "critical":
                    self.memory_monitor.trigger_gc()
                
                # 记录资源状态
                logger.debug(f"资源状态 - 内存: {memory_status['usage']['rss_mb']:.1f}MB, "
                           f"连接: {self.connection_pool.active_connections}/{self.connection_pool.max_connections}, "
                           f"并发: {self.concurrency_controller.active_tasks}/{self.concurrency_controller.max_concurrent}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控异常: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        if self._monitor_task:
            self._monitor_task.cancel()
            logger.info("资源监控任务已停止")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有资源统计"""
        return {
            "memory": self.memory_monitor.get_metrics_summary(),
            "connection_pool": self.connection_pool.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "concurrency": self.concurrency_controller.get_stats()
        }
    
    def optimize_resources(self):
        """优化资源使用"""
        logger.info("开始资源优化...")
        
        # 触发垃圾回收
        gc_result = self.memory_monitor.trigger_gc()
        
        # 获取当前状态
        stats = self.get_all_stats()
        
        logger.info(f"资源优化完成 - 释放内存: {gc_result['freed_mb']:.1f}MB")
        
        return {
            "gc_result": gc_result,
            "current_stats": stats
        }


# 全局资源优化器
global_resource_optimizer = ResourceOptimizer()


def get_resource_optimizer() -> ResourceOptimizer:
    """获取全局资源优化器"""
    return global_resource_optimizer


# 测试代码
async def test_resource_optimizer():
    """测试资源优化器"""
    optimizer = get_resource_optimizer()
    
    # 启动监控
    await optimizer.start_monitoring()
    
    # 模拟一些操作
    print("测试连接池...")
    for i in range(5):
        if await optimizer.connection_pool.acquire():
            print(f"  连接 {i+1} 已获取")
            await asyncio.sleep(0.1)
            optimizer.connection_pool.release()
            print(f"  连接 {i+1} 已释放")
    
    # 测试速率限制
    print("\n测试速率限制...")
    for i in range(10):
        if await optimizer.rate_limiter.acquire():
            print(f"  请求 {i+1} 已通过")
        else:
            print(f"  请求 {i+1} 被限流")
    
    # 测试并发控制
    print("\n测试并发控制...")
    async def dummy_task(n):
        await asyncio.sleep(0.1)
        return f"Task {n} completed"
    
    tasks = [optimizer.concurrency_controller.execute(dummy_task(i)) for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(f"  完成 {len(results)} 个任务")
    
    # 打印统计
    print("\n资源统计:")
    import json
    stats = optimizer.get_all_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 优化资源
    print("\n执行资源优化...")
    optimize_result = optimizer.optimize_resources()
    print(f"  释放内存: {optimize_result['gc_result']['freed_mb']:.1f}MB")
    
    # 停止监控
    optimizer.stop_monitoring()
    await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(test_resource_optimizer())
