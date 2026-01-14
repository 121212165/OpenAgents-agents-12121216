# 通用工具函数
import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel
from loguru import logger


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


if __name__ == "__main__":
    # 测试代码
    setup_logger()
    logger.info("工具模块测试")
