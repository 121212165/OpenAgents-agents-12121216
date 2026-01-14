# BriefingAgent - 简报生成 Agent（多Agent协作重构版）
import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# OpenAgents 导入
from openagents.agents import WorkerAgent

# 导入LLM客户端
from src.utils.llm_client import llm_client
from src.utils.error_handler import register_agent_for_recovery, handle_agent_error
from src.utils.common import DetailedLogger

@dataclass
class BriefingRequest:
    """简报请求"""
    time_range: str = "today"
    include_trends: bool = True
    include_live_data: bool = True
    max_items: int = 10
    requester: str = "unknown"
    priority: int = 1

@dataclass
class AgentCollaborationResult:
    """Agent协作结果"""
    agent_name: str
    success: bool
    data: Any
    processing_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BriefingAgent(WorkerAgent):
    """
    简报生成 Agent - 多Agent协作重构版本

    核心功能：
    1. 多Agent协作数据收集
    2. 智能结果聚合和分析
    3. 个性化简报生成
    4. 实时数据整合
    """

    def __init__(self):
        super().__init__(agent_id="briefing-agent")
        
        self.description = "多Agent协作智能简报生成系统"
        self.capabilities = [
            "multi_agent_coordination",
            "data_aggregation", 
            "intelligent_summarization",
            "trend_analysis",
            "personalized_briefing"
        ]

        # Agent协作配置
        self.collaborating_agents = {}
        self.agent_priorities = {
            "data_source": 1,    # 最高优先级 - 基础数据
            "live_monitor": 2,   # 次高优先级 - 实时状态
            "router": 3          # 系统状态和路由信息
        }
        
        # 数据聚合配置
        self.aggregation_strategies = {
            "live_data": self._aggregate_live_data,
            "trend_data": self._aggregate_trend_data,
            "system_data": self._aggregate_system_data
        }
        
        # 简报模板配置
        self.briefing_templates = {
            "daily": self._generate_daily_briefing,
            "live_focus": self._generate_live_focus_briefing,
            "trend_analysis": self._generate_trend_analysis_briefing
        }
        
        # 协作统计
        self.collaboration_stats = {
            "total_requests": 0,
            "successful_collaborations": 0,
            "agent_response_times": {},
            "aggregation_success_rate": 0.0,
            "last_reset": datetime.now()
        }
        
        # LLM增强功能
        self.use_llm = True
        self.llm_enhancement_enabled = True

        logger.info(f"{self.agent_id} 初始化成功 - 多Agent协作系统就绪")

    def register_collaborating_agent(self, agent_name: str, agent_instance):
        """注册协作Agent"""
        self.collaborating_agents[agent_name] = agent_instance
        self.collaboration_stats["agent_response_times"][agent_name] = []
        logger.info(f"协作Agent注册成功: {agent_name}")

    async def on_startup(self):
        """Agent 启动时调用"""
        logger.info(f"🚀 {self.agent_id} 启动 - 多Agent协作系统在线")
        
        # 检查协作Agent状态
        await self._check_collaborating_agents()

    async def on_direct(self, message):
        """处理直接消息 - OpenAgents标准接口"""
        try:
            content = message.get('content', '').strip()
            sender = message.get('sender', 'unknown')
            
            logger.info(f"收到简报请求 - 发送者: {sender}, 内容: {content}")
            
            # 解析请求类型
            if content in ['briefing', 'report', '简报', '日报']:
                # 生成标准简报
                request = BriefingRequest(
                    time_range="today",
                    requester=sender
                )
                briefing = await self.generate_collaborative_briefing(request)
                await self.send_direct(sender, briefing)
            
            elif content.startswith('summary'):
                # 生成特定主播摘要
                parts = content.split()
                if len(parts) > 1:
                    player_name = parts[1]
                    summary = await self.generate_player_summary(player_name, sender)
                    await self.send_direct(sender, summary)
                else:
                    await self.send_direct(sender, "请指定主播名称，例如：summary Uzi")
            
            elif content.startswith('trend'):
                # 生成趋势分析简报
                request = BriefingRequest(
                    time_range="recent",
                    include_trends=True,
                    requester=sender
                )
                briefing = await self.generate_trend_briefing(request)
                await self.send_direct(sender, briefing)
            
            elif content == 'stats':
                # 显示协作统计
                stats_report = self._format_collaboration_stats()
                await self.send_direct(sender, stats_report)
            
            elif content == 'agents':
                # 显示协作Agent状态
                agent_status = await self._get_collaborating_agents_status()
                await self.send_direct(sender, agent_status)
            
            else:
                help_message = self._get_briefing_help()
                await self.send_direct(sender, help_message)
                
        except Exception as e:
            logger.error(f"处理直接消息失败: {e}")
            await self.send_direct(
                message.get('sender', 'unknown'), 
                f"❌ 处理简报请求时出错：{str(e)}"
            )

    # 核心多Agent协作方法
    async def generate_collaborative_briefing(self, request: BriefingRequest) -> str:
        """
        生成协作式简报 - 核心方法
        
        Args:
            request: 简报请求对象
            
        Returns:
            格式化的简报文本
        """
        start_time = datetime.now()
        self.collaboration_stats["total_requests"] += 1
        
        try:
            logger.info(f"开始生成协作式简报 - 时间范围: {request.time_range}, 请求者: {request.requester}")

            # 1. 多Agent数据收集阶段
            collaboration_results = await self._collect_data_from_agents(request)
            
            # 2. 数据聚合和分析阶段
            aggregated_data = await self._aggregate_collaboration_results(collaboration_results)
            
            # 3. 智能简报生成阶段
            briefing_content = await self._generate_intelligent_briefing(
                aggregated_data, request
            )
            
            # 4. 结果优化和格式化阶段
            final_briefing = await self._optimize_briefing_output(
                briefing_content, aggregated_data, request
            )
            
            # 更新成功统计
            processing_time = (datetime.now() - start_time).total_seconds()
            self.collaboration_stats["successful_collaborations"] += 1
            
            logger.info(f"协作式简报生成成功 - 耗时: {processing_time:.2f}s")
            
            return final_briefing

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"协作式简报生成失败: {e} - 耗时: {processing_time:.2f}s")
            
            # 返回降级简报
            return await self._generate_fallback_briefing(request, str(e))

    async def _collect_data_from_agents(self, request: BriefingRequest) -> List[AgentCollaborationResult]:
        """从多个Agent收集数据"""
        collection_tasks = []
        
        # 根据请求配置决定需要哪些Agent的数据
        if request.include_live_data:
            # 收集实时直播数据
            if "live_monitor" in self.collaborating_agents:
                collection_tasks.append(
                    self._collect_from_agent("live_monitor", "get_live_players", {})
                )
            
            if "data_source" in self.collaborating_agents:
                collection_tasks.append(
                    self._collect_from_agent("data_source", "get_live_streams", {"first": 10})
                )
        
        if request.include_trends:
            # 收集趋势数据
            if "data_source" in self.collaborating_agents:
                collection_tasks.append(
                    self._collect_from_agent("data_source", "get_trending_data", {})
                )
        
        # 总是收集系统状态（用于简报元信息）
        if "router" in self.collaborating_agents:
            collection_tasks.append(
                self._collect_from_agent("router", "get_system_status", {})
            )
        
        # 并发执行数据收集
        if collection_tasks:
            logger.info(f"并发执行 {len(collection_tasks)} 个数据收集任务")
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"数据收集任务异常: {result}")
                    processed_results.append(AgentCollaborationResult(
                        agent_name="unknown",
                        success=False,
                        data=None,
                        processing_time=0.0,
                        error=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
        else:
            logger.warning("没有可用的协作Agent，使用降级模式")
            return []

    async def _collect_from_agent(self, agent_name: str, method_name: str, 
                                 parameters: Dict[str, Any]) -> AgentCollaborationResult:
        """从单个Agent收集数据"""
        start_time = datetime.now()
        
        try:
            agent = self.collaborating_agents.get(agent_name)
            if not agent:
                raise Exception(f"Agent {agent_name} 未注册")
            
            # 检查Agent是否有指定方法
            method = getattr(agent, method_name, None)
            if not method:
                raise Exception(f"Agent {agent_name} 不支持方法 {method_name}")
            
            logger.debug(f"调用 {agent_name}.{method_name}({parameters})")
            
            # 执行方法调用（支持超时）
            result = await asyncio.wait_for(
                method(**parameters),
                timeout=10.0  # 10秒超时
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录响应时间
            self.collaboration_stats["agent_response_times"][agent_name].append(processing_time)
            
            return AgentCollaborationResult(
                agent_name=agent_name,
                success=True,
                data=result,
                processing_time=processing_time,
                metadata={"method": method_name, "parameters": parameters}
            )
            
        except asyncio.TimeoutError:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Agent {agent_name} 调用超时"
            logger.error(error_msg)
            
            return AgentCollaborationResult(
                agent_name=agent_name,
                success=False,
                data=None,
                processing_time=processing_time,
                error=error_msg
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Agent {agent_name} 调用失败: {str(e)}"
            logger.error(error_msg)
            
            return AgentCollaborationResult(
                agent_name=agent_name,
                success=False,
                data=None,
                processing_time=processing_time,
                error=error_msg
            )

    async def _aggregate_collaboration_results(self, results: List[AgentCollaborationResult]) -> Dict[str, Any]:
        """聚合协作结果"""
        aggregated = {
            "live_data": [],
            "trend_data": [],
            "system_data": {},
            "successful_agents": [],
            "failed_agents": [],
            "total_processing_time": 0.0,
            "data_sources": []
        }
        
        for result in results:
            aggregated["total_processing_time"] += result.processing_time
            
            if result.success:
                aggregated["successful_agents"].append(result.agent_name)
                
                # 根据Agent类型和数据内容进行分类聚合
                if result.agent_name in ["live_monitor", "data_source"]:
                    if result.metadata and result.metadata.get("method") in ["get_live_players", "get_live_streams"]:
                        aggregated["live_data"].extend(self._normalize_live_data(result.data))
                    elif result.metadata and result.metadata.get("method") == "get_trending_data":
                        aggregated["trend_data"].append(result.data)
                
                elif result.agent_name == "router":
                    aggregated["system_data"] = result.data
                
                # 记录数据源
                if hasattr(result.data, 'source'):
                    aggregated["data_sources"].append(result.data.source)
                elif isinstance(result.data, dict) and 'source' in result.data:
                    aggregated["data_sources"].append(result.data['source'])
                else:
                    aggregated["data_sources"].append(result.agent_name)
            else:
                aggregated["failed_agents"].append({
                    "agent": result.agent_name,
                    "error": result.error
                })
        
        # 应用聚合策略
        for data_type, strategy in self.aggregation_strategies.items():
            if data_type in aggregated:
                aggregated[data_type] = await strategy(aggregated[data_type])
        
        logger.info(f"数据聚合完成 - 成功: {len(aggregated['successful_agents'])}, 失败: {len(aggregated['failed_agents'])}")
        
        return aggregated

    def _normalize_live_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """标准化直播数据格式"""
        normalized = []
        
        if isinstance(raw_data, list):
            for item in raw_data:
                if hasattr(item, '__dict__'):
                    # 对象转字典
                    normalized.append(vars(item))
                elif isinstance(item, dict):
                    normalized.append(item)
        elif hasattr(raw_data, 'data') and isinstance(raw_data.data, list):
            # QueryResponse对象
            for item in raw_data.data:
                if hasattr(item, '__dict__'):
                    normalized.append(vars(item))
                elif isinstance(item, dict):
                    normalized.append(item)
        elif isinstance(raw_data, dict):
            normalized.append(raw_data)
        
        return normalized

    # 聚合策略方法
    async def _aggregate_live_data(self, live_data: List) -> Dict[str, Any]:
        """聚合直播数据"""
        if not live_data:
            return {"streams": [], "total_viewers": 0, "total_streamers": 0}
        
        # 去重和排序
        unique_streams = {}
        for stream in live_data:
            user_key = stream.get('user_name') or stream.get('user_login', 'unknown')
            if user_key not in unique_streams:
                unique_streams[user_key] = stream
            else:
                # 保留观众数更高的记录
                if stream.get('viewer_count', 0) > unique_streams[user_key].get('viewer_count', 0):
                    unique_streams[user_key] = stream
        
        sorted_streams = sorted(
            unique_streams.values(),
            key=lambda x: x.get('viewer_count', 0),
            reverse=True
        )
        
        total_viewers = sum(s.get('viewer_count', 0) for s in sorted_streams)
        
        return {
            "streams": sorted_streams[:10],  # 取前10个
            "total_viewers": total_viewers,
            "total_streamers": len(sorted_streams),
            "top_games": self._extract_top_games(sorted_streams)
        }

    async def _aggregate_trend_data(self, trend_data: List) -> Dict[str, Any]:
        """聚合趋势数据"""
        if not trend_data:
            return {"trends": [], "categories": []}
        
        # 合并所有趋势数据
        all_trends = []
        categories = set()
        
        for data in trend_data:
            if isinstance(data, list):
                all_trends.extend(data)
            elif isinstance(data, dict):
                if 'trends' in data:
                    all_trends.extend(data['trends'])
                if 'categories' in data:
                    categories.update(data['categories'])
        
        return {
            "trends": all_trends[:5],  # 取前5个趋势
            "categories": list(categories)
        }

    async def _aggregate_system_data(self, system_data: Dict) -> Dict[str, Any]:
        """聚合系统数据"""
        if not system_data:
            return {"status": "unknown", "agents": [], "performance": {}}
        
        return {
            "status": system_data.get("router_status", "unknown"),
            "agents": list(system_data.get("agents", {}).keys()),
            "llm_status": system_data.get("llm_status", {}),
            "timestamp": system_data.get("timestamp")
        }

    def _extract_top_games(self, streams: List[Dict]) -> List[Dict[str, Any]]:
        """提取热门游戏"""
        game_stats = {}
        
        for stream in streams:
            game_name = stream.get('game_name', '未知游戏')
            if game_name not in game_stats:
                game_stats[game_name] = {
                    "name": game_name,
                    "streamers": 0,
                    "total_viewers": 0
                }
            
            game_stats[game_name]["streamers"] += 1
            game_stats[game_name]["total_viewers"] += stream.get('viewer_count', 0)
        
        # 按总观众数排序
        sorted_games = sorted(
            game_stats.values(),
            key=lambda x: x["total_viewers"],
            reverse=True
        )
        
        return sorted_games[:5]

    async def _generate_intelligent_briefing(self, aggregated_data: Dict[str, Any], 
                                           request: BriefingRequest) -> str:
        """生成智能简报内容"""
        try:
            # 选择简报模板
            template_key = self._select_briefing_template(aggregated_data, request)
            template_func = self.briefing_templates.get(template_key, self._generate_daily_briefing)
            
            # 生成基础简报
            base_briefing = await template_func(aggregated_data, request)
            
            # 使用LLM增强简报（如果启用）
            if self.llm_enhancement_enabled:
                enhanced_briefing = await self._enhance_briefing_with_llm(
                    base_briefing, aggregated_data, request
                )
                return enhanced_briefing if enhanced_briefing else base_briefing
            
            return base_briefing
            
        except Exception as e:
            logger.error(f"智能简报生成失败: {e}")
            return await self._generate_basic_briefing(aggregated_data)

    def _select_briefing_template(self, aggregated_data: Dict[str, Any], 
                                 request: BriefingRequest) -> str:
        """选择合适的简报模板"""
        live_data = aggregated_data.get("live_data", {})
        trend_data = aggregated_data.get("trend_data", {})
        
        # 根据数据特征选择模板
        if request.include_trends and trend_data.get("trends"):
            return "trend_analysis"
        elif live_data.get("total_streamers", 0) > 5:
            return "live_focus"
        else:
            return "daily"

    # 简报模板方法
    async def _generate_daily_briefing(self, aggregated_data: Dict[str, Any], 
                                     request: BriefingRequest) -> str:
        """生成日常简报"""
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        
        live_data = aggregated_data.get("live_data", {})
        system_data = aggregated_data.get("system_data", {})
        
        briefing = f"""📰 【小游探智能简报】{date_str}

{'='*50}

🔥 **实时直播概况**
"""
        
        streams = live_data.get("streams", [])
        total_viewers = live_data.get("total_viewers", 0)
        total_streamers = live_data.get("total_streamers", 0)
        
        if streams:
            briefing += f"📊 当前直播: {total_streamers} 位主播在线\n"
            briefing += f"👥 总观众数: {total_viewers:,} 人\n\n"
            
            briefing += "🌟 **热门直播**:\n"
            for i, stream in enumerate(streams[:5], 1):
                user_name = stream.get('user_name', '未知主播')
                game_name = stream.get('game_name', '未知游戏')
                viewers = stream.get('viewer_count', 0)
                title = stream.get('title', '无标题')
                
                briefing += f"{i}. **{user_name}** - {game_name}\n"
                briefing += f"   👥 {viewers:,} 观众 | 📝 {title[:30]}{'...' if len(title) > 30 else ''}\n"
                
                if stream.get('live_url'):
                    briefing += f"   🔗 {stream['live_url']}\n"
                briefing += "\n"
        else:
            briefing += "📺 当前暂无主播直播\n\n"
        
        # 热门游戏统计
        top_games = live_data.get("top_games", [])
        if top_games:
            briefing += "🎮 **热门游戏排行**:\n"
            for i, game in enumerate(top_games[:3], 1):
                briefing += f"{i}. {game['name']} - {game['streamers']}位主播, {game['total_viewers']:,}观众\n"
            briefing += "\n"
        
        # 系统状态
        if system_data:
            briefing += f"🖥️ **系统状态**: {system_data.get('status', '正常')}\n"
            briefing += f"🤖 **协作Agent**: {len(aggregated_data.get('successful_agents', []))}个在线\n"
        
        briefing += f"\n{'='*50}\n"
        briefing += f"📊 数据来源: {', '.join(set(aggregated_data.get('data_sources', ['系统'])))}\n"
        briefing += f"⏰ 生成时间: {now.strftime('%H:%M:%S')}\n"
        briefing += f"💡 提示: 询问具体主播状态或生成趋势分析\n"
        
        return briefing

    async def _generate_live_focus_briefing(self, aggregated_data: Dict[str, Any], 
                                          request: BriefingRequest) -> str:
        """生成直播焦点简报"""
        now = datetime.now()
        live_data = aggregated_data.get("live_data", {})
        streams = live_data.get("streams", [])
        
        briefing = f"""🔴 【直播焦点简报】{now.strftime('%H:%M')}

🌟 **当前热门直播** ({len(streams)} 个直播间)
"""
        
        total_viewers = live_data.get("total_viewers", 0)
        briefing += f"👥 总观众: {total_viewers:,} 人\n\n"
        
        # 按观众数分组显示
        if streams:
            high_viewers = [s for s in streams if s.get('viewer_count', 0) >= 10000]
            medium_viewers = [s for s in streams if 1000 <= s.get('viewer_count', 0) < 10000]
            
            if high_viewers:
                briefing += "🔥 **超高人气** (1万+观众):\n"
                for stream in high_viewers[:3]:
                    user_name = stream.get('user_name', '未知')
                    viewers = stream.get('viewer_count', 0)
                    game_name = stream.get('game_name', '未知游戏')
                    briefing += f"• {user_name} - {viewers:,}观众 - {game_name}\n"
                briefing += "\n"
            
            if medium_viewers:
                briefing += "⭐ **高人气** (1千-1万观众):\n"
                for stream in medium_viewers[:5]:
                    user_name = stream.get('user_name', '未知')
                    viewers = stream.get('viewer_count', 0)
                    game_name = stream.get('game_name', '未知游戏')
                    briefing += f"• {user_name} - {viewers:,}观众 - {game_name}\n"
                briefing += "\n"
        
        # 游戏分布
        top_games = live_data.get("top_games", [])
        if top_games:
            briefing += "🎮 **游戏热度分布**:\n"
            for game in top_games[:5]:
                briefing += f"• {game['name']}: {game['streamers']}主播, {game['total_viewers']:,}观众\n"
        
        briefing += f"\n📊 数据更新: {now.strftime('%H:%M:%S')}"
        
        return briefing

    async def _generate_trend_analysis_briefing(self, aggregated_data: Dict[str, Any], 
                                              request: BriefingRequest) -> str:
        """生成趋势分析简报"""
        now = datetime.now()
        trend_data = aggregated_data.get("trend_data", {})
        live_data = aggregated_data.get("live_data", {})
        
        briefing = f"""📈 【游戏圈趋势分析】{now.strftime('%Y-%m-%d %H:%M')}

🔍 **趋势洞察**
"""
        
        trends = trend_data.get("trends", [])
        if trends:
            briefing += "📊 **热门趋势**:\n"
            for i, trend in enumerate(trends[:5], 1):
                if isinstance(trend, dict):
                    name = trend.get('name', trend.get('title', '未知趋势'))
                    briefing += f"{i}. {name}\n"
                else:
                    briefing += f"{i}. {str(trend)}\n"
            briefing += "\n"
        
        # 直播数据趋势分析
        streams = live_data.get("streams", [])
        if streams:
            briefing += "🎮 **直播趋势分析**:\n"
            
            # 游戏类型分析
            top_games = live_data.get("top_games", [])
            if top_games:
                briefing += f"• 最热门游戏: {top_games[0]['name']} ({top_games[0]['total_viewers']:,}观众)\n"
                
                if len(top_games) > 1:
                    growth_games = [g for g in top_games[1:3] if g['streamers'] >= 2]
                    if growth_games:
                        briefing += f"• 上升趋势: {', '.join([g['name'] for g in growth_games])}\n"
            
            # 观众分布分析
            total_viewers = live_data.get("total_viewers", 0)
            avg_viewers = total_viewers // len(streams) if streams else 0
            briefing += f"• 平均观众数: {avg_viewers:,} 人/直播间\n"
            
            high_viewer_streams = [s for s in streams if s.get('viewer_count', 0) > avg_viewers * 2]
            if high_viewer_streams:
                briefing += f"• 超高人气主播: {len(high_viewer_streams)}位 (超过平均值2倍)\n"
        
        briefing += f"\n📊 分析基于 {len(aggregated_data.get('successful_agents', []))} 个数据源"
        briefing += f"\n⏰ 分析时间: {now.strftime('%H:%M:%S')}"
        
        return briefing
    
    async def _generate_basic_briefing(self, aggregated_data: Dict[str, Any]) -> str:
        """生成基础简报（降级模式）"""
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        
        briefing = f"📰 【小游探简报】{date_str}\n\n"
        
        live_data = aggregated_data.get("live_data", {})
        streams = live_data.get("streams", [])
        
        if streams:
            briefing += f"🔥 当前直播: {len(streams)} 位主播在线\n"
            briefing += f"👥 总观众: {live_data.get('total_viewers', 0):,} 人\n\n"
            
            for i, stream in enumerate(streams[:3], 1):
                user_name = stream.get('user_name', '未知')
                viewers = stream.get('viewer_count', 0)
                briefing += f"{i}. {user_name} - {viewers:,} 观众\n"
        else:
            briefing += "📺 当前暂无主播直播\n"
        
        briefing += f"\n⏰ {now.strftime('%H:%M:%S')} | 基础模式"
        
        return briefing

    async def _optimize_briefing_output(self, briefing_content: str, 
                                      aggregated_data: Dict[str, Any], 
                                      request: BriefingRequest) -> str:
        """优化简报输出"""
        try:
            # 添加个性化元素
            if request.requester != "unknown":
                briefing_content = f"👋 {request.requester}，为您生成的简报：\n\n" + briefing_content
            
            # 添加协作统计信息（调试模式）
            if len(aggregated_data.get("failed_agents", [])) > 0:
                briefing_content += f"\n⚠️ 部分数据源暂时不可用，已使用备用数据"
            
            # 添加交互提示
            briefing_content += f"\n\n💬 回复 'trend' 查看趋势分析，'stats' 查看系统统计"
            
            return briefing_content
            
        except Exception as e:
            logger.error(f"简报输出优化失败: {e}")
            return briefing_content

    async def _generate_fallback_briefing(self, request: BriefingRequest, error: str) -> str:
        """生成降级简报"""
        now = datetime.now()
        
        briefing = f"""📰 【小游探简报】{now.strftime('%Y年%m月%d日')}

⚠️ 系统正在维护中，为您提供基础服务

🤖 **系统状态**: 部分功能受限
📊 **数据更新**: {now.strftime('%H:%M:%S')}
🔧 **技术信息**: {error[:50]}...

💡 **建议操作**:
• 稍后重试生成完整简报
• 查询具体主播状态
• 联系技术支持

📞 如需帮助，请回复 'help' 获取更多信息"""

        return briefing

    # 特定功能方法
    async def generate_player_summary(self, player_name: str, requester: str = "unknown") -> str:
        """生成特定主播摘要（多Agent协作版）"""
        try:
            logger.info(f"生成主播摘要: {player_name}")
            
            # 从多个Agent收集主播数据
            collection_tasks = []
            
            if "live_monitor" in self.collaborating_agents:
                collection_tasks.append(
                    self._collect_from_agent("live_monitor", "check_player_status", {"player_name": player_name})
                )
            
            if "data_source" in self.collaborating_agents:
                collection_tasks.append(
                    self._collect_from_agent("data_source", "get_live_streams", {"user_login": player_name.lower(), "first": 1})
                )
            
            if collection_tasks:
                results = await asyncio.gather(*collection_tasks, return_exceptions=True)
                
                # 处理结果
                player_data = None
                for result in results:
                    if isinstance(result, AgentCollaborationResult) and result.success:
                        if result.data:
                            if isinstance(result.data, dict) and result.data.get("is_live"):
                                player_data = result.data
                                break
                            elif isinstance(result.data, list) and result.data:
                                # 转换数据源格式
                                stream = result.data[0]
                                player_data = {
                                    "is_live": True,
                                    "user_name": stream.get('user_name', player_name),
                                    "title": stream.get('title', '无标题'),
                                    "viewer_count": stream.get('viewer_count', 0),
                                    "game_name": stream.get('game_name', '未知游戏'),
                                    "live_url": stream.get('live_url', '')
                                }
                                break
                
                if player_data and player_data.get("is_live"):
                    # 生成详细摘要
                    summary = await self._format_player_summary(player_name, player_data)
                    
                    # LLM增强
                    if self.llm_enhancement_enabled:
                        enhanced = await self._enhance_summary_with_llm(summary, player_data)
                        return enhanced if enhanced else summary
                    
                    return summary
                else:
                    return f"📺 {player_name} 当前未在直播\n💡 你可以查询其他主播或生成游戏简报"
            
            return f"❌ 无法获取 {player_name} 的直播信息，请稍后重试"
            
        except Exception as e:
            logger.error(f"生成主播摘要失败: {e}")
            return f"❌ 生成 {player_name} 摘要时出错：{str(e)}"

    async def _format_player_summary(self, player_name: str, player_data: Dict) -> str:
        """格式化主播摘要"""
        summary = f"""🎮 **{player_name}** 直播中

📝 **直播标题**: {player_data.get('title', '无标题')}
👥 **当前观众**: {player_data.get('viewer_count', 0):,} 人
🎮 **游戏类型**: {player_data.get('game_name', '未知游戏')}
"""
        
        if player_data.get('live_url'):
            summary += f"🔗 **直播链接**: {player_data['live_url']}\n"
        
        # 添加观众数分析
        viewers = player_data.get('viewer_count', 0)
        if viewers >= 50000:
            summary += "🔥 **人气等级**: 超高人气主播\n"
        elif viewers >= 10000:
            summary += "⭐ **人气等级**: 高人气主播\n"
        elif viewers >= 1000:
            summary += "📈 **人气等级**: 中等人气主播\n"
        
        summary += f"\n⏰ 数据更新: {datetime.now().strftime('%H:%M:%S')}"
        
        return summary

    async def generate_trend_briefing(self, request: BriefingRequest) -> str:
        """生成趋势分析简报"""
        request.include_trends = True
        request.include_live_data = True
        
        return await self.generate_collaborative_briefing(request)

    # LLM增强方法
    async def _enhance_briefing_with_llm(self, base_briefing: str, 
                                       aggregated_data: Dict[str, Any], 
                                       request: BriefingRequest) -> Optional[str]:
        """使用LLM增强简报内容"""
        try:
            # 准备上下文数据
            context_data = {
                "live_streams": aggregated_data.get("live_data", {}).get("streams", [])[:5],
                "total_streamers": aggregated_data.get("live_data", {}).get("total_streamers", 0),
                "total_viewers": aggregated_data.get("live_data", {}).get("total_viewers", 0),
                "top_games": aggregated_data.get("live_data", {}).get("top_games", [])[:3],
                "trends": aggregated_data.get("trend_data", {}).get("trends", [])[:3],
                "system_status": aggregated_data.get("system_data", {}),
                "request_type": request.time_range,
                "timestamp": datetime.now().isoformat()
            }
            
            # 调用LLM增强
            llm_response = await llm_client.process_with_fallback(
                "briefing_generation",
                base_briefing,
                {"data": context_data, "request": request.__dict__}
            )
            
            if llm_response.success:
                logger.info(f"简报已通过LLM增强 (来源: {llm_response.source})")
                return llm_response.content
            else:
                logger.warning(f"LLM简报增强失败: {llm_response.error}")
                return None
                
        except Exception as e:
            logger.error(f"简报LLM增强异常: {e}")
            return None
    
    async def _enhance_summary_with_llm(self, basic_summary: str, player_data: Dict) -> Optional[str]:
        """使用LLM增强主播摘要"""
        try:
            # 调用LLM增强响应
            llm_response = await llm_client.process_with_fallback(
                "response_enhancement",
                basic_summary,
                {"stream_data": player_data, "type": "player_summary"}
            )
            
            if llm_response.success:
                logger.info(f"摘要已通过LLM增强 (来源: {llm_response.source})")
                return llm_response.content
            else:
                logger.warning(f"LLM摘要增强失败: {llm_response.error}")
                return None
                
        except Exception as e:
            logger.error(f"摘要LLM增强异常: {e}")
            return None

    # 系统管理和监控方法
    async def _check_collaborating_agents(self):
        """检查协作Agent状态"""
        logger.info("检查协作Agent状态...")
        
        available_agents = []
        unavailable_agents = []
        
        for agent_name, agent in self.collaborating_agents.items():
            try:
                # 简单的健康检查
                if hasattr(agent, 'health_check'):
                    is_healthy = await agent.health_check()
                elif hasattr(agent, 'agent_id'):
                    is_healthy = True  # 假设OpenAgents标准Agent健康
                else:
                    is_healthy = True  # 假设健康
                
                if is_healthy:
                    available_agents.append(agent_name)
                else:
                    unavailable_agents.append(agent_name)
                    
            except Exception as e:
                logger.error(f"检查Agent {agent_name} 状态失败: {e}")
                unavailable_agents.append(agent_name)
        
        logger.info(f"协作Agent状态 - 可用: {len(available_agents)}, 不可用: {len(unavailable_agents)}")
        
        if unavailable_agents:
            logger.warning(f"不可用的Agent: {', '.join(unavailable_agents)}")

    async def _get_collaborating_agents_status(self) -> str:
        """获取协作Agent状态报告"""
        status_report = "🤖 **协作Agent状态报告**\n\n"
        
        if not self.collaborating_agents:
            return status_report + "❌ 未注册任何协作Agent"
        
        for agent_name, agent in self.collaborating_agents.items():
            try:
                # 检查Agent状态
                if hasattr(agent, 'agent_id'):
                    status_icon = "🟢"
                    status_text = "在线"
                else:
                    status_icon = "🟡"
                    status_text = "未知"
                
                # 获取响应时间统计
                response_times = self.collaboration_stats["agent_response_times"].get(agent_name, [])
                if response_times:
                    avg_time = sum(response_times[-10:]) / len(response_times[-10:])  # 最近10次平均
                    status_report += f"{status_icon} **{agent_name}**: {status_text} (平均响应: {avg_time:.2f}s)\n"
                else:
                    status_report += f"{status_icon} **{agent_name}**: {status_text}\n"
                
            except Exception as e:
                status_report += f"🔴 **{agent_name}**: 异常 ({str(e)[:30]}...)\n"
        
        # 添加协作统计
        total_requests = self.collaboration_stats["total_requests"]
        successful = self.collaboration_stats["successful_collaborations"]
        
        if total_requests > 0:
            success_rate = (successful / total_requests) * 100
            status_report += f"\n📊 **协作统计**:\n"
            status_report += f"• 总请求: {total_requests}\n"
            status_report += f"• 成功率: {success_rate:.1f}%\n"
        
        return status_report

    def _format_collaboration_stats(self) -> str:
        """格式化协作统计信息"""
        stats = self.collaboration_stats
        
        if stats["total_requests"] == 0:
            return "📊 **协作统计**: 暂无协作记录"
        
        success_rate = (stats["successful_collaborations"] / stats["total_requests"]) * 100
        
        report = f"""📊 **Briefing Agent 协作统计**

🔢 **总体数据**:
• 总协作请求: {stats["total_requests"]}
• 成功协作: {stats["successful_collaborations"]} ({success_rate:.1f}%)
• 聚合成功率: {stats["aggregation_success_rate"]:.1f}%

⚡ **Agent响应时间** (最近10次平均):"""
        
        for agent_name, times in stats["agent_response_times"].items():
            if times:
                recent_times = times[-10:]
                avg_time = sum(recent_times) / len(recent_times)
                report += f"\n• {agent_name}: {avg_time:.2f}s"
        
        report += f"\n\n📅 **统计周期**: 自 {stats['last_reset'].strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report

    def _get_briefing_help(self) -> str:
        """获取简报帮助信息"""
        return f"""🤖 **Briefing Agent 帮助**

📋 **可用命令**:
• `briefing` / `简报` - 生成智能日报
• `summary <主播名>` - 生成主播直播摘要
• `trend` - 生成趋势分析简报
• `stats` - 查看协作统计
• `agents` - 查看协作Agent状态

🔧 **协作Agent**: {len(self.collaborating_agents)} 个已注册
🧠 **LLM增强**: {'启用' if self.llm_enhancement_enabled else '禁用'}

💡 **示例**:
• `briefing` - 生成今日游戏圈简报
• `summary Faker` - 查看Faker直播状态
• `trend` - 分析游戏圈趋势

🎯 **特色功能**:
• 多Agent数据协作收集
• 智能结果聚合分析
• LLM增强内容生成
• 个性化简报定制"""

    # 向后兼容方法
    async def generate_briefing(self, time_range: str = "today") -> str:
        """向后兼容的简报生成方法"""
        request = BriefingRequest(
            time_range=time_range,
            include_trends=True,
            include_live_data=True,
            requester="legacy"
        )
        
        return await self.generate_collaborative_briefing(request)

    async def generate_live_summary(self, player_name: str) -> str:
        """向后兼容的主播摘要方法"""
        return await self.generate_player_summary(player_name, "legacy")

    async def add_custom_event(self, title: str, content: str, importance: int = 5):
        """
        添加自定义事件（用于手动添加重要新闻）

        Args:
            title: 事件标题
            content: 事件内容
            importance: 重要性（1-10）
        """
        # TODO: 实现事件存储和简报集成
        logger.info(f"添加自定义事件: {title} (重要性: {importance})")
        pass
    
    async def get_intelligence_status(self) -> Dict[str, Any]:
        """获取智能系统状态"""
        llm_stats = llm_client.get_usage_stats()
        
        return {
            "llm_enabled": self.use_llm,
            "llm_enhancement_enabled": self.llm_enhancement_enabled,
            "llm_available": llm_stats['remaining_calls'] > 0,
            "daily_usage": f"{llm_stats['daily_calls']}/{llm_stats['daily_limit']}",
            "cache_size": llm_stats['cache_size'],
            "fallback_active": llm_stats['remaining_calls'] == 0,
            "collaborating_agents": len(self.collaborating_agents),
            "collaboration_stats": self.collaboration_stats
        }

    def reset_collaboration_stats(self):
        """重置协作统计"""
        self.collaboration_stats = {
            "total_requests": 0,
            "successful_collaborations": 0,
            "agent_response_times": {name: [] for name in self.collaborating_agents.keys()},
            "aggregation_success_rate": 0.0,
            "last_reset": datetime.now()
        }
        logger.info("协作统计已重置")

    async def on_shutdown(self):
        """Agent 关闭时调用"""
        logger.info(f"🛑 {self.agent_id} 关闭")
        
        # 输出最终协作统计
        total = self.collaboration_stats["total_requests"]
        if total > 0:
            success_rate = (self.collaboration_stats["successful_collaborations"] / total) * 100
            logger.info(f"最终协作统计 - 总请求: {total}, 成功率: {success_rate:.1f}%")


# 测试代码
async def test_briefing_agent():
    """测试重构后的多Agent协作简报Agent"""
    # 创建模拟的协作Agent
    class MockLiveMonitor:
        async def get_live_players(self):
            return [
                {"user_name": "Uzi", "viewer_count": 200000, "title": "深夜Rank训练", "live_url": "https://huya.com/995888", "game_name": "英雄联盟"},
                {"user_name": "Faker", "viewer_count": 150000, "title": "T1训练赛", "live_url": "https://huya.com/123456", "game_name": "英雄联盟"},
                {"user_name": "大司马", "viewer_count": 80000, "title": "金牌讲师在线教学", "live_url": "https://huya.com/dasima", "game_name": "英雄联盟"}
            ]
        
        async def check_player_status(self, player_name):
            players = await self.get_live_players()
            for player in players:
                if player["user_name"].lower() == player_name.lower():
                    return {
                        "is_live": True,
                        "user_name": player["user_name"],
                        "title": player["title"],
                        "viewer_count": player["viewer_count"],
                        "game_name": player["game_name"],
                        "live_url": player["live_url"]
                    }
            return {"is_live": False}

    class MockDataSource:
        async def get_live_streams(self, **kwargs):
            return [
                {"user_name": "Shroud", "viewer_count": 45000, "game_name": "Valorant", "title": "Ranked Grind"},
                {"user_name": "xQc", "viewer_count": 35000, "game_name": "Variety", "title": "React Content"}
            ]
        
        async def get_trending_data(self):
            return [
                {"name": "League of Legends World Championship", "category": "esports"},
                {"name": "Valorant Champions", "category": "esports"}
            ]

    class MockRouter:
        async def get_system_status(self):
            return {
                "router_status": "online",
                "agents": {"live_monitor": True, "data_source": True, "briefing": True},
                "llm_status": {"available": True, "provider": "openai"},
                "timestamp": datetime.now().isoformat()
            }

    # 创建并配置Briefing Agent
    briefing_agent = BriefingAgent()
    
    # 注册协作Agent
    briefing_agent.register_collaborating_agent("live_monitor", MockLiveMonitor())
    briefing_agent.register_collaborating_agent("data_source", MockDataSource())
    briefing_agent.register_collaborating_agent("router", MockRouter())
    
    await briefing_agent.on_startup()

    print("🧪 测试重构后的多Agent协作简报Agent...")
    
    # 测试协作式简报生成
    print("\n1. 测试协作式简报生成:")
    request = BriefingRequest(time_range="today", requester="test_user")
    briefing = await briefing_agent.generate_collaborative_briefing(request)
    print(briefing)
    
    # 测试主播摘要
    print("\n2. 测试主播摘要:")
    summary = await briefing_agent.generate_player_summary("Faker", "test_user")
    print(summary)
    
    # 测试趋势分析简报
    print("\n3. 测试趋势分析简报:")
    trend_request = BriefingRequest(time_range="recent", include_trends=True, requester="test_user")
    trend_briefing = await briefing_agent.generate_trend_briefing(trend_request)
    print(trend_briefing)
    
    # 显示协作统计
    print("\n4. 协作统计:")
    stats = briefing_agent._format_collaboration_stats()
    print(stats)
    
    # 显示Agent状态
    print("\n5. 协作Agent状态:")
    agent_status = await briefing_agent._get_collaborating_agents_status()
    print(agent_status)
    
    # 显示智能系统状态
    print("\n6. 智能系统状态:")
    intelligence_status = await briefing_agent.get_intelligence_status()
    print(f"LLM可用: {intelligence_status['llm_available']}")
    print(f"协作Agent数量: {intelligence_status['collaborating_agents']}")
    print(f"协作成功率: {intelligence_status['collaboration_stats']['successful_collaborations']}/{intelligence_status['collaboration_stats']['total_requests']}")
    
    await briefing_agent.on_shutdown()


if __name__ == "__main__":
    asyncio.run(test_briefing_agent())
