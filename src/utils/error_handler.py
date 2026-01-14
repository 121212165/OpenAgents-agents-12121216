# 错误处理模块 - 统一异常管理和恢复机制
"""
提供统一的错误处理、Agent自动恢复和用户友好的错误信息

功能：
1. 异常分类和处理
2. Agent自动恢复机制
3. 用户友好的错误消息
4. 错误监控和统计
"""

import asyncio
import functools
from typing import Callable, Any, Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
from dataclasses import dataclass, field


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 轻微错误，不影响核心功能
    MEDIUM = "medium"     # 中等错误，影响部分功能
    HIGH = "high"         # 严重错误，影响核心功能
    CRITICAL = "critical" # 致命错误，需要立即处理


class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"           # 网络相关错误
    API = "api"                   # API调用错误
    DATA_SOURCE = "data_source"   # 数据源错误
    AGENT = "agent"               # Agent执行错误
    LLM = "llm"                   # LLM调用错误
    VALIDATION = "validation"     # 输入验证错误
    TIMEOUT = "timeout"           # 超时错误
    UNKNOWN = "unknown"           # 未知错误


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    suggested_action: Optional[str] = None


class UserFriendlyMessages:
    """用户友好的错误消息库"""

    MESSAGES = {
        ErrorCategory.NETWORK: {
            "title": "网络连接问题",
            "default": "抱歉，网络连接出现问题，请检查您的网络设置",
            "suggestions": [
                "检查您的网络连接是否正常",
                "稍后重试",
                "如果问题持续，请联系技术支持"
            ]
        },
        ErrorCategory.API: {
            "title": "服务暂时不可用",
            "default": "抱歉，外部服务暂时无法访问，系统正在使用备用数据源",
            "suggestions": [
                "系统已自动切换到备用数据源",
                "您可以继续使用系统功能",
                "完整功能将在服务恢复后可用"
            ]
        },
        ErrorCategory.DATA_SOURCE: {
            "title": "数据源问题",
            "default": "抱歉，数据获取遇到问题，系统正在使用缓存数据",
            "suggestions": [
                "系统正在尝试恢复数据源",
                "当前显示的是缓存数据",
                "数据将在恢复后自动更新"
            ]
        },
        ErrorCategory.AGENT: {
            "title": "服务处理异常",
            "default": "抱歉，处理您的请求时遇到了问题",
            "suggestions": [
                "请尝试重新表述您的请求",
                "或者尝试其他查询方式",
                "如果问题持续，请联系技术支持"
            ]
        },
        ErrorCategory.LLM: {
            "title": "AI服务降级",
            "default": "AI增强功能暂时不可用，系统使用基础模式继续服务",
            "suggestions": [
                "系统已自动切换到基础模式",
                "核心功能不受影响",
                "AI增强将在恢复后重新启用"
            ]
        },
        ErrorCategory.VALIDATION: {
            "title": "输入格式问题",
            "default": "抱歉，您的请求格式不正确",
            "suggestions": [
                "请检查您的输入格式",
                "查看帮助信息了解正确格式",
                "使用示例查询作为参考"
            ]
        },
        ErrorCategory.TIMEOUT: {
            "title": "请求超时",
            "default": "抱歉，请求处理时间过长，已自动取消",
            "suggestions": [
                "请稍后重试",
                "尝试简化您的查询",
                "或者稍后再试"
            ]
        },
        ErrorCategory.UNKNOWN: {
            "title": "未知错误",
            "default": "抱歉，遇到了未预期的错误",
            "suggestions": [
                "请稍后重试",
                "如果问题持续，请联系技术支持",
                "技术团队已收到通知"
            ]
        }
    }

    @classmethod
    def get_message(cls, category: ErrorCategory, detail: str = None) -> str:
        """获取用户友好的错误消息"""
        msg_config = cls.MESSAGES.get(category, cls.MESSAGES[ErrorCategory.UNKNOWN])

        message = f"🔔 **{msg_config['title']}**\n\n"
        message += f"{msg_config['default']}\n"

        if detail:
            message += f"\n详细信息：{detail}\n"

        message += "\n💡 **建议**：\n"
        for i, suggestion in enumerate(msg_config['suggestions'], 1):
            message += f"{i}. {suggestion}\n"

        return message


class AgentRecoveryManager:
    """Agent恢复管理器 - 处理Agent异常和自动恢复"""

    def __init__(self):
        # Agent状态跟踪
        self.agent_status: Dict[str, Dict[str, Any]] = {}

        # 错误统计
        self.error_stats: Dict[str, Dict[str, int]] = {}

        # 恢复配置
        self.recovery_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "backoff_multiplier": 2.0,
            "max_error_count": 5,
            "error_window_seconds": 300,  # 5分钟窗口
            "cooldown_seconds": 60         # 冷却时间
        }

        # 恢复任务
        self.recovery_tasks: Dict[str, asyncio.Task] = {}

    def register_agent(self, agent_name: str, agent_instance: Any):
        """注册Agent到恢复管理器"""
        self.agent_status[agent_name] = {
            "instance": agent_instance,
            "status": "active",
            "error_count": 0,
            "errors": [],  # 最近的错误列表
            "last_error_time": None,
            "recovery_attempts": 0,
            "in_cooldown": False,
            "cooldown_until": None
        }
        self.error_stats[agent_name] = {}
        logger.info(f"Agent {agent_name} 已注册到恢复管理器")

    def update_agent_status(self, agent_name: str, status: str):
        """更新Agent状态"""
        if agent_name in self.agent_status:
            self.agent_status[agent_name]["status"] = status
            logger.info(f"Agent {agent_name} 状态更新为: {status}")

    def is_agent_available(self, agent_name: str) -> bool:
        """检查Agent是否可用"""
        if agent_name not in self.agent_status:
            return True  # 未注册的Agent假设可用

        status_info = self.agent_status[agent_name]

        # 检查是否在冷却期
        if status_info["in_cooldown"]:
            if datetime.now() < status_info["cooldown_until"]:
                return False
            else:
                # 冷却期结束，重置状态
                status_info["in_cooldown"] = False
                status_info["error_count"] = 0

        # 检查错误次数
        return status_info["error_count"] < self.recovery_config["max_error_count"]

    async def handle_error(self, agent_name: str, error: Exception,
                          context: Dict[str, Any] = None) -> ErrorInfo:
        """处理Agent错误"""
        logger.error(f"Agent {agent_name} 发生错误: {error}")

        # 分类错误
        error_info = self._classify_error(agent_name, error, context)

        # 更新Agent状态
        await self._update_agent_error_status(agent_name, error_info)

        # 触发恢复流程
        if error_info.recoverable:
            await self._trigger_recovery(agent_name, error_info)

        return error_info

    def _classify_error(self, agent_name: str, error: Exception,
                       context: Dict[str, Any] = None) -> ErrorInfo:
        """分类错误并生成错误信息"""
        error_type = type(error).__name__
        error_message = str(error)

        # 根据错误类型分类
        if "timeout" in error_type.lower() or "TimeoutError" in error_type:
            category = ErrorCategory.TIMEOUT
        elif "connection" in error_message.lower() or "network" in error_message.lower():
            category = ErrorCategory.NETWORK
        elif "api" in error_message.lower() or "http" in error_message.lower():
            category = ErrorCategory.API
        elif "llm" in error_message.lower() or "openai" in error_message.lower():
            category = ErrorCategory.LLM
        elif "validation" in error_message.lower() or "invalid" in error_message.lower():
            category = ErrorCategory.VALIDATION
        elif "data" in error_message.lower():
            category = ErrorCategory.DATA_SOURCE
        else:
            category = ErrorCategory.UNKNOWN

        # 确定严重程度
        if category in [ErrorCategory.TIMEOUT, ErrorCategory.NETWORK]:
            severity = ErrorSeverity.MEDIUM
        elif category == ErrorCategory.AGENT:
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.LOW

        # 判断是否可恢复
        recoverable = severity != ErrorSeverity.CRITICAL

        # 生成用户友好的消息
        user_message = UserFriendlyMessages.get_message(category, error_message)

        return ErrorInfo(
            error_type=error_type,
            category=category,
            severity=severity,
            message=error_message,
            user_message=user_message,
            agent_name=agent_name,
            context=context or {},
            recoverable=recoverable,
            suggested_action=self._get_suggested_action(category)
        )

    def _get_suggested_action(self, category: ErrorCategory) -> str:
        """获取建议的操作"""
        actions = {
            ErrorCategory.NETWORK: "Check network connection and retry",
            ErrorCategory.API: "Switch to backup data source",
            ErrorCategory.DATA_SOURCE: "Use cached data",
            ErrorCategory.AGENT: "Restart agent and retry",
            ErrorCategory.LLM: "Use fallback mode",
            ErrorCategory.VALIDATION: "Check input format",
            ErrorCategory.TIMEOUT: "Retry with shorter timeout",
            ErrorCategory.UNKNOWN: "Contact technical support"
        }
        return actions.get(category, "Retry the operation")

    async def _update_agent_error_status(self, agent_name: str, error_info: ErrorInfo):
        """更新Agent错误状态"""
        if agent_name not in self.agent_status:
            return

        status_info = self.agent_status[agent_name]
        status_info["error_count"] += 1
        status_info["last_error_time"] = datetime.now()

        # 记录错误（保留最近的10个）
        status_info["errors"].append({
            "time": datetime.now(),
            "type": error_info.error_type,
            "category": error_info.category.value,
            "message": error_info.message
        })
        if len(status_info["errors"]) > 10:
            status_info["errors"].pop(0)

        # 更新错误统计
        category = error_info.category.value
        if category not in self.error_stats[agent_name]:
            self.error_stats[agent_name][category] = 0
        self.error_stats[agent_name][category] += 1

        # 检查是否需要进入冷却期
        if status_info["error_count"] >= self.recovery_config["max_error_count"]:
            status_info["in_cooldown"] = True
            status_info["cooldown_until"] = datetime.now() + timedelta(
                seconds=self.recovery_config["cooldown_seconds"]
            )
            logger.warning(f"Agent {agent_name} 进入冷却期，{self.recovery_config['cooldown_seconds']}秒后恢复")

    async def _trigger_recovery(self, agent_name: str, error_info: ErrorInfo):
        """触发Agent恢复流程"""
        if agent_name in self.recovery_tasks and not self.recovery_tasks[agent_name].done():
            logger.info(f"Agent {agent_name} 的恢复任务已在运行")
            return

        logger.info(f"启动 Agent {agent_name} 的恢复流程")
        recovery_task = asyncio.create_task(self._recover_agent(agent_name))
        self.recovery_tasks[agent_name] = recovery_task

    async def _recover_agent(self, agent_name: str):
        """恢复Agent"""
        max_retries = self.recovery_config["max_retries"]
        delay = self.recovery_config["retry_delay"]

        for attempt in range(1, max_retries + 1):
            logger.info(f"Agent {agent_name} 恢复尝试 {attempt}/{max_retries}")

            # 等待一段时间
            await asyncio.sleep(delay * attempt)

            try:
                # 尝试调用Agent的健康检查或重启方法
                if agent_name in self.agent_status:
                    agent_instance = self.agent_status[agent_name]["instance"]

                    # 尝试不同的恢复方法
                    recovered = False

                    if hasattr(agent_instance, 'health_check'):
                        is_healthy = await agent_instance.health_check()
                        if is_healthy:
                            recovered = True
                            logger.info(f"Agent {agent_name} 健康检查通过")

                    if not recovered and hasattr(agent_instance, 'restart'):
                        await agent_instance.restart()
                        recovered = True
                        logger.info(f"Agent {agent_name} 已重启")

                    if recovered:
                        # 重置错误计数
                        self.agent_status[agent_name]["error_count"] = 0
                        self.agent_status[agent_name]["recovery_attempts"] += 1
                        self.update_agent_status(agent_name, "active")
                        logger.info(f"✅ Agent {agent_name} 恢复成功")
                        return

            except Exception as e:
                logger.error(f"Agent {agent_name} 恢复失败 (尝试 {attempt}): {e}")

        # 所有恢复尝试都失败
        logger.error(f"❌ Agent {agent_name} 经过 {max_retries} 次尝试后仍无法恢复")
        self.update_agent_status(agent_name, "failed")

    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """获取Agent状态"""
        if agent_name:
            if agent_name in self.agent_status:
                status_info = self.agent_status[agent_name].copy()
                # 移除instance引用，避免序列化问题
                status_info.pop("instance", None)
                return status_info
            return {}

        # 返回所有Agent状态
        all_status = {}
        for name, info in self.agent_status.items():
            status_info = info.copy()
            status_info.pop("instance", None)
            all_status[name] = status_info
        return all_status

    def get_error_statistics(self) -> Dict[str, Dict[str, int]]:
        """获取错误统计"""
        return self.error_stats.copy()

    def reset_agent_status(self, agent_name: str):
        """重置Agent状态（手动恢复）"""
        if agent_name in self.agent_status:
            self.agent_status[agent_name]["error_count"] = 0
            self.agent_status[agent_name]["in_cooldown"] = False
            self.agent_status[agent_name]["cooldown_until"] = None
            self.update_agent_status(agent_name, "active")
            logger.info(f"Agent {agent_name} 状态已手动重置")


def with_error_handling(recovery_manager: AgentRecoveryManager = None,
                       agent_name: str = None,
                       fallback_result: Any = None):
    """
    错误处理装饰器

    Args:
        recovery_manager: 恢复管理器实例
        agent_name: Agent名称
        fallback_result: 错误时的返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}")

                # 如果提供了恢复管理器，处理错误
                if recovery_manager and agent_name:
                    error_info = await recovery_manager.handle_error(
                        agent_name, e,
                        {"function": func.__name__, "args": str(args)[:100]}
                    )

                    # 返回用户友好的错误
                    if fallback_result is not None:
                        return fallback_result
                    raise Exception(error_info.user_message) from e

                # 没有恢复管理器，直接抛出
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {e}")
                raise

        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全局恢复管理器实例
global_recovery_manager = AgentRecoveryManager()


def get_global_recovery_manager() -> AgentRecoveryManager:
    """获取全局恢复管理器"""
    return global_recovery_manager


# 便捷函数
async def handle_agent_error(agent_name: str, error: Exception,
                            context: Dict[str, Any] = None) -> str:
    """
    处理Agent错误并返回用户友好的消息

    Args:
        agent_name: Agent名称
        error: 异常对象
        context: 错误上下文

    Returns:
        用户友好的错误消息
    """
    error_info = await global_recovery_manager.handle_error(agent_name, error, context)
    return error_info.user_message


def is_agent_healthy(agent_name: str) -> bool:
    """检查Agent是否健康"""
    return global_recovery_manager.is_agent_available(agent_name)


def register_agent_for_recovery(agent_name: str, agent_instance: Any):
    """注册Agent到恢复管理器"""
    global_recovery_manager.register_agent(agent_name, agent_instance)


if __name__ == "__main__":
    # 测试代码
    async def test_error_handler():
        print("🧪 测试错误处理模块...")

        # 测试用户友好消息
        print("\n1. 测试用户友好消息:")
        for category in ErrorCategory:
            message = UserFriendlyMessages.get_message(category)
            print(f"\n{category.value.upper()}:")
            print(message[:200] + "...")

        # 测试恢复管理器
        print("\n2. 测试恢复管理器:")
        manager = AgentRecoveryManager()
        manager.register_agent("test_agent", None)

        # 模拟错误
        try:
            raise ConnectionError("网络连接失败")
        except Exception as e:
            error_info = await manager.handle_error("test_agent", e)
            print(f"\n错误分类: {error_info.category.value}")
            print(f"严重程度: {error_info.severity.value}")
            print(f"可恢复: {error_info.recoverable}")
            print(f"\n用户消息:\n{error_info.user_message[:300]}...")

        # 获取状态
        print("\n3. Agent状态:")
        status = manager.get_agent_status("test_agent")
        print(f"状态: {status}")

        print("\n4. 错误统计:")
        stats = manager.get_error_statistics()
        print(f"统计: {stats}")

    asyncio.run(test_error_handler())
