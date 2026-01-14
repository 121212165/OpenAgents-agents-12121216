# LLM客户端 - OpenRouter集成
"""
智能降级的LLM客户端
支持OpenRouter API调用，带有智能降级和缓存机制
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import aiohttp

@dataclass
class LLMResponse:
    """LLM响应结果"""
    content: str
    success: bool
    source: str  # "llm" or "fallback"
    tokens_used: int = 0
    response_time: float = 0.0
    error: Optional[str] = None

class LLMClient:
    """智能降级的LLM客户端"""
    
    def __init__(self):
        # 检测使用的LLM方案
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "")
        
        # 优先级：OpenRouter > Claude > OpenAI > Ollama
        if self.openai_key and "openrouter.ai" in base_url:
            # OpenRouter配置
            self.api_key = self.openai_key
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            self.model = os.getenv("OPENAI_MODEL", "xiaomi/mimo-v2-flash:free")
            self.provider = "openrouter"
        elif self.anthropic_key:
            # Claude配置
            self.api_key = self.anthropic_key
            self.base_url = "https://api.anthropic.com"
            self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            self.provider = "claude"
        elif self.openai_key and base_url:
            # OpenAI或其他兼容API配置
            self.api_key = self.openai_key
            self.base_url = base_url
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            if "localhost" in base_url or "127.0.0.1" in base_url:
                self.provider = "ollama"
            else:
                self.provider = "openai"
        elif self.openai_key:
            # 默认OpenAI配置
            self.api_key = self.openai_key
            self.base_url = "https://api.openai.com/v1"
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            self.provider = "openai"
        else:
            # 无API密钥，仅使用降级模式
            self.api_key = None
            self.base_url = None
            self.model = None
            self.provider = "fallback_only"
        
        # 配置参数
        self.daily_limit = int(os.getenv("LLM_DAILY_LIMIT", "45"))
        self.cache_ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "10"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
        # 使用限制
        self.call_count = 0
        self.last_reset = datetime.now().date()
        
        # 缓存机制
        self.response_cache = {}
        
        # 降级响应模板
        self.fallback_templates = {
            "intent_classification": self._classify_intent_fallback,
            "briefing_generation": self._generate_briefing_fallback,
            "response_enhancement": self._enhance_response_fallback,
            "entity_extraction": self._extract_entities_fallback
        }
        
        logger.info(f"LLM客户端初始化 - 提供商: {self.provider}, 模型: {self.model}")
    
    def _reset_daily_counter(self):
        """重置每日计数器"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.call_count = 0
            self.last_reset = today
            logger.info("每日LLM调用计数器已重置")
    
    def can_use_llm(self) -> bool:
        """检查是否可以使用LLM"""
        self._reset_daily_counter()
        
        if not self.api_key:
            return False
        
        if self.call_count >= self.daily_limit:
            logger.warning(f"已达到每日LLM调用限制: {self.call_count}/{self.daily_limit}")
            return False
        
        return True
    
    def _get_cache_key(self, task_type: str, content: str) -> str:
        """生成缓存键"""
        return f"{task_type}:{hash(content)}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """获取缓存响应"""
        if cache_key in self.response_cache:
            cached_item = self.response_cache[cache_key]
            
            # 检查是否过期
            if datetime.now() - cached_item["timestamp"] < timedelta(seconds=self.cache_ttl):
                logger.debug(f"LLM缓存命中: {cache_key}")
                return cached_item["response"]
            else:
                # 清理过期缓存
                del self.response_cache[cache_key]
        
        return None
    
    def _cache_response(self, cache_key: str, response: LLMResponse):
        """缓存响应"""
        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }
    
    async def process_with_fallback(self, task_type: str, content: str, 
                                  context: Dict[str, Any] = None) -> LLMResponse:
        """
        带降级的LLM处理
        
        Args:
            task_type: 任务类型 (intent_classification, briefing_generation, etc.)
            content: 输入内容
            context: 上下文信息
            
        Returns:
            LLMResponse对象
        """
        # 确保 context 不为 None
        if context is None:
            context = {}
            
        cache_key = self._get_cache_key(task_type, content)
        
        # 1. 检查缓存
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        # 2. 尝试LLM调用
        if self.can_use_llm():
            try:
                response = await self._call_llm(task_type, content, context)
                if response.success:
                    self._cache_response(cache_key, response)
                    return response
            except Exception as e:
                logger.warning(f"LLM调用失败，降级到规则引擎: {e}")
        
        # 3. 降级到规则引擎
        fallback_func = self.fallback_templates.get(task_type)
        if fallback_func:
            response = fallback_func(content, context)
            self._cache_response(cache_key, response)
            return response
        
        # 4. 默认响应
        return LLMResponse(
            content="抱歉，暂时无法处理您的请求",
            success=False,
            source="fallback",
            error="No fallback handler available"
        )
    
    async def _call_llm(self, task_type: str, content: str, 
                       context: Dict[str, Any]) -> LLMResponse:
        """调用LLM API"""
        start_time = datetime.now()
        
        # 构建提示词
        prompt = self._build_prompt(task_type, content, context)
        
        try:
            if self.provider == "claude":
                return await self._call_claude(task_type, prompt, start_time)
            else:
                return await self._call_openai_compatible(task_type, prompt, start_time)
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return LLMResponse(
                content="",
                success=False,
                source="llm",
                response_time=response_time,
                error=str(e)
            )
    
    async def _call_claude(self, task_type: str, prompt: str, start_time: datetime) -> LLMResponse:
        """调用Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user", 
                    "content": f"{self._get_system_prompt(task_type)}\n\n{prompt}"
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # 更新调用计数
                    self.call_count += 1
                    
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    return LLMResponse(
                        content=data["content"][0]["text"],
                        success=True,
                        source="llm",
                        tokens_used=data.get("usage", {}).get("output_tokens", 0),
                        response_time=response_time
                    )
                else:
                    error_text = await resp.text()
                    raise Exception(f"Claude API错误 {resp.status}: {error_text}")
    
    async def _call_openai_compatible(self, task_type: str, prompt: str, start_time: datetime) -> LLMResponse:
        """调用OpenAI兼容API（OpenRouter、OpenAI、Ollama等）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter需要额外的头部
        if self.provider == "openrouter":
            headers.update({
                "HTTP-Referer": "https://github.com/yourusername/yougame-explorer",
                "X-Title": "YouGame Explorer"
            })
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._get_system_prompt(task_type)},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # 更新调用计数
                    self.call_count += 1
                    
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    return LLMResponse(
                        content=data["choices"][0]["message"]["content"],
                        success=True,
                        source="llm",
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        response_time=response_time
                    )
                else:
                    error_text = await resp.text()
                    raise Exception(f"API错误 {resp.status}: {error_text}")
    
    def _build_prompt(self, task_type: str, content: str, context: Dict[str, Any]) -> str:
        """构建任务特定的提示词"""
        prompts = {
            "intent_classification": f"""
分析用户查询的意图，从以下类别中选择最合适的：
- 直播查询：查询主播直播状态
- 简报生成：生成游戏圈简报
- 数据分析：分析游戏数据趋势
- 问候：打招呼或闲聊
- 其他：无法分类的查询

用户查询："{content}"

请返回JSON格式：
{{"intent": "意图类别", "confidence": 0.95, "entities": {{"主播名": "Faker"}}}}
""",
            
            "briefing_generation": f"""
基于以下游戏直播数据，生成一份简洁有趣的游戏圈简报：

数据：{context.get('data', {})}

要求：
1. 使用emoji增加趣味性
2. 突出重点数据和趋势
3. 保持简洁，不超过200字
4. 使用中文

请生成简报内容：
""",
            
            "response_enhancement": f"""
优化以下回复，使其更加生动有趣：

原始回复："{content}"
上下文：{context}

要求：
1. 保持原意不变
2. 添加合适的emoji
3. 使用更生动的表达
4. 保持专业性

优化后的回复：
""",
            
            "entity_extraction": f"""
从用户查询中提取关键实体：

查询："{content}"

请提取：
- 主播名称
- 游戏名称  
- 时间范围
- 平台名称

返回JSON格式：
{{"主播名": "Faker", "游戏": "英雄联盟", "时间": "今天", "平台": "虎牙"}}
"""
        }
        
        return prompts.get(task_type, content)
    
    def _get_system_prompt(self, task_type: str) -> str:
        """获取系统提示词"""
        return """你是小游探AI助手，专门处理游戏圈相关查询。
请根据用户需求提供准确、有用的回复。
保持回复简洁明了，使用中文回复。"""
    
    # 降级处理函数
    def _classify_intent_fallback(self, content: str, context: Dict) -> LLMResponse:
        """意图分类降级处理"""
        content_lower = content.lower()
        
        # 规则匹配
        if any(word in content_lower for word in ["直播", "开播", "在线", "live"]):
            intent = "直播查询"
            confidence = 0.9
        elif any(word in content_lower for word in ["简报", "汇总", "报告", "briefing"]):
            intent = "简报生成"
            confidence = 0.9
        elif any(word in content_lower for word in ["你好", "嗨", "hello", "hi"]):
            intent = "问候"
            confidence = 0.95
        else:
            intent = "其他"
            confidence = 0.6
        
        # 简单实体提取
        entities = {}
        known_streamers = ["Faker", "Uzi", "大司马", "TheShy", "Rookie"]
        for streamer in known_streamers:
            if streamer in content:
                entities["主播名"] = streamer
                break
        
        result = {
            "intent": intent,
            "confidence": confidence,
            "entities": entities
        }
        
        return LLMResponse(
            content=json.dumps(result, ensure_ascii=False),
            success=True,
            source="fallback"
        )
    
    def _generate_briefing_fallback(self, content: str, context: Dict) -> LLMResponse:
        """简报生成降级处理"""
        data = context.get('data', {})
        live_count = len(data.get('live_streams', []))
        
        briefing = f"""📰 【小游探简报】
        
🔥 当前直播: {live_count}位主播在线
📊 系统运行正常，数据更新及时
🎮 热门游戏: 英雄联盟、王者荣耀持续火热

💡 更多详情请查询具体主播状态"""
        
        return LLMResponse(
            content=briefing,
            success=True,
            source="fallback"
        )
    
    def _enhance_response_fallback(self, content: str, context: Dict) -> LLMResponse:
        """响应优化降级处理"""
        # 简单的emoji添加
        enhanced = content
        if "直播" in content:
            enhanced = f"🔴 {enhanced}"
        if "观众" in content or "人气" in content:
            enhanced = enhanced.replace("观众", "👥观众").replace("人气", "👥人气")
        
        return LLMResponse(
            content=enhanced,
            success=True,
            source="fallback"
        )
    
    def _extract_entities_fallback(self, content: str, context: Dict) -> LLMResponse:
        """实体提取降级处理"""
        entities = {}
        
        # 主播名提取
        known_streamers = ["Faker", "Uzi", "大司马", "TheShy", "Rookie", "PDD", "小团团"]
        for streamer in known_streamers:
            if streamer in content:
                entities["主播名"] = streamer
                break
        
        # 时间提取
        if "今天" in content:
            entities["时间"] = "今天"
        elif "最近" in content:
            entities["时间"] = "最近"
        
        # 平台提取
        if "虎牙" in content:
            entities["平台"] = "虎牙"
        elif "twitch" in content.lower():
            entities["平台"] = "Twitch"
        
        return LLMResponse(
            content=json.dumps(entities, ensure_ascii=False),
            success=True,
            source="fallback"
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "provider": self.provider,
            "model": self.model,
            "daily_calls": self.call_count,
            "daily_limit": self.daily_limit,
            "remaining_calls": max(0, self.daily_limit - self.call_count),
            "cache_size": len(self.response_cache),
            "last_reset": self.last_reset.isoformat(),
            "api_configured": self.api_key is not None,
            "fallback_only": self.provider == "fallback_only"
        }

# 全局实例
llm_client = LLMClient()

# 测试代码
async def test_llm_client():
    """测试LLM客户端"""
    print("🧪 测试LLM客户端...")
    
    # 测试意图分类
    print("\n1. 测试意图分类:")
    result = await llm_client.process_with_fallback(
        "intent_classification", 
        "Faker在直播吗？"
    )
    print(f"   结果: {result.content}")
    print(f"   来源: {result.source}")
    
    # 测试简报生成
    print("\n2. 测试简报生成:")
    context = {
        "data": {
            "live_streams": [
                {"user_name": "Faker", "viewer_count": 45000},
                {"user_name": "Uzi", "viewer_count": 30000}
            ]
        }
    }
    result = await llm_client.process_with_fallback(
        "briefing_generation",
        "生成简报",
        context
    )
    print(f"   结果: {result.content}")
    print(f"   来源: {result.source}")
    
    # 显示使用统计
    print(f"\n📊 使用统计: {llm_client.get_usage_stats()}")

if __name__ == "__main__":
    asyncio.run(test_llm_client())