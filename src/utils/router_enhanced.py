"""
Router Agent增强工具 - 集成响应格式化器
为RouterAgent提供增强的响应格式化功能
"""

from typing import Dict, Any
from loguru import logger

# 导入响应格式化器
try:
    from src.utils.response_formatter import (
        ResponseFormatter,
        format_live_status,
        format_briefing,
        format_error,
        format_system_status
    )
except ImportError:
    from utils.response_formatter import (
        ResponseFormatter,
        format_live_status,
        format_briefing,
        format_error,
        format_system_status
    )


class RouterFormatter:
    """
    Router Agent格式化助手
    
    为RouterAgent提供统一的响应格式化接口
    """
    
    @staticmethod
    def format_live_query_response(result: Dict[str, Any], entities: Dict) -> str:
        """格式化直播查询响应"""
        live_data = result.get("data")
        
        if not live_data:
            return format_error("未获取到直播数据", "直播查询")
        
        # 检查是否是单个主播查询
        if entities.get("主播名"):
            player_name = entities["主播名"]
            
            # 如果数据中有该主播的信息
            if isinstance(live_data, dict):
                live_data["player_name"] = player_name
                return format_live_status(live_data)
            
            # 如果是列表，查找匹配的主播
            if isinstance(live_data, list):
                for stream in live_data:
                    if player_name.lower() in str(stream).lower():
                        stream["player_name"] = player_name
                        return format_live_status(stream)
                
                # 未找到匹配主播
                return f"""{ResponseFormatter.EMOJI['未直播']} 未找到 {player_name} 的直播信息

💡 可能原因：
   • 该主播当前未在直播
   • 主播名称有误
   • 数据源暂时无法访问

{ResponseFormatter.EMOJI['信息']} 建议: 请检查主播名称或稍后重试"""
        
        # 多个主播查询
        if isinstance(live_data, list) and live_data:
            response = f"""{ResponseFormatter.EMOJI['直播']} 当前热门直播

"""
            for i, stream in enumerate(live_data[:5], 1):
                user_name = stream.get("user_name", "未知")
                game_name = stream.get("game_name", "")
                viewers = stream.get("viewer_count", 0)
                platform = stream.get("platform", "")
                
                game_icon = ResponseFormatter.get_game_icon(game_name)
                platform_icon = ResponseFormatter.get_platform_icon(platform)
                
                response += f"{i}. {ResponseFormatter.EMOJI['星星']} {user_name}"
                if game_name:
                    response += f" - {game_icon} {game_name}"
                response += f"\n   {platform_icon} {platform} | "
                response += f"{ResponseFormatter.EMOJI['观众']} {ResponseFormatter._format_viewers(viewers)}\n"
            
            return response.strip()
        
        return format_error("直播数据格式错误", "数据解析")
    
    @staticmethod
    def format_briefing_response(result: Dict[str, Any]) -> str:
        """格式化简报响应"""
        return format_briefing(result.get("data", {}))
    
    @staticmethod
    def format_system_status_response(status: Dict[str, Any]) -> str:
        """格式化系统状态响应"""
        return format_system_status(status)
    
    @staticmethod
    def format_greeting_response(context: Dict) -> str:
        """格式化问候响应"""
        hour = context.get("hour", 12)
        
        if 5 <= hour < 12:
            greeting = "早上好"
        elif 12 <= hour < 18:
            greeting = "下午好"
        elif 18 <= hour < 22:
            greeting = "晚上好"
        else:
            greeting = "夜深了"
        
        return f"""{ResponseFormatter.EMOJI['闪电']} {greeting}！我是小游探，你的游戏圈AI助手 🎮

{ResponseFormatter.EMOJI['信息']} 我可以帮你：
   • 查询主播直播状态 - \"Uzi直播了吗？\"
   • 生成游戏圈简报 - \"生成今日简报\"
   • 查看热门游戏 - \"热门游戏有哪些？\"
   • 系统状态查询 - \"系统状态\"

{ResponseFormatter.EMOJI['闪光']} 多Agent协作系统正在运行中
{ResponseFormatter.EMOJI['火箭']} 准备好为你服务！"""
    
    @staticmethod
    def format_error_response(error_msg: str, context: str = "") -> str:
        """格式化错误响应"""
        return format_error(error_msg, context)
    
    @staticmethod
    def format_help_message() -> str:
        """格式化帮助消息"""
        return f"""{ResponseFormatter.EMOJI['简报']} 小游探使用指南

{ResponseFormatter.EMOJI['直播']} 直播查询：
   • \"Uzi直播了吗？\" - 查询单个主播
   • \"谁在直播英雄联盟？\" - 按游戏查询
   • \"热门直播\" - 查看当前热门

{ResponseFormatter.EMOJI['数据']} 数据查询：
   • \"生成今日简报\" - 游戏圈动态汇总
   • \"热门游戏有哪些\" - 游戏热度排行
   • \"游戏趋势\" - 热度变化趋势

{ResponseFormatter.EMOJI['信息']} 系统功能：
   • \"系统状态\" - 查看Agent和数据源状态
   • \"帮助\" - 显示此帮助信息

{ResponseFormatter.EMOJI['闪光']} 多Agent系统特性：
   ⚡ 并发处理提升响应速度
   🔄 智能缓存优化查询性能
   🛡️ 故障自动切换保障稳定

{ResponseFormatter.EMOJI['星星']} 开始使用吧！"""


# 为RouterAgent提供的便捷函数
def enhance_router_response(result: Dict[str, Any], intent: str, 
                            entities: Dict = None) -> str:
    """
    增强Router响应（便捷函数）
    
    Args:
        result: Agent执行结果
        intent: 意图类型
        entities: 提取的实体
    
    Returns:
        格式化后的响应字符串
    """
    if not result.get("success"):
        return RouterFormatter.format_error_response(
            result.get("message", "未知错误"),
            result.get("context", "")
        )
    
    if intent == "直播查询":
        return RouterFormatter.format_live_query_response(result, entities or {})
    elif intent == "简报生成":
        return RouterFormatter.format_briefing_response(result)
    elif intent == "系统状态":
        return RouterFormatter.format_system_status_response(result.get("data", {}))
    elif intent == "问候":
        return RouterFormatter.format_greeting_response(result.get("context", {}))
    else:
        # 默认响应
        data = result.get("data")
        if isinstance(data, (dict, list)):
            import json
            return f"{ResponseFormatter.EMOJI['数据']} 查询结果：\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        return str(data)


if __name__ == "__main__":
    # 测试代码
    test_result = {
        "success": True,
        "data": {
            "player_name": "Uzi",
            "is_live": True,
            "platform": "虎牙",
            "game_name": "英雄联盟",
            "viewer_count": 150000,
            "title": "冲分啦！",
            "room_url": "https://huya.com/uzi"
        }
    }
    
    print(enhance_router_response(test_result, "直播查询", {"主播名": "Uzi"}))
