# OpenAgents Studio 交互助手
"""
Studio 交互助手 - 优化用户体验

功能：
1. 用户引导和帮助信息
2. 预设演示查询
3. 快捷命令支持
4. 交互式提示
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class DemoQuery:
    """演示查询"""
    title: str
    query: str
    description: str
    category: str
    emoji: str


class StudioHelper:
    """Studio 交互助手"""
    
    def __init__(self):
        self.demo_queries = self._init_demo_queries()
        self.help_topics = self._init_help_topics()
        self.quick_commands = self._init_quick_commands()
        
        logger.info("Studio交互助手初始化完成")
    
    def _init_demo_queries(self) -> List[DemoQuery]:
        """初始化演示查询"""
        return [
            # 问候类
            DemoQuery(
                title="打招呼",
                query="你好",
                description="与小游探打招呼，了解系统功能",
                category="问候",
                emoji="👋"
            ),
            DemoQuery(
                title="系统介绍",
                query="你能做什么？",
                description="了解小游探的核心功能",
                category="问候",
                emoji="❓"
            ),
            
            # 直播查询类
            DemoQuery(
                title="查询Faker直播",
                query="Faker在直播吗？",
                description="查询知名主播Faker的直播状态",
                category="直播查询",
                emoji="🔴"
            ),
            DemoQuery(
                title="查询Uzi直播",
                query="Uzi在直播吗？",
                description="查询知名主播Uzi的直播状态",
                category="直播查询",
                emoji="🎮"
            ),
            DemoQuery(
                title="查询大司马直播",
                query="大司马在直播吗？",
                description="查询知名主播大司马的直播状态",
                category="直播查询",
                emoji="📺"
            ),
            DemoQuery(
                title="查看所有直播",
                query="现在有哪些主播在直播？",
                description="查看当前所有在线主播",
                category="直播查询",
                emoji="🌟"
            ),
            
            # 简报生成类
            DemoQuery(
                title="今日简报",
                query="生成今日简报",
                description="获取今日游戏圈动态汇总",
                category="简报生成",
                emoji="📰"
            ),
            DemoQuery(
                title="游戏圈动态",
                query="最近游戏圈有什么新闻？",
                description="了解最新的游戏圈动态",
                category="简报生成",
                emoji="📊"
            ),
            
            # 系统状态类
            DemoQuery(
                title="系统状态",
                query="系统状态",
                description="查看系统运行状态和健康信息",
                category="系统",
                emoji="🖥️"
            ),
            DemoQuery(
                title="性能报告",
                query="显示性能报告",
                description="查看系统性能统计信息",
                category="系统",
                emoji="📈"
            ),
        ]
    
    def _init_help_topics(self) -> Dict[str, str]:
        """初始化帮助主题"""
        return {
            "基础使用": """
🎮 **小游探使用指南**

小游探是一个智能游戏圈AI助手，可以帮你：
• 查询主播直播状态
• 生成游戏圈智能简报
• 分析游戏圈动态和趋势
• 监控系统运行状态

**快速开始**：
1. 直接输入你的问题
2. 使用预设查询快速体验
3. 输入 "帮助" 获取更多信息
""",
            
            "直播查询": """
🔴 **直播查询功能**

你可以这样查询：
• "Faker在直播吗？" - 查询特定主播
• "现在有谁在直播？" - 查看所有在线主播
• "LOL有哪些主播在播？" - 按游戏查询

**支持的主播**：
Faker, Uzi, 大司马, TheShy, Rookie, PDD, 小团团等

**支持的平台**：
Twitch, 虎牙, 斗鱼, Bilibili, YouTube
""",
            
            "简报生成": """
📰 **智能简报功能**

获取游戏圈动态汇总：
• "生成今日简报" - 今日动态
• "最近有什么新闻？" - 近期动态
• "游戏圈热点" - 热门话题

**简报内容包括**：
• 直播动态
• 热门游戏
• 主播动态
• 系统统计
""",
            
            "系统功能": """
🖥️ **系统功能**

查看系统信息：
• "系统状态" - 查看运行状态
• "性能报告" - 查看性能统计
• "帮助" - 获取帮助信息

**技术特性**：
• 多Agent协作
• 智能意图识别
• 实时数据更新
• 性能监控
""",
            
            "快捷命令": """
⚡ **快捷命令**

使用快捷命令快速操作：
• /help - 显示帮助
• /status - 系统状态
• /demo - 演示查询
• /clear - 清空对话

**提示**：
直接输入命令即可，无需特殊前缀
"""
        }
    
    def _init_quick_commands(self) -> Dict[str, str]:
        """初始化快捷命令"""
        return {
            "/help": "显示帮助信息",
            "/status": "查看系统状态",
            "/demo": "显示演示查询",
            "/clear": "清空对话历史",
            "/about": "关于小游探",
            "/performance": "性能报告"
        }
    
    def get_welcome_message(self) -> str:
        """获取欢迎消息"""
        return """
👋 **欢迎使用小游探！**

我是你的游戏圈AI助手，可以帮你：
🔴 查询主播直播状态
📰 生成游戏圈智能简报
📊 分析游戏圈动态趋势
🖥️ 监控系统运行状态

**快速开始**：
• 点击下方预设查询快速体验
• 直接输入你的问题
• 输入 "帮助" 了解更多功能

💡 **提示**：试试问我 "Faker在直播吗？" 或 "生成今日简报"
"""
    
    def get_demo_queries_by_category(self) -> Dict[str, List[DemoQuery]]:
        """按类别获取演示查询"""
        categories = {}
        for query in self.demo_queries:
            if query.category not in categories:
                categories[query.category] = []
            categories[query.category].append(query)
        return categories
    
    def get_demo_queries_formatted(self) -> str:
        """获取格式化的演示查询列表"""
        categories = self.get_demo_queries_by_category()
        
        result = "🎯 **预设演示查询**\n\n"
        
        for category, queries in categories.items():
            result += f"**{category}**\n"
            for query in queries:
                result += f"{query.emoji} {query.title}: `{query.query}`\n"
                result += f"   _{query.description}_\n\n"
        
        return result
    
    def get_help_message(self, topic: Optional[str] = None) -> str:
        """获取帮助信息"""
        if topic and topic in self.help_topics:
            return self.help_topics[topic]
        
        # 返回完整帮助
        result = "📚 **小游探帮助中心**\n\n"
        
        for topic_name, content in self.help_topics.items():
            result += f"**{topic_name}**\n"
            result += content + "\n\n"
        
        return result
    
    def get_quick_commands_list(self) -> str:
        """获取快捷命令列表"""
        result = "⚡ **快捷命令**\n\n"
        
        for command, description in self.quick_commands.items():
            result += f"`{command}` - {description}\n"
        
        return result
    
    def handle_command(self, command: str) -> Optional[str]:
        """处理快捷命令"""
        command = command.strip().lower()
        
        if command == "/help" or command == "帮助":
            return self.get_help_message()
        
        elif command == "/demo" or command == "演示":
            return self.get_demo_queries_formatted()
        
        elif command == "/about" or command == "关于":
            return self.get_about_message()
        
        elif command == "/commands" or command == "命令":
            return self.get_quick_commands_list()
        
        return None
    
    def get_about_message(self) -> str:
        """获取关于信息"""
        return """
🎮 **关于小游探**

**版本**: MVP v1.0
**技术栈**: OpenAgents + Python + AI

**核心特性**：
• 🤖 多Agent智能协作
• 🧠 AI增强的意图识别
• ⚡ 高性能缓存系统
• 📊 完整的性能监控
• 🔄 自动故障恢复

**开发团队**：
小游探开发团队

**技术支持**：
• GitHub: [项目地址]
• 文档: [文档链接]
• 反馈: [反馈渠道]

💡 **提示**：这是一个展示OpenAgents框架能力的MVP项目
"""
    
    def get_contextual_help(self, user_query: str, intent: str) -> Optional[str]:
        """根据上下文提供帮助"""
        # 如果用户查询失败或意图不明确，提供相关帮助
        if intent == "未知":
            return """
🤔 **我不太理解你的问题**

你可以尝试：
• 查询主播直播："Faker在直播吗？"
• 生成简报："生成今日简报"
• 查看系统："系统状态"
• 获取帮助："帮助"

或者点击预设查询快速体验！
"""
        
        return None
    
    def format_response_with_suggestions(self, response: str, intent: str) -> str:
        """为响应添加建议"""
        suggestions = {
            "问候": [
                "💡 试试查询 \"Faker在直播吗？\"",
                "💡 或者 \"生成今日简报\""
            ],
            "直播查询": [
                "💡 你还可以查询其他主播",
                "💡 或者 \"生成今日简报\" 看看整体动态"
            ],
            "简报生成": [
                "💡 想了解具体主播？试试 \"Faker在直播吗？\"",
                "💡 查看系统状态：\"系统状态\""
            ],
            "系统状态": [
                "💡 试试查询主播直播状态",
                "💡 或者生成游戏圈简报"
            ]
        }
        
        if intent in suggestions:
            response += "\n\n**你可能还想试试**：\n"
            for suggestion in suggestions[intent]:
                response += f"{suggestion}\n"
        
        return response
    
    def get_error_help(self, error_type: str) -> str:
        """获取错误相关的帮助"""
        error_helps = {
            "timeout": """
⏱️ **请求超时**

可能的原因：
• 网络连接问题
• 服务器负载过高
• 查询过于复杂

**建议**：
• 稍后重试
• 尝试更简单的查询
• 检查网络连接
""",
            "not_found": """
🔍 **未找到相关信息**

可能的原因：
• 主播名称拼写错误
• 主播当前未在直播
• 数据源暂时不可用

**建议**：
• 检查主播名称
• 查看所有在线主播
• 稍后重试
""",
            "system_error": """
❌ **系统错误**

系统遇到了一些问题，我们正在处理。

**你可以**：
• 稍后重试
• 尝试其他查询
• 查看系统状态
• 联系技术支持
"""
        }
        
        return error_helps.get(error_type, error_helps["system_error"])


# 全局Studio助手实例
global_studio_helper = StudioHelper()


def get_studio_helper() -> StudioHelper:
    """获取全局Studio助手"""
    return global_studio_helper


# 测试代码
if __name__ == "__main__":
    helper = get_studio_helper()
    
    print("="*60)
    print("欢迎消息")
    print("="*60)
    print(helper.get_welcome_message())
    
    print("\n" + "="*60)
    print("演示查询")
    print("="*60)
    print(helper.get_demo_queries_formatted())
    
    print("\n" + "="*60)
    print("帮助信息")
    print("="*60)
    print(helper.get_help_message("基础使用"))
    
    print("\n" + "="*60)
    print("快捷命令")
    print("="*60)
    print(helper.get_quick_commands_list())
