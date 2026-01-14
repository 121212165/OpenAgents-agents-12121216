# DataSource Agent - 数据源代理（OpenAgents标准重构版）
"""
标准化的数据源代理，统一管理所有数据源
支持OpenAgents标准接口和多数据源管理
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from datetime import datetime
from dataclasses import dataclass

# OpenAgents 导入
from openagents.agents import WorkerAgent

# 导入数据源管理器
from src.utils.data_sources import DataSourceManager, DataQuery, DataResult
from src.utils.llm_client import llm_client
from src.utils.error_handler import register_agent_for_recovery, handle_agent_error
from src.utils.common import monitor_performance, DetailedLogger

@dataclass
class QueryRequest:
    """查询请求"""
    query_type: str
    parameters: Dict[str, Any]
    requester: str
    priority: int = 1
    timeout: float = 10.0

@dataclass
class QueryResponse:
    """查询响应"""
    success: bool
    data: Any
    source: str
    cached: bool = False
    processing_time: float = 0.0
    error: Optional[str] = None

class DataSourceAgent(WorkerAgent):
    """
    数据源代理 - OpenAgents 标准重构版本
    
    核心功能：
    1. 标准化数据查询接口
    2. 多数据源管理和智能故障切换
    3. 查询优化和缓存管理
    4. 性能监控和健康检查
    """
    
    def __init__(self):
        super().__init__(agent_id="datasource-agent")
        
        self.description = "统一数据源管理和查询服务 - 支持多数据源故障切换"
        self.capabilities = [
            "data_query",
            "source_management", 
            "cache_management",
            "health_monitoring"
        ]
        
        # 初始化数据源管理器
        self.data_manager = DataSourceManager()
        
        # 查询统计和监控
        self.query_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "cache_hits": 0,
            "source_failures": 0,
            "avg_response_time": 0.0,
            "last_reset": datetime.now()
        }
        
        # 支持的查询类型
        self.supported_queries = {
            "streams": self._handle_streams_query,
            "user": self._handle_user_query,
            "trending": self._handle_trending_query,
            "game_info": self._handle_game_info_query,
            "live_status": self._handle_live_status_query
        }
        
        logger.info(f"{self.agent_id} 初始化成功 - 支持 {len(self.supported_queries)} 种查询类型")
    
    async def on_startup(self):
        """Agent 启动时调用"""
        logger.info(f"🚀 {self.agent_id} 启动")
        
        # 执行数据源初始化和健康检查
        await self._initialize_data_sources()
        await self._initial_health_check()
    
    async def on_direct(self, message):
        """处理直接消息 - OpenAgents标准接口"""
        try:
            content = message.get('content', '').strip()
            sender = message.get('sender', 'unknown')
            
            logger.info(f"收到数据查询请求 - 发送者: {sender}, 内容: {content}")
            
            # 解析查询请求
            if content.startswith('query'):
                await self._handle_query_command(content, sender)
            elif content == 'status':
                status = await self.get_comprehensive_status()
                await self.send_direct(sender, self._format_status_report(status))
            elif content == 'health':
                health = await self.perform_health_check()
                await self.send_direct(sender, self._format_health_report(health))
            elif content == 'stats':
                await self.send_direct(sender, self._format_stats_report())
            elif content == 'reset':
                self._reset_stats()
                await self.send_direct(sender, "📊 统计数据已重置")
            else:
                await self.send_direct(sender, self._get_help_message())
                
        except Exception as e:
            logger.error(f"处理直接消息失败: {e}")
            await self.send_direct(
                message.get('sender', 'unknown'), 
                f"❌ 处理请求时出错：{str(e)}"
            )
    
    async def on_channel_mention(self, message):
        """处理频道提及 - OpenAgents标准接口"""
        try:
            content = message.get('content', '').strip()
            sender = message.get('sender', 'unknown')
            channel = message.get('channel', 'unknown')
            
            logger.info(f"频道提及 - 频道: {channel}, 发送者: {sender}, 内容: {content}")
            
            # 在频道中处理查询
            if content.startswith('query'):
                response = await self._process_query_command(content)
                await self.post_to_channel(channel, f"@{sender} {response}")
            else:
                await self.post_to_channel(channel, f"@{sender} {self._get_help_message()}")
                
        except Exception as e:
            logger.error(f"处理频道提及失败: {e}")
            await self.post_to_channel(
                message.get('channel', 'unknown'),
                f"@{message.get('sender', 'unknown')} ❌ 处理请求时出错：{str(e)}"
            )

    # 标准化查询接口 - 供其他Agent调用
    async def get_live_streams(self, game_name: str = None, user_login: str = None, 
                             first: int = 10, language: str = None) -> QueryResponse:
        """
        获取直播流数据 - 标准接口
        
        Args:
            game_name: 游戏名称
            user_login: 主播登录名（可以是列表）
            first: 返回数量
            language: 语言过滤
            
        Returns:
            QueryResponse对象
        """
        start_time = datetime.now()
        
        try:
            parameters = {"first": first}
            if game_name:
                parameters["game_name"] = game_name
            if user_login:
                parameters["user_login"] = user_login
            if language:
                parameters["language"] = language
            
            query = DataQuery(
                query_type="streams",
                parameters=parameters,
                cache_ttl=300  # 5分钟缓存
            )
            
            result = await self.data_manager.fetch(query)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(result.success, processing_time, result.cached)
            
            return QueryResponse(
                success=result.success,
                data=result.data,
                source=result.source,
                cached=result.cached,
                processing_time=processing_time,
                error=result.error
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, processing_time, False)
            
            logger.error(f"获取直播流失败: {e}")
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                processing_time=processing_time,
                error=str(e)
            )

    async def get_user_info(self, user_login: str) -> QueryResponse:
        """
        获取用户信息 - 标准接口
        
        Args:
            user_login: 用户登录名
            
        Returns:
            QueryResponse对象
        """
        start_time = datetime.now()
        
        try:
            query = DataQuery(
                query_type="user",
                parameters={"login": user_login},
                cache_ttl=600  # 10分钟缓存
            )
            
            result = await self.data_manager.fetch(query)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self._update_stats(result.success, processing_time, result.cached)
            
            return QueryResponse(
                success=result.success,
                data=result.data,
                source=result.source,
                cached=result.cached,
                processing_time=processing_time,
                error=result.error
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, processing_time, False)
            
            logger.error(f"获取用户信息失败: {e}")
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                processing_time=processing_time,
                error=str(e)
            )

    async def get_trending_data(self) -> QueryResponse:
        """
        获取热门数据 - 标准接口
        
        Returns:
            QueryResponse对象
        """
        start_time = datetime.now()
        
        try:
            query = DataQuery(
                query_type="trending",
                parameters={},
                cache_ttl=1800  # 30分钟缓存
            )
            
            result = await self.data_manager.fetch(query)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self._update_stats(result.success, processing_time, result.cached)
            
            return QueryResponse(
                success=result.success,
                data=result.data,
                source=result.source,
                cached=result.cached,
                processing_time=processing_time,
                error=result.error
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, processing_time, False)
            
            logger.error(f"获取热门数据失败: {e}")
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                processing_time=processing_time,
                error=str(e)
            )

    async def intelligent_query(self, natural_query: str) -> QueryResponse:
        """
        智能查询 - 使用LLM理解自然语言查询
        
        Args:
            natural_query: 自然语言查询
            
        Returns:
            QueryResponse对象
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"智能查询: {natural_query}")
            
            # 使用LLM提取查询意图和参数
            llm_response = await llm_client.process_with_fallback(
                "entity_extraction",
                natural_query
            )
            
            if llm_response.success:
                try:
                    import json
                    entities = json.loads(llm_response.content)
                    logger.info(f"提取实体: {entities}")
                    
                    # 根据提取的实体执行相应查询
                    if entities.get("主播名"):
                        return await self.get_user_info(entities["主播名"].lower())
                    elif entities.get("游戏名") or entities.get("游戏"):
                        game_name = entities.get("游戏名") or entities.get("游戏")
                        return await self.get_live_streams(game_name=game_name)
                    elif "热门" in natural_query or "趋势" in natural_query:
                        return await self.get_trending_data()
                    else:
                        # 默认返回热门直播
                        return await self.get_live_streams(first=5)
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"LLM返回格式错误: {e}")
            
            # 降级到简单查询
            logger.info("降级到简单查询")
            return await self.get_live_streams(first=5)
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(False, processing_time, False)
            
            logger.error(f"智能查询失败: {e}")
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                processing_time=processing_time,
                error=str(e)
            )

    # 内部查询处理方法
    async def _handle_streams_query(self, parameters: Dict[str, Any]) -> QueryResponse:
        """处理直播流查询"""
        return await self.get_live_streams(**parameters)
    
    async def _handle_user_query(self, parameters: Dict[str, Any]) -> QueryResponse:
        """处理用户查询"""
        user_login = parameters.get("login") or parameters.get("user_login")
        if not user_login:
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                error="缺少用户登录名参数"
            )
        return await self.get_user_info(user_login)
    
    async def _handle_trending_query(self, parameters: Dict[str, Any]) -> QueryResponse:
        """处理热门数据查询"""
        return await self.get_trending_data()
    
    async def _handle_game_info_query(self, parameters: Dict[str, Any]) -> QueryResponse:
        """处理游戏信息查询"""
        game_name = parameters.get("game_name")
        if not game_name:
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                error="缺少游戏名称参数"
            )
        
        # 查询该游戏的直播流
        return await self.get_live_streams(game_name=game_name, first=20)
    
    async def _handle_live_status_query(self, parameters: Dict[str, Any]) -> QueryResponse:
        """处理直播状态查询"""
        user_login = parameters.get("user_login")
        if not user_login:
            return QueryResponse(
                success=False,
                data=None,
                source="error",
                error="缺少用户登录名参数"
            )
        
        # 查询特定用户的直播状态
        return await self.get_live_streams(user_login=user_login, first=1)

    # 命令处理
    async def _handle_query_command(self, content: str, sender: str):
        """处理查询命令"""
        response = await self._process_query_command(content)
        await self.send_direct(sender, response)
    
    async def _process_query_command(self, content: str) -> str:
        """处理查询命令并返回响应"""
        parts = content.split()
        if len(parts) < 2:
            return "❌ 查询格式：query <类型> [参数]\n支持类型: " + ", ".join(self.supported_queries.keys())
        
        query_type = parts[1].lower()
        
        if query_type not in self.supported_queries:
            return f"❌ 不支持的查询类型: {query_type}\n支持类型: " + ", ".join(self.supported_queries.keys())
        
        try:
            # 解析参数
            parameters = self._parse_query_parameters(query_type, parts[2:])
            
            # 执行查询
            handler = self.supported_queries[query_type]
            result = await handler(parameters)
            
            # 格式化响应
            return self._format_query_result(query_type, result)
            
        except Exception as e:
            logger.error(f"处理查询命令失败: {e}")
            return f"❌ 查询执行失败: {str(e)}"
    
    def _parse_query_parameters(self, query_type: str, args: List[str]) -> Dict[str, Any]:
        """解析查询参数"""
        parameters = {}
        
        if query_type == "streams":
            if args:
                if args[0].isdigit():
                    parameters["first"] = int(args[0])
                    if len(args) > 1:
                        parameters["game_name"] = " ".join(args[1:])
                else:
                    parameters["game_name"] = " ".join(args)
                    parameters["first"] = 10
            else:
                parameters["first"] = 10
        
        elif query_type == "user":
            if args:
                parameters["login"] = args[0]
            else:
                raise ValueError("用户查询需要提供用户名")
        
        elif query_type == "game_info":
            if args:
                parameters["game_name"] = " ".join(args)
            else:
                raise ValueError("游戏信息查询需要提供游戏名")
        
        elif query_type == "live_status":
            if args:
                parameters["user_login"] = args[0]
            else:
                raise ValueError("直播状态查询需要提供用户名")
        
        return parameters
    
    def _format_query_result(self, query_type: str, result: QueryResponse) -> str:
        """格式化查询结果"""
        if not result.success:
            return f"❌ 查询失败: {result.error}"
        
        header = f"✅ **{query_type.upper()}查询结果** (来源: {result.source}"
        if result.cached:
            header += ", 缓存"
        header += f", 耗时: {result.processing_time:.2f}s)\n\n"
        
        if query_type == "streams":
            return header + self._format_streams_data(result.data)
        elif query_type == "user":
            return header + self._format_user_data(result.data)
        elif query_type == "trending":
            return header + self._format_trending_data(result.data)
        elif query_type == "game_info":
            return header + self._format_game_info_data(result.data)
        elif query_type == "live_status":
            return header + self._format_live_status_data(result.data)
        else:
            return header + str(result.data)

    # 数据格式化方法
    def _format_streams_data(self, streams: List) -> str:
        """格式化直播流数据"""
        if not streams:
            return "📺 未找到直播流"
        
        response = ""
        for i, stream in enumerate(streams[:10], 1):
            if hasattr(stream, 'user_name'):
                # StreamData对象
                response += f"{i}. **{stream.user_name}**\n"
                response += f"   🎮 {stream.game_name}\n"
                response += f"   👥 {stream.viewer_count:,} 观众\n"
                response += f"   📝 {stream.title}\n"
                if hasattr(stream, 'live_url') and stream.live_url:
                    response += f"   🔗 {stream.live_url}\n"
                response += "\n"
            else:
                # 字典格式
                user_name = stream.get('user_name') or stream.get('user_login', '未知')
                response += f"{i}. **{user_name}**\n"
                response += f"   🎮 {stream.get('game_name', '未知游戏')}\n"
                response += f"   👥 {stream.get('viewer_count', 0):,} 观众\n"
                response += f"   📝 {stream.get('title', '无标题')}\n"
                if stream.get('live_url'):
                    response += f"   🔗 {stream['live_url']}\n"
                response += "\n"
        
        if len(streams) > 10:
            response += f"... 还有 {len(streams) - 10} 个直播流"
        
        return response
    
    def _format_user_data(self, user: Dict) -> str:
        """格式化用户数据"""
        if not user:
            return "👤 未找到用户"
        
        response = f"👤 **{user.get('display_name', user.get('login', '未知用户'))}**\n"
        response += f"**ID**: {user.get('id', '未知')}\n"
        
        if user.get('description'):
            response += f"**描述**: {user['description']}\n"
        
        if user.get('follower_count'):
            response += f"**粉丝数**: {user['follower_count']:,}\n"
        
        if user.get('view_count'):
            response += f"**总观看数**: {user['view_count']:,}\n"
        
        if user.get('is_partner'):
            response += f"**认证**: ✅ 合作伙伴\n"
        
        if user.get('created_at'):
            response += f"**创建时间**: {user['created_at']}\n"
        
        return response
    
    def _format_trending_data(self, trending: Any) -> str:
        """格式化热门数据"""
        if not trending:
            return "📈 暂无热门数据"
        
        if isinstance(trending, list):
            response = "📈 **热门内容**:\n\n"
            for i, item in enumerate(trending[:5], 1):
                if isinstance(item, dict):
                    title = item.get('title', item.get('name', '未知'))
                    response += f"{i}. {title}\n"
                else:
                    response += f"{i}. {str(item)}\n"
        else:
            response = f"📈 **热门数据**: {str(trending)}"
        
        return response
    
    def _format_game_info_data(self, streams: List) -> str:
        """格式化游戏信息数据"""
        if not streams:
            return "🎮 该游戏当前无人直播"
        
        total_viewers = sum(s.get('viewer_count', 0) for s in streams)
        response = f"🎮 **游戏直播统计**:\n"
        response += f"📊 直播数量: {len(streams)}\n"
        response += f"👥 总观众数: {total_viewers:,}\n\n"
        
        # 显示前5个直播
        response += "🔥 **热门直播**:\n"
        for i, stream in enumerate(streams[:5], 1):
            user_name = stream.get('user_name', '未知')
            viewers = stream.get('viewer_count', 0)
            response += f"{i}. {user_name} - {viewers:,} 观众\n"
        
        return response
    
    def _format_live_status_data(self, streams: List) -> str:
        """格式化直播状态数据"""
        if not streams:
            return "📺 该用户当前未在直播"
        
        stream = streams[0]
        if hasattr(stream, 'user_name'):
            response = f"🔴 **{stream.user_name}** 正在直播!\n"
            response += f"🎮 游戏: {stream.game_name}\n"
            response += f"👥 观众: {stream.viewer_count:,}\n"
            response += f"📝 标题: {stream.title}\n"
            if hasattr(stream, 'live_url') and stream.live_url:
                response += f"🔗 直播间: {stream.live_url}\n"
        else:
            user_name = stream.get('user_name', '未知')
            response = f"🔴 **{user_name}** 正在直播!\n"
            response += f"🎮 游戏: {stream.get('game_name', '未知')}\n"
            response += f"👥 观众: {stream.get('viewer_count', 0):,}\n"
            response += f"📝 标题: {stream.get('title', '无标题')}\n"
            if stream.get('live_url'):
                response += f"🔗 直播间: {stream['live_url']}\n"
        
        return response

    # 系统管理方法
    async def _initialize_data_sources(self):
        """初始化数据源"""
        logger.info("初始化数据源...")
        
        # 数据源管理器会自动加载配置的数据源
        sources = self.data_manager.get_source_status()
        logger.info(f"已加载 {len(sources)} 个数据源")
        
        for source_name, info in sources.items():
            logger.info(f"  - {source_name}: {info['type']}")

    async def _initial_health_check(self):
        """初始健康检查"""
        logger.info("执行数据源初始健康检查...")
        health_results = await self.data_manager.health_check_all()
        
        healthy_count = sum(1 for is_healthy in health_results.values() if is_healthy)
        total_count = len(health_results)
        
        logger.info(f"健康检查完成: {healthy_count}/{total_count} 数据源健康")
        
        for source_name, is_healthy in health_results.items():
            status = "✅" if is_healthy else "❌"
            logger.info(f"  {source_name}: {status}")

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """获取综合状态"""
        source_status = self.data_manager.get_source_status()
        health_status = await self.data_manager.health_check_all()
        
        return {
            "agent_status": "online",
            "sources": source_status,
            "health": health_status,
            "stats": self.query_stats,
            "timestamp": datetime.now().isoformat()
        }

    async def perform_health_check(self) -> Dict[str, bool]:
        """执行健康检查"""
        return await self.data_manager.health_check_all()

    def _update_stats(self, success: bool, processing_time: float, cached: bool):
        """更新统计信息"""
        self.query_stats["total_queries"] += 1
        
        if success:
            self.query_stats["successful_queries"] += 1
        else:
            self.query_stats["source_failures"] += 1
        
        if cached:
            self.query_stats["cache_hits"] += 1
        
        # 更新平均响应时间
        total = self.query_stats["total_queries"]
        current_avg = self.query_stats["avg_response_time"]
        self.query_stats["avg_response_time"] = ((current_avg * (total - 1)) + processing_time) / total

    def _reset_stats(self):
        """重置统计信息"""
        self.query_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "cache_hits": 0,
            "source_failures": 0,
            "avg_response_time": 0.0,
            "last_reset": datetime.now()
        }

    # 报告格式化方法
    def _format_status_report(self, status: Dict[str, Any]) -> str:
        """格式化状态报告"""
        response = "📊 **DataSource Agent 状态报告**\n\n"
        
        # Agent状态
        response += f"🤖 **Agent状态**: {status['agent_status']}\n\n"
        
        # 数据源状态
        response += "🔌 **数据源状态**:\n"
        for source_name, info in status['sources'].items():
            status_emoji = {
                "healthy": "🟢",
                "degraded": "🟡", 
                "failed": "🔴",
                "unknown": "⚪"
            }.get(info["status"], "⚪")
            
            response += f"{status_emoji} {source_name} ({info['type']})\n"
            response += f"   错误次数: {info['error_count']}\n"
        
        # 健康状态
        response += "\n🏥 **健康检查**:\n"
        for source_name, is_healthy in status['health'].items():
            status_icon = "✅" if is_healthy else "❌"
            response += f"{status_icon} {source_name}\n"
        
        # 统计信息
        stats = status['stats']
        total = stats['total_queries']
        if total > 0:
            success_rate = (stats['successful_queries'] / total) * 100
            cache_rate = (stats['cache_hits'] / total) * 100
            
            response += f"\n📈 **查询统计**:\n"
            response += f"总查询: {total}\n"
            response += f"成功率: {success_rate:.1f}%\n"
            response += f"缓存命中率: {cache_rate:.1f}%\n"
            response += f"平均响应时间: {stats['avg_response_time']:.2f}s\n"
        
        return response

    def _format_health_report(self, health: Dict[str, bool]) -> str:
        """格式化健康检查报告"""
        response = "🏥 **健康检查报告**\n\n"
        
        for source_name, is_healthy in health.items():
            status = "✅ 健康" if is_healthy else "❌ 异常"
            response += f"{status} {source_name}\n"
        
        healthy_count = sum(1 for is_healthy in health.values() if is_healthy)
        total_count = len(health)
        
        response += f"\n📊 总体状态: {healthy_count}/{total_count} 数据源健康"
        
        if healthy_count < total_count:
            response += "\n⚠️ 部分数据源异常，系统将自动切换到可用数据源"
        
        return response

    def _format_stats_report(self) -> str:
        """格式化统计报告"""
        stats = self.query_stats
        total = stats["total_queries"]
        
        if total == 0:
            return "📊 **查询统计**: 暂无查询记录"
        
        success_rate = (stats["successful_queries"] / total) * 100
        cache_rate = (stats["cache_hits"] / total) * 100
        failure_rate = (stats["source_failures"] / total) * 100
        
        response = f"""📊 **查询统计报告**

🔢 **总体数据**:
   总查询数: {total}
   成功查询: {stats["successful_queries"]} ({success_rate:.1f}%)
   失败查询: {stats["source_failures"]} ({failure_rate:.1f}%)
   缓存命中: {stats["cache_hits"]} ({cache_rate:.1f}%)

⚡ **性能指标**:
   平均响应时间: {stats["avg_response_time"]:.2f}s
   缓存效率: {cache_rate:.1f}%
   
📅 **统计周期**: 自 {stats["last_reset"].strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return response

    def _get_help_message(self) -> str:
        """获取帮助信息"""
        return f"""🤖 **DataSource Agent 帮助**

📋 **可用命令**:
• `query streams [数量] [游戏名]` - 查询直播流
• `query user <用户名>` - 查询用户信息  
• `query trending` - 查询热门数据
• `query game_info <游戏名>` - 查询游戏信息
• `query live_status <用户名>` - 查询直播状态
• `status` - 查看系统状态
• `health` - 执行健康检查
• `stats` - 查看查询统计
• `reset` - 重置统计数据

🔧 **支持的查询类型**: {', '.join(self.supported_queries.keys())}

💡 **示例**:
• `query streams 5 League of Legends`
• `query user faker`
• `query trending`"""

    async def on_shutdown(self):
        """Agent 关闭时调用"""
        logger.info(f"🛑 {self.agent_id} 关闭")
        
        # 输出最终统计
        total = self.query_stats["total_queries"]
        if total > 0:
            success_rate = (self.query_stats["successful_queries"] / total) * 100
            logger.info(f"最终统计 - 总查询: {total}, 成功率: {success_rate:.1f}%")


# 测试代码
async def test_datasource_agent():
    """测试重构后的数据源代理"""
    from src.utils.data_sources import MockDataSource
    
    agent = DataSourceAgent()
    
    # 添加模拟数据源
    mock_source = MockDataSource()
    agent.data_manager.add_source(mock_source)
    
    await agent.on_startup()
    
    print("🧪 测试重构后的DataSource Agent...")
    
    # 测试标准接口
    print("\n1. 测试标准接口 - 获取直播流:")
    result = await agent.get_live_streams(first=3)
    if result.success:
        print(f"✅ 查询成功，获取到 {len(result.data)} 个直播流")
        print(f"   来源: {result.source}, 缓存: {result.cached}, 耗时: {result.processing_time:.2f}s")
    else:
        print(f"❌ 查询失败: {result.error}")
    
    # 测试用户查询
    print("\n2. 测试用户查询:")
    result = await agent.get_user_info("faker")
    if result.success:
        print(f"✅ 用户查询成功")
        print(f"   来源: {result.source}, 缓存: {result.cached}")
    else:
        print(f"❌ 用户查询失败: {result.error}")
    
    # 测试智能查询
    print("\n3. 测试智能查询:")
    result = await agent.intelligent_query("Faker在直播吗？")
    if result.success:
        print(f"✅ 智能查询成功")
        print(f"   来源: {result.source}")
    else:
        print(f"❌ 智能查询失败: {result.error}")
    
    # 测试系统状态
    print("\n4. 测试系统状态:")
    status = await agent.get_comprehensive_status()
    print(f"✅ 系统状态获取成功")
    print(f"   数据源数量: {len(status['sources'])}")
    print(f"   查询统计: {status['stats']}")
    
    await agent.on_shutdown()


if __name__ == "__main__":
    asyncio.run(test_datasource_agent())