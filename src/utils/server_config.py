"""
服务器配置模块
处理端口和主机配置，兼容Zeabur等云平台
"""
import os
from loguru import logger


def get_server_config() -> tuple[str, int]:
    """
    获取服务器主机和端口配置
    
    Returns:
        tuple: (host, port) 其中host为'0.0.0.0'，port从环境变量读取
    
    优先级:
        1. PORT (Zeabur标准)
        2. OPENAGENTS_PORT (向后兼容)
        3. 8000 (默认值)
    """
    # 主机始终为0.0.0.0以接受外部连接
    host = "0.0.0.0"
    
    # 按优先级读取端口
    port_str = os.getenv('PORT') or os.getenv('OPENAGENTS_PORT') or '8000'
    
    try:
        port = int(port_str)
        
        # 验证端口范围
        if port < 1 or port > 65535:
            logger.warning(f"端口 {port} 超出有效范围 (1-65535)，使用默认端口 8000")
            port = 8000
            
        logger.info(f"服务器配置: host={host}, port={port}")
        logger.info(f"  PORT环境变量: {os.getenv('PORT')}")
        logger.info(f"  OPENAGENTS_PORT环境变量: {os.getenv('OPENAGENTS_PORT')}")
        
        return host, port
        
    except ValueError:
        logger.error(f"无效的端口值: {port_str}，使用默认端口 8000")
        return host, 8000
