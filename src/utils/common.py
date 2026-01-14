# 通用工具函数
import os
import json
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from functools import wraps
import yaml
from pydantic import BaseModel
from loguru import logger
from collections import defaultdict
from contextlib import contextmanager


# 配置日志
def setup_logger(log_level: str = "INFO", log_file: str = "logs/yougame.log"):
    """设置日志"""
    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 配置 loguru
    logger.remove()  # 移除默认处理器
    logger.add(
        log_file,
        rotation="10 MB",
        retention="7 days",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=log_level,
        format="{time:HH:mm:ss} | {level: <8} | {message}\n"
    )

    return logger


# 加载 YAML 配置
def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"配置文件加载成功: {config_path}")
        return config
    except Exception as e:
        logger.error(f"配置文件加载失败: {e}")
        return {}


# 加载环境变量
def load_env():
    """加载环境变量"""
    from dotenv import load_dotenv
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv()
        logger.info("环境变量加载成功")
    else:
        logger.warning(".env 文件不存在，使用默认配置")


# 数据模型
class LiveStatus(BaseModel):
    """直播状态数据模型"""
    player_name: str
    platform: str
    is_live: bool = False
    room_url: Optional[str] = None
    title: Optional[str] = None
    viewer_count: Optional[int] = None
    started_at: Optional[datetime] = None
    game_name: Optional[str] = None
    screenshot_url: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventMessage(BaseModel):
    """事件消息模型"""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    priority: str = "medium"  # high/medium/low

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BriefingItem(BaseModel):
    """简报条目模型"""
    title: str
    content: str
    importance: int  # 1-10
    category: str  # 直播/转会/比赛/其他
    timestamp: datetime
    url: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 异步任务辅助函数
async def run_with_timeout(coro, timeout: float):
    """带超时的异步任务"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"任务超时: {timeout}秒")
        return None


# 重试装饰器
async def retry_async(func, max_retries: int = 3, delay: float = 1.0):
    """异步重试"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"重试 {max_retries} 次后仍失败: {e}")
                raise
            logger.warning(f"第 {attempt + 1} 次尝试失败: {e}，{delay}秒后重试...")
            await asyncio.sleep(delay * (attempt + 1))  # 指数退避


# 时间格式化
def format_duration(seconds: int) -> str:
    """格式化时长"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}小时{minutes}分"
    return f"{minutes}分钟"


def format_number(num: int) -> str:
    """格式化数字（万人/千万）"""
    if num >= 10000:
        return f"{num / 10000:.1f}万"
    return str(num)


# 安全工具
def mask_api_key(key: str) -> str:
    """遮蔽 API Key"""
    if len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


# ==================== 性能监控和日志增强 ====================

class PerformanceMonitor:
    """性能监控器 - 跟踪系统性能指标"""

    def __init__(self):
        # 调用统计
        self.call_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "errors": 0,
            "last_called": None
        })

        # 慢查询阈值（秒）
        self.slow_threshold = 3.0

        # 性能警告阈值
        self.performance_warning_threshold = 5.0

    def record_call(self, name: str, duration: float, success: bool = True):
        """记录函数调用"""
        stats = self.call_stats[name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)
        stats["last_called"] = datetime.now()

        if not success:
            stats["errors"] += 1

        # 记录慢查询
        if duration > self.slow_threshold:
            logger.warning(f"⚠️ 慢查询: {name} 耗时 {duration:.2f}s")
        elif duration > self.performance_warning_threshold:
            logger.error(f"🔴 性能警告: {name} 耗时 {duration:.2f}s 超过阈值")

    def get_stats(self, name: str = None) -> Dict[str, Any]:
        """获取性能统计"""
        if name:
            if name in self.call_stats:
                return self._format_stats(name, self.call_stats[name])
            return {}

        # 返回所有统计
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

        return {
            "name": name,
            "count": count,
            "avg_time": round(avg_time, 3),
            "min_time": round(stats["min_time"], 3),
            "max_time": round(stats["max_time"], 3),
            "total_time": round(stats["total_time"], 3),
            "error_rate": round(error_rate, 2),
            "last_called": stats["last_called"].isoformat() if stats["last_called"] else None
        }

    def reset(self, name: str = None):
        """重置统计"""
        if name:
            if name in self.call_stats:
                del self.call_stats[name]
        else:
            self.call_stats.clear()

    def get_slow_queries(self, threshold: float = None) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        threshold = threshold or self.slow_threshold
        slow_queries = []

        for name, stats in self.call_stats.items():
            if stats["count"] > 0:
                avg_time = stats["total_time"] / stats["count"]
                if avg_time > threshold:
                    slow_queries.append({
                        "name": name,
                        "avg_time": avg_time,
                        "max_time": stats["max_time"],
                        "count": stats["count"]
                    })

        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)


# 全局性能监控器
global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return global_monitor


def monitor_performance(name: str = None):
    """
    性能监控装饰器

    Args:
        name: 监控名称，默认使用函数名
    """
    def decorator(func: Callable) -> Callable:
        monitor_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"性能监控: {monitor_name} 执行失败: {e}")
                raise
            finally:
                duration = time.time() - start_time
                global_monitor.record_call(monitor_name, duration, success)

                # 记录详细日志
                logger.debug(f"⏱️ {monitor_name} 耗时 {duration:.3f}s")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"性能监控: {monitor_name} 执行失败: {e}")
                raise
            finally:
                duration = time.time() - start_time
                global_monitor.record_call(monitor_name, duration, success)
                logger.debug(f"⏱️ {monitor_name} 耗时 {duration:.3f}s")

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


@contextmanager
def performance_context(name: str):
    """
    性能监控上下文管理器

    Usage:
        with performance_context("database_query"):
            # 执行数据库查询
            result = db.query(...)
    """
    start_time = time.time()
    success = True

    try:
        yield
    except Exception as e:
        success = False
        logger.error(f"性能监控: {name} 执行失败: {e}")
        raise
    finally:
        duration = time.time() - start_time
        global_monitor.record_call(name, duration, success)
        logger.debug(f"⏱️ {name} 耗时 {duration:.3f}s")


class DetailedLogger:
    """详细日志记录器 - 提供结构化日志"""

    @staticmethod
    def log_agent_call(agent_name: str, method: str, parameters: Dict[str, Any],
                      result: Any = None, duration: float = None, error: str = None):
        """记录Agent调用"""
        log_data = {
            "type": "agent_call",
            "agent": agent_name,
            "method": method,
            "parameters": str(parameters)[:200],  # 限制长度
            "timestamp": datetime.now().isoformat()
        }

        if duration is not None:
            log_data["duration_ms"] = round(duration * 1000, 2)

        if result:
            log_data["result"] = str(result)[:200]

        if error:
            log_data["error"] = error
            logger.error(f"🤖 Agent调用失败: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.info(f"🤖 Agent调用: {json.dumps(log_data, ensure_ascii=False)}")

    @staticmethod
    def log_data_source_query(source: str, query_type: str, parameters: Dict[str, Any],
                             result_count: int = None, cached: bool = False,
                             duration: float = None, error: str = None):
        """记录数据源查询"""
        log_data = {
            "type": "data_query",
            "source": source,
            "query_type": query_type,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        }

        if duration is not None:
            log_data["duration_ms"] = round(duration * 1000, 2)

        if result_count is not None:
            log_data["result_count"] = result_count

        if error:
            log_data["error"] = error
            logger.error(f"📊 数据查询失败: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.info(f"📊 数据查询: {json.dumps(log_data, ensure_ascii=False)}")

    @staticmethod
    def log_llm_call(prompt_type: str, prompt_length: int,
                     response_length: int = None, cached: bool = False,
                     duration: float = None, error: str = None):
        """记录LLM调用"""
        log_data = {
            "type": "llm_call",
            "prompt_type": prompt_type,
            "prompt_length": prompt_length,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        }

        if duration is not None:
            log_data["duration_ms"] = round(duration * 1000, 2)

        if response_length is not None:
            log_data["response_length"] = response_length

        if error:
            log_data["error"] = error
            logger.warning(f"🧠 LLM调用失败: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.debug(f"🧠 LLM调用: {json.dumps(log_data, ensure_ascii=False)}")

    @staticmethod
    def log_user_query(query: str, intent: str, confidence: float,
                      agents_used: List[str], duration: float,
                      success: bool = True):
        """记录用户查询"""
        log_data = {
            "type": "user_query",
            "query": query[:100],
            "intent": intent,
            "confidence": round(confidence, 2),
            "agents": agents_used,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        if success:
            logger.info(f"👤 用户查询: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.error(f"👤 用户查询失败: {json.dumps(log_data, ensure_ascii=False)}")


def format_performance_report() -> str:
    """格式化性能报告"""
    stats = global_monitor.get_stats()

    if not stats:
        return "📊 暂无性能数据"

    report = "📊 **性能监控报告**\n\n"

    # 总体统计
    total_calls = sum(s["count"] for s in stats.values())
    total_time = sum(s["total_time"] for s in stats.values())
    avg_time = total_time / total_calls if total_calls > 0 else 0

    report += f"📈 **总体统计**:\n"
    report += f"  总调用数: {total_calls}\n"
    report += f"  总耗时: {total_time:.2f}s\n"
    report += f"  平均耗时: {avg_time:.3f}s\n\n"

    # 慢查询
    slow_queries = global_monitor.get_slow_queries()
    if slow_queries:
        report += "⚠️ **慢查询** (>3s):\n"
        for sq in slow_queries[:5]:
            report += f"  • {sq['name']}: {sq['avg_time']:.2f}s (最大: {sq['max_time']:.2f}s)\n"
        report += "\n"

    # 详细统计
    report += "**详细统计**:\n"
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["total_time"], reverse=True)

    for name, stat in sorted_stats[:10]:
        report += f"\n🔹 {name}:\n"
        report += f"   调用次数: {stat['count']}\n"
        report += f"   平均耗时: {stat['avg_time']}s\n"
        report += f"   总耗时: {stat['total_time']}s\n"

        if stat['error_rate'] > 0:
            report += f"   ❌ 错误率: {stat['error_rate']}%\n"

    return report


if __name__ == "__main__":
    # 测试代码
    setup_logger()
    logger.info("工具模块测试")

    # 测试性能监控
    @monitor_performance("test_function")
    async def test_func():
        await asyncio.sleep(0.1)
        return "done"

    async def test_monitor():
        await test_func()
        await test_func()

        print("\n性能统计:")
        print(json.dumps(global_monitor.get_stats(), indent=2, ensure_ascii=False))
        print("\n性能报告:")
        print(format_performance_report())

    asyncio.run(test_monitor())
