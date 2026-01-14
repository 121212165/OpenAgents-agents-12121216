# API 参考文档

**版本**: MVP v1.0  
**更新日期**: 2026-01-14

## 目录

- [概述](#概述)
- [核心Agent](#核心agent)
  - [RouterAgent](#routeragent)
  - [LiveMonitorAgent](#livemonitoragent)
  - [BriefingAgent](#briefingagent)
  - [DataSourceAgent](#datasourceagent)
- [工具类](#工具类)
  - [LLMClient](#llmclient)
  - [DataSourceManager](#datasourcemanager)
- [数据模型](#数据模型)

---

## 概述

小游探系统基于 OpenAgents 框架构建，提供了一套完整的 Agent API 用于游戏圈信息追踪和分析。

### 基础使用

```python
from src.agents.router_agent import RouterAgent, QueryContext
from datetime import datetime

# 创建Router Agent
router = RouterAgent()

# 启动Agent
await router.on_startup()

# 处理查询
context = QueryContext(
    user_id="user123",
    session_id="session456",
    timestamp=datetime.now()
)

result = await router.smart_process("Faker在直播吗？", context)
print(result)

# 关闭Agent
await router.on_shutdown()
```

---

## 核心Agent

### RouterAgent

智能路由Agent，负责意图识别和任务分发。

#### 类定义

```python
class RouterAgent(WorkerAgent):
    """
    路由Agent - 系统的大脑
    
    功能：
    - 意图识别
    - 任务路由
    - Agent协调
    """
```

#### 初始化

```python
router = RouterAgent()
```

#### 主要方法

##### `smart_process(query: str, context: QueryContext) -> Dict[str, Any]`

智能处理用户查询。

**参数**:
- `query` (str): 用户查询文本
- `context` (QueryContext): 查询上下文

**返回**:
```python
{
    "success": bool,           # 是否成功
    "response": str,           # 响应文本
    "intent": str,             # 识别的意图
    "confidence": float,       # 置信度 (0-1)
    "agents_used": List[str],  # 使用的Agent列表
    "processing_time": float   # 处理时间（秒）
}
```

**示例**:
```python
result = await router.smart_process(
    "Faker在直播吗？",
    QueryContext(
        user_id="user123",
        session_id="session456",
        timestamp=datetime.now()
    )
)
```

##### `register_agent(name: str, agent: WorkerAgent) -> None`

注册子Agent。

**参数**:
- `name` (str): Agent名称
- `agent` (WorkerAgent): Agent实例

**示例**:
```python
live_monitor = LiveMonitorAgent()
router.register_agent("live_monitor", live_monitor)
```

##### `on_startup() -> None`

启动Agent。

**示例**:
```python
await router.on_startup()
```

##### `on_shutdown() -> None`

关闭Agent。

**示例**:
```python
await router.on_shutdown()
```

#### 支持的意图

| 意图 | 描述 | 示例查询 |
|------|------|----------|
| `问候` | 用户打招呼 | "你好", "hi" |
| `直播查询` | 查询主播直播状态 | "Faker在直播吗？" |
| `简报生成` | 生成游戏圈简报 | "生成今日简报" |
| `系统状态` | 查询系统状态 | "系统状态" |
| `未知` | 无法识别的查询 | 其他查询 |

---

### LiveMonitorAgent

直播监控Agent，负责追踪主播直播状态。

#### 类定义

```python
class LiveMonitorAgent(WorkerAgent):
    """
    直播监控Agent
    
    功能：
    - 监控主播直播状态
    - 查询直播信息
    - 搜索直播流
    """
```

#### 初始化

```python
live_monitor = LiveMonitorAgent()
```

#### 主要方法

##### `check_player_status(player_name: str) -> Dict[str, Any]`

检查指定主播的直播状态。

**参数**:
- `player_name` (str): 主播名称

**返回**:
```python
{
    "player": str,        # 主播名称
    "is_live": bool,      # 是否在直播
    "stream_info": {      # 直播信息（如果在直播）
        "title": str,     # 直播标题
        "game": str,      # 游戏名称
        "viewers": int,   # 观众数
        "url": str        # 直播间URL
    }
}
```

**示例**:
```python
status = await live_monitor.check_player_status("Faker")
if status["is_live"]:
    print(f"Faker正在直播: {status['stream_info']['title']}")
```

##### `search_streams(query: str, first: int = 10) -> List[Dict]`

搜索直播流。

**参数**:
- `query` (str): 搜索关键词
- `first` (int): 返回数量，默认10

**返回**:
```python
[
    {
        "title": str,      # 直播标题
        "game": str,       # 游戏名称
        "viewers": int,    # 观众数
        "streamer": str,   # 主播名称
        "url": str         # 直播间URL
    },
    ...
]
```

**示例**:
```python
streams = await live_monitor.search_streams("英雄联盟", first=5)
for stream in streams:
    print(f"{stream['streamer']}: {stream['title']}")
```

##### `monitor_all_players() -> None`

后台监控所有配置的主播。

**示例**:
```python
# 在on_startup中自动启动
await live_monitor.on_startup()
```

---

### BriefingAgent

简报生成Agent，负责汇总和生成游戏圈简报。

#### 类定义

```python
class BriefingAgent(WorkerAgent):
    """
    简报生成Agent
    
    功能：
    - 生成游戏圈简报
    - 多Agent协作
    - 数据聚合
    """
```

#### 初始化

```python
briefing_agent = BriefingAgent()
```

#### 主要方法

##### `generate_collaborative_briefing(time_range: str = "today") -> Dict[str, Any]`

生成协作式简报。

**参数**:
- `time_range` (str): 时间范围，可选值: "today", "week", "month"

**返回**:
```python
{
    "success": bool,           # 是否成功
    "briefing": str,           # 简报内容
    "sources": List[str],      # 数据来源
    "generated_at": datetime,  # 生成时间
    "stats": {                 # 统计信息
        "live_count": int,     # 直播数量
        "events_count": int    # 事件数量
    }
}
```

**示例**:
```python
briefing = await briefing_agent.generate_collaborative_briefing("today")
print(briefing["briefing"])
```

---

### DataSourceAgent

数据源Agent，负责管理和获取数据。

#### 类定义

```python
class DataSourceAgent(WorkerAgent):
    """
    数据源Agent
    
    功能：
    - 数据源管理
    - 数据获取
    - 故障切换
    """
```

#### 初始化

```python
data_source = DataSourceAgent()
```

#### 主要方法

##### `handle_query(query: Dict[str, Any]) -> Any`

处理数据查询。

**参数**:
- `query` (Dict): 查询参数
  - `type` (str): 查询类型
  - `parameters` (Dict): 查询参数

**返回**: 根据查询类型返回不同的数据

**支持的查询类型**:
- `get_live_streams`: 获取直播流
- `search_streams`: 搜索直播
- `get_player_info`: 获取主播信息

**示例**:
```python
result = await data_source.handle_query({
    "type": "get_live_streams",
    "parameters": {"first": 10}
})
```

---

## 工具类

### LLMClient

LLM客户端，负责与大语言模型交互。

#### 类定义

```python
class LLMClient:
    """
    LLM客户端
    
    支持的提供商：
    - Claude (Anthropic)
    - OpenAI
    - Fallback (降级模式)
    """
```

#### 初始化

```python
from src.utils.llm_client import LLMClient

client = LLMClient(
    provider="claude",
    model="claude-3-5-sonnet-20241022"
)
```

#### 主要方法

##### `chat(messages: List[Dict], **kwargs) -> str`

发送聊天请求。

**参数**:
- `messages` (List[Dict]): 消息列表
- `**kwargs`: 其他参数（temperature, max_tokens等）

**返回**: str - LLM响应文本

**示例**:
```python
response = await client.chat([
    {"role": "user", "content": "你好"}
])
print(response)
```

---

### DataSourceManager

数据源管理器，负责多数据源管理和故障切换。

#### 类定义

```python
class DataSourceManager:
    """
    数据源管理器
    
    功能：
    - 多数据源管理
    - 自动故障切换
    - 缓存管理
    """
```

#### 初始化

```python
from src.utils.data_sources import DataSourceManager

manager = DataSourceManager()
```

#### 主要方法

##### `add_source(source: DataSource) -> None`

添加数据源。

**参数**:
- `source` (DataSource): 数据源实例

**示例**:
```python
from src.utils.data_sources import MockDataSource

mock_source = MockDataSource()
manager.add_source(mock_source)
```

##### `fetch(query: DataQuery) -> DataResult`

获取数据（自动故障切换）。

**参数**:
- `query` (DataQuery): 数据查询

**返回**: DataResult - 查询结果

**示例**:
```python
from src.utils.data_sources import DataQuery

query = DataQuery(
    query_type="streams",
    parameters={"first": 10}
)

result = await manager.fetch(query)
if result.success:
    print(f"获取到 {len(result.data)} 条数据")
```

---

## 数据模型

### QueryContext

查询上下文。

```python
@dataclass
class QueryContext:
    user_id: str           # 用户ID
    session_id: str        # 会话ID
    timestamp: datetime    # 时间戳
```

### DataQuery

数据查询。

```python
@dataclass
class DataQuery:
    query_type: str              # 查询类型
    parameters: Dict[str, Any]   # 查询参数
    timeout: float = 30.0        # 超时时间
    cache_ttl: int = 300         # 缓存TTL
```

### DataResult

数据结果。

```python
@dataclass
class DataResult:
    success: bool                # 是否成功
    data: Any                    # 数据
    source: str                  # 数据来源
    cached: bool = False         # 是否来自缓存
    processing_time: float = 0.0 # 处理时间
    error: Optional[str] = None  # 错误信息
```

---

## 错误处理

### 异常类型

```python
class AgentError(Exception):
    """Agent基础异常"""
    pass

class DataSourceError(Exception):
    """数据源异常"""
    pass

class LLMError(Exception):
    """LLM异常"""
    pass
```

### 错误处理示例

```python
try:
    result = await router.smart_process(query, context)
except AgentError as e:
    print(f"Agent错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 配置

### 环境变量

```bash
# LLM配置
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# 数据源配置
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret

# 系统配置
LOG_LEVEL=INFO
CACHE_TTL=300
```

### 配置文件

#### config/players.yaml

```yaml
monitored_players:
  - name: "Faker"
    platform: "twitch"
    channel: "faker"
  - name: "Uzi"
    platform: "huya"
    room_id: "123456"
```

---

## 最佳实践

### 1. Agent生命周期管理

```python
# 正确的方式
async def main():
    router = RouterAgent()
    
    try:
        await router.on_startup()
        # 使用router
        result = await router.smart_process(query, context)
    finally:
        await router.on_shutdown()

# 使用asyncio.run
asyncio.run(main())
```

### 2. 错误处理

```python
result = await router.smart_process(query, context)

if not result["success"]:
    print(f"处理失败: {result.get('error', '未知错误')}")
else:
    print(f"响应: {result['response']}")
```

### 3. 性能优化

```python
# 使用缓存
query = DataQuery(
    query_type="streams",
    parameters={"first": 10},
    cache_ttl=600  # 缓存10分钟
)

# 并发查询
results = await asyncio.gather(
    router.smart_process(query1, context1),
    router.smart_process(query2, context2)
)
```

---

## 更新日志

### v1.0 (2026-01-14)
- ✅ 初始版本
- ✅ RouterAgent API
- ✅ LiveMonitorAgent API
- ✅ BriefingAgent API
- ✅ DataSourceAgent API
- ✅ 工具类API

---

## 相关文档

- [开发者指南](DEVELOPER_GUIDE.md)
- [用户手册](USER_GUIDE.md)
- [架构文档](ARCHITECTURE.md)
- [部署文档](DEPLOYMENT.md)

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-14
