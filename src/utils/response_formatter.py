# 响应格式化模块
"""
响应格式化 - 增强响应的表现力和可读性

功能：
1. 丰富表情符号使用
2. 优化结构化文本展示
3. 添加链接和媒体内容
4. Markdown格式化
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class ResponseFormatter:
    """响应格式化器"""
    
    def __init__(self):
        self.emoji_map = self._init_emoji_map()
        logger.info("响应格式化器初始化完成")
    
    def _init_emoji_map(self) -> Dict[str, str]:
        """初始化表情符号映射"""
        return {
            # 状态类
            "online": "🟢",
            "offline": "🔴",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
            "info": "ℹ️",
            
            # 直播类
            "live": "🔴",
            "streaming": "📺",
            "viewers": "👥",
            "game": "🎮",
            "platform": "🌐",
            
            # 内容类
            "news": "📰",
            "report": "📊",
            "trend": "📈",
            "hot": "🔥",
            "new": "🆕",
            
            # 交互类
            "hello": "👋",
            "help": "💡",
            "search": "🔍",
            "link": "🔗",
            "time": "⏰",
            
            # 系统类
            "system": "🖥️",
            "agent": "🤖",
            "ai": "🧠",
            "performance": "⚡",
            "cache": "💾"
        }
    
    def format_live_status(self, status: Dict[str, Any], data_source: str = "unknown") -> str:
        """
        格式化直播状态
        
        Args:
            status: 直播状态数据
            data_source: 数据来源 (twitch_api, mock, cache等)
        """
        user_name = status.get("user_name") or status.get("player_name", "未知")
        platform = status.get("platform", "未知平台")
        title = status.get("title", "无标题")
        viewers = status.get("viewer_count", 0)
        game_name = status.get("game_name", "")
        live_url = status.get("live_url", "")
        
        # 构建响应
        response = f"## {self.emoji_map['live']} {user_name} 正在直播！\n\n"
        
        # 基本信息
        response += f"**{self.emoji_map['platform']} 平台**: {platform}\n"
        response += f"**📝 标题**: {title}\n"
        
        if game_name:
            response += f"**{self.emoji_map['game']} 游戏**: {game_name}\n"
        
        response += f"**{self.emoji_map['viewers']} 观众**: {self._format_number(viewers)}\n"
        
        # 添加链接
        if live_url:
            response += f"\n{self.emoji_map['link']} [**点击观看直播**]({live_url})\n"
        
        # 添加数据来源标识
        response += self._format_data_source_label(data_source)
        
        # 添加建议
        response += f"\n---\n"
        response += f"{self.emoji_map['help']} _你还可以查询其他主播或生成游戏圈简报_\n"
        
        return response
    
    def format_offline_status(self, player_name: str) -> str:
        """格式化离线状态"""
        response = f"## {self.emoji_map['offline']} {player_name} 当前未在直播\n\n"
        response += f"{self.emoji_map['info']} 该主播当前不在线\n\n"
        response += f"**你可以**：\n"
        response += f"- {self.emoji_map['search']} 查询其他主播的直播状态\n"
        response += f"- {self.emoji_map['news']} 生成今日游戏圈简报\n"
        response += f"- {self.emoji_map['help']} 输入 \"帮助\" 了解更多功能\n"
        
        return response
    
    def format_live_list(self, streams: List[Dict[str, Any]]) -> str:
        """格式化直播列表"""
        if not streams:
            return f"{self.emoji_map['info']} 当前没有主播在直播"
        
        response = f"## {self.emoji_map['live']} 当前直播中的主播\n\n"
        response += f"_共 {len(streams)} 位主播在线_\n\n"
        
        for i, stream in enumerate(streams[:10], 1):
            user_name = stream.get("user_name", "未知")
            game_name = stream.get("game_name", "")
            viewers = stream.get("viewer_count", 0)
            live_url = stream.get("live_url", "")
            
            response += f"### {i}. {user_name}\n"
            
            if game_name:
                response += f"   {self.emoji_map['game']} {game_name} | "
            
            response += f"{self.emoji_map['viewers']} {self._format_number(viewers)} 观众"
            
            if live_url:
                response += f" | {self.emoji_map['link']} [观看]({live_url})"
            
            response += "\n\n"
        
        if len(streams) > 10:
            response += f"_...还有 {len(streams) - 10} 位主播在线_\n"
        
        return response
    
    def format_briefing(self, briefing_data: str, live_count: int = 0, data_sources: List[str] = None) -> str:
        """
        格式化简报
        
        Args:
            briefing_data: 简报内容
            live_count: 在线主播数量
            data_sources: 数据来源列表
        """
        response = f"## {self.emoji_map['news']} 小游探游戏圈简报\n\n"
        response += f"{self.emoji_map['time']} _{datetime.now().strftime('%Y年%m月%d日 %H:%M')}_\n\n"
        response += "---\n\n"
        
        # 添加简报内容
        response += briefing_data
        
        # 添加统计信息
        if live_count > 0:
            response += f"\n\n---\n"
            response += f"### {self.emoji_map['report']} 实时统计\n\n"
            response += f"{self.emoji_map['live']} **当前直播**: {live_count} 位主播在线\n"
        
        # 添加数据来源标识
        if data_sources:
            response += self._format_data_source_label(data_sources[0] if len(data_sources) == 1 else "mixed")
        
        # 添加建议
        response += f"\n{self.emoji_map['help']} _想了解具体主播？试试查询 \"Faker在直播吗？\"_\n"
        
        return response
    
    def format_system_status(self, status: Dict[str, Any]) -> str:
        """格式化系统状态"""
        response = f"## {self.emoji_map['system']} 系统状态报告\n\n"
        response += f"{self.emoji_map['time']} _{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
        response += "---\n\n"
        
        # 路由状态
        router_status = status.get("router_status", "unknown")
        status_emoji = self.emoji_map['online'] if router_status == "online" else self.emoji_map['offline']
        response += f"### {self.emoji_map['agent']} 核心服务\n\n"
        response += f"{status_emoji} **路由中枢**: {router_status}\n\n"
        
        # LLM状态
        llm_status = status.get("llm_status", {})
        llm_available = llm_status.get("available", False)
        llm_emoji = self.emoji_map['online'] if llm_available else self.emoji_map['warning']
        
        response += f"### {self.emoji_map['ai']} AI引擎\n\n"
        response += f"{llm_emoji} **提供商**: {llm_status.get('provider', 'unknown')}\n"
        response += f"{self.emoji_map['report']} **今日调用**: {llm_status.get('daily_usage', '0/0')}\n"
        
        if llm_status.get('cache_size', 0) > 0:
            response += f"{self.emoji_map['cache']} **缓存大小**: {llm_status.get('cache_size', 0)}\n"
        
        response += "\n"
        
        # Agent状态
        agents = status.get("agents", {})
        if agents:
            response += f"### {self.emoji_map['agent']} Agent状态\n\n"
            
            for agent_name, agent_status in agents.items():
                available = agent_status.get("available", False)
                error_count = agent_status.get("error_count", 0)
                
                agent_emoji = self.emoji_map['online'] if available else self.emoji_map['offline']
                response += f"{agent_emoji} **{agent_name}**"
                
                if error_count > 0:
                    response += f" _{self.emoji_map['warning']} {error_count} 错误_"
                
                response += "\n"
        
        response += f"\n---\n"
        response += f"{self.emoji_map['success']} _系统运行正常_\n"
        
        return response
    
    def format_error_message(self, error_type: str, error_msg: str) -> str:
        """格式化错误消息"""
        response = f"## {self.emoji_map['error']} 出错了\n\n"
        
        if error_type == "timeout":
            response += f"{self.emoji_map['warning']} **请求超时**\n\n"
            response += "可能的原因：\n"
            response += "- 网络连接问题\n"
            response += "- 服务器负载过高\n\n"
        elif error_type == "not_found":
            response += f"{self.emoji_map['search']} **未找到相关信息**\n\n"
            response += "可能的原因：\n"
            response += "- 主播名称拼写错误\n"
            response += "- 主播当前未在直播\n\n"
        else:
            response += f"{self.emoji_map['error']} **系统错误**\n\n"
            response += f"错误信息：{error_msg}\n\n"
        
        response += "**建议**：\n"
        response += f"- {self.emoji_map['help']} 稍后重试\n"
        response += f"- {self.emoji_map['search']} 尝试其他查询\n"
        response += f"- {self.emoji_map['system']} 查看系统状态\n"
        
        return response
    
    def add_suggestions(self, response: str, intent: str) -> str:
        """为响应添加建议"""
        suggestions = {
            "问候": [
                f"{self.emoji_map['live']} 查询主播直播：\"Faker在直播吗？\"",
                f"{self.emoji_map['news']} 生成简报：\"生成今日简报\""
            ],
            "直播查询": [
                f"{self.emoji_map['search']} 查询其他主播",
                f"{self.emoji_map['news']} 生成游戏圈简报"
            ],
            "简报生成": [
                f"{self.emoji_map['live']} 查询具体主播状态",
                f"{self.emoji_map['system']} 查看系统状态"
            ]
        }
        
        if intent in suggestions:
            response += "\n\n---\n"
            response += f"### {self.emoji_map['help']} 你可能还想试试\n\n"
            for suggestion in suggestions[intent]:
                response += f"- {suggestion}\n"
        
        return response
    
    def format_with_markdown(self, text: str, style: str = "default") -> str:
        """使用Markdown格式化文本"""
        if style == "bold":
            return f"**{text}**"
        elif style == "italic":
            return f"_{text}_"
        elif style == "code":
            return f"`{text}`"
        elif style == "quote":
            return f"> {text}"
        elif style == "heading1":
            return f"# {text}"
        elif style == "heading2":
            return f"## {text}"
        elif style == "heading3":
            return f"### {text}"
        else:
            return text
    
    def create_link(self, text: str, url: str) -> str:
        """创建Markdown链接"""
        return f"[{text}]({url})"
    
    def create_list(self, items: List[str], ordered: bool = False) -> str:
        """创建列表"""
        result = ""
        for i, item in enumerate(items, 1):
            if ordered:
                result += f"{i}. {item}\n"
            else:
                result += f"- {item}\n"
        return result
    
    def create_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """创建Markdown表格"""
        # 表头
        table = "| " + " | ".join(headers) + " |\n"
        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        # 表格行
        for row in rows:
            table += "| " + " | ".join(row) + " |\n"
        
        return table
    
    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 10000:
            return f"{num / 10000:.1f}万"
        elif num >= 1000:
            return f"{num / 1000:.1f}千"
        return str(num)
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分"
        return f"{minutes}分钟"
    
    def _format_data_source_label(self, data_source: str) -> str:
        """
        格式化数据来源标识
        
        Args:
            data_source: 数据来源 (twitch_api, mock, cache, mixed等)
        
        Returns:
            格式化的数据来源标签
        """
        if data_source == "mock":
            return f"\n\n{self.emoji_map['info']} _数据来源: 演示模式 (模拟数据)_"
        elif data_source == "twitch_api":
            return f"\n\n{self.emoji_map['success']} _数据来源: Twitch API (实时数据)_"
        elif data_source == "cache":
            return f"\n\n{self.emoji_map['cache']} _数据来源: 缓存 (最近更新)_"
        elif data_source == "mixed":
            return f"\n\n{self.emoji_map['info']} _数据来源: 混合模式 (多数据源)_"
        elif data_source == "unknown":
            return ""
        else:
            return f"\n\n{self.emoji_map['info']} _数据来源: {data_source}_"


# 全局响应格式化器
global_response_formatter = ResponseFormatter()


def get_response_formatter() -> ResponseFormatter:
    """获取全局响应格式化器"""
    return global_response_formatter


# 测试代码
if __name__ == "__main__":
    formatter = get_response_formatter()
    
    # 测试直播状态格式化
    print("="*60)
    print("直播状态格式化")
    print("="*60)
    status = {
        "user_name": "Faker",
        "platform": "Twitch",
        "title": "Faker的直播间",
        "viewer_count": 45000,
        "game_name": "League of Legends",
        "live_url": "https://twitch.tv/faker"
    }
    print(formatter.format_live_status(status))
    
    # 测试系统状态格式化
    print("\n" + "="*60)
    print("系统状态格式化")
    print("="*60)
    system_status = {
        "router_status": "online",
        "llm_status": {
            "provider": "OpenAI",
            "available": True,
            "daily_usage": "50/1000",
            "cache_size": 10
        },
        "agents": {
            "live_monitor": {"available": True, "error_count": 0},
            "briefing_agent": {"available": True, "error_count": 0}
        }
    }
    print(formatter.format_system_status(system_status))
