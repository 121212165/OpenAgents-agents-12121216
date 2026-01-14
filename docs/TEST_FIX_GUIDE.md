# 测试修复指南

**目标**: 修复所有失败的测试，提升测试覆盖率到70%+  
**优先级**: 🔴 高  
**预计时间**: 1-2天

---

## 🐛 当前测试问题

### 问题1: Hypothesis Fixture配置错误
**文件**: `tests/test_agent_routing_properties.py`  
**错误**: `fixture 'query_text' not found`  
**影响**: 5个属性测试失败

**原因分析**:
```python
# ❌ 错误写法 - hypothesis参数未正确注入
@given(st.text(min_size=1, max_size=100))
async def test_xxx(self, query_text, setup_router_system):
    pass
```

**解决方案**:
```python
# ✅ 正确写法 - 使用命名参数
@given(query_text=st.text(min_size=1, max_size=100))
async def test_xxx(self, query_text, setup_router_system):
    pass

# 或者使用pytest-asyncio的方式
@pytest.mark.asyncio
@given(st.text(min_size=1, max_size=100))
async def test_xxx(query_text):
    # 在测试内部创建setup
    system = await setup_system()
    ...
```

### 问题2: 异步测试配置
**文件**: `tests/test_integration.py`  
**错误**: `async def functions are not natively supported`  
**影响**: 2个集成测试失败

**解决方案1 - 添加pytest.ini**:
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
```

**解决方案2 - 使用装饰器**:
```python
import pytest

@pytest.mark.asyncio
async def test_full_system_integration():
    # 测试代码
    pass
```

### 问题3: Pydantic警告
**文件**: `src/utils/common.py`  
**警告**: `PydanticDeprecatedSince20: Support for class-based config is deprecated`  
**影响**: 6个警告信息

**解决方案**:
```python
# ❌ 旧写法
class LiveStatus(BaseModel):
    class Config:
        json_encoders = {...}

# ✅ 新写法
from pydantic import ConfigDict

class LiveStatus(BaseModel):
    model_config = ConfigDict(
        json_encoders={...}
    )
```

---

## 🔧 修复步骤

### Step 1: 创建pytest.ini配置
```bash
# 在项目根目录创建pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
# 异步测试配置
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function

# 测试发现
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 输出配置
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings

# 标记
markers =
    asyncio: mark test as async
    slow: mark test as slow
    integration: mark test as integration test
    property: mark test as property-based test
EOF
```

### Step 2: 修复test_agent_routing_properties.py
```python
# tests/test_agent_routing_properties.py

import pytest
from hypothesis import given, settings, strategies as st
from loguru import logger

class TestAgentRoutingProperties:
    """Agent路由属性测试"""
    
    @pytest.fixture
    async def setup_router_system(self):
        """设置测试系统"""
        from src.agents.router_agent import RouterAgent
        from src.agents.data_source_agent import DataSourceAgent
        from src.agents.briefing_agent import BriefingAgent
        from src.agents.live_monitor_agent import LiveMonitorAgent
        
        # 创建所有Agent
        data_source = DataSourceAgent()
        live_monitor = LiveMonitorAgent()
        briefing = BriefingAgent()
        router = RouterAgent()
        
        # 注册Agent
        router.register_agent("data_source", data_source)
        router.register_agent("live_monitor", live_monitor)
        router.register_agent("briefing_agent", briefing)
        
        # 启动Agent
        await data_source.on_startup()
        await live_monitor.on_startup()
        await briefing.on_startup()
        await router.on_startup()
        
        yield {
            "router": router,
            "data_source": data_source,
            "live_monitor": live_monitor,
            "briefing": briefing
        }
        
        # 清理
        await router.on_shutdown()
        await briefing.on_shutdown()
        await live_monitor.on_shutdown()
        await data_source.on_shutdown()
    
    @pytest.mark.asyncio
    @given(query_text=st.text(min_size=1, max_size=100))
    @settings(max_examples=50, deadline=5000)
    async def test_property_intent_classification_consistency(
        self, query_text, setup_router_system
    ):
        """
        Property 3.1: 意图分类一致性
        相同的查询应该产生一致的意图分类结果
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            # 多次执行相同查询
            results = []
            for _ in range(3):
                result = await router._smart_intent_detection(query_text)
                results.append(result)
            
            # 验证一致性
            if len(results) > 1:
                first_intent = results[0].get("intent")
                for result in results[1:]:
                    assert result.get("intent") == first_intent, \
                        f"意图分类不一致: {query_text} -> {[r.get('intent') for r in results]}"
            
            logger.info(f"✅ 意图分类一致性测试通过: {query_text} -> {results[0].get('intent')}")
        
        except Exception as e:
            logger.error(f"❌ 意图分类一致性测试失败: {query_text} -> {e}")
            # 对于无效输入，允许失败
            if len(query_text.strip()) == 0:
                pytest.skip("空查询跳过")
            raise
    
    @pytest.mark.asyncio
    @given(live_query=st.sampled_from([
        "Faker在直播吗",
        "Uzi开播了吗",
        "查看TheShy的直播状态",
        "大司马在线吗",
        "直播中的主播有哪些"
    ]))
    @settings(max_examples=20, deadline=10000)
    async def test_property_live_query_routing(
        self, live_query, setup_router_system
    ):
        """
        Property 3.2: 直播查询路由正确性
        直播相关查询应该正确路由到LiveMonitor Agent
        """
        system = await setup_router_system
        router = system["router"]
        
        try:
            result = await router.process(live_query)
            
            # 验证路由正确性
            assert result["success"] is not None, "结果应该有success字段"
            assert "agent_used" in result, "结果应该包含使用的agent信息"
            
            # 对于直播查询，应该使用live_monitor或router
            used_agent = result["agent_used"]
            assert used_agent in ["live_monitor", "router"], \
                f"直播查询应该路由到live_monitor或router，实际: {used_agent}"
            
            # 响应应该包含直播相关信息
            response = result["response"]
            assert isinstance(response, str), "响应应该是字符串"
            assert len(response) > 0, "响应不应该为空"
            
            logger.info(f"✅ 直播查询路由测试通过: {live_query} -> {used_agent}")
        
        except Exception as e:
            logger.error(f"❌ 直播查询路由测试失败: {live_query} -> {e}")
            raise
```

### Step 3: 修复test_integration.py
```python
# tests/test_integration.py

import pytest
import asyncio
from loguru import logger

@pytest.mark.asyncio
async def test_full_system_integration():
    """完整系统集成测试"""
    from src.main import YouGameExplorer
    
    app = YouGameExplorer()
    
    try:
        # 初始化系统
        await app.initialize()
        logger.info("✅ 系统初始化成功")
        
        # 测试基础查询
        test_queries = [
            "你好",
            "Faker在直播吗",
            "生成今日简报"
        ]
        
        for query in test_queries:
            result = await app.router.process(query)
            assert result["success"] is not None
            assert "response" in result
            assert len(result["response"]) > 0
            logger.info(f"✅ 查询测试通过: {query}")
        
        logger.info("✅ 完整系统集成测试通过")
    
    finally:
        # 清理资源
        await app.shutdown()

@pytest.mark.asyncio
async def test_error_recovery():
    """错误恢复测试"""
    from src.main import YouGameExplorer
    
    app = YouGameExplorer()
    
    try:
        await app.initialize()
        
        # 测试无效查询
        invalid_queries = ["", "   ", "\n\n"]
        
        for query in invalid_queries:
            result = await app.router.process(query)
            # 应该有响应，即使是错误响应
            assert "response" in result
            logger.info(f"✅ 错误处理测试通过: '{query}'")
        
        logger.info("✅ 错误恢复测试通过")
    
    finally:
        await app.shutdown()
```

### Step 4: 修复Pydantic警告
```python
# src/utils/common.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class LiveStatus(BaseModel):
    """直播状态数据模型"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    player_name: str
    is_live: bool
    platform: str
    title: Optional[str] = None
    viewer_count: Optional[int] = 0
    game_name: Optional[str] = None
    live_url: Optional[str] = None
    start_time: Optional[datetime] = None

class EventMessage(BaseModel):
    """事件消息数据模型"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str

class BriefingItem(BaseModel):
    """简报项数据模型"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    title: str
    content: str
    timestamp: datetime
    category: str
    priority: int = 1
```

---

## ✅ 验证步骤

### 1. 运行所有测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_agent_routing_properties.py -v
pytest tests/test_integration.py -v

# 运行并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 2. 检查测试覆盖率
```bash
# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=term-missing

# 查看HTML报告
# 打开 htmlcov/index.html
```

### 3. 验证所有测试通过
```bash
# 期望输出
# ============== test session starts ==============
# collected 39 items
# 
# tests/test_agent_routing_properties.py::... PASSED
# tests/test_data_source_properties.py::... PASSED
# tests/test_integration.py::... PASSED
# tests/test_multi_agent_collaboration.py::... PASSED
# 
# ============== 39 passed in 45.23s ==============
```

---

## 📊 测试覆盖率目标

| 模块 | 当前覆盖率 | 目标覆盖率 | 优先级 |
|-----|-----------|-----------|--------|
| router_agent.py | ~50% | 80% | 🔴 高 |
| data_source_agent.py | ~60% | 80% | 🔴 高 |
| briefing_agent.py | ~40% | 70% | 🟡 中 |
| live_monitor_agent.py | ~50% | 70% | 🟡 中 |
| utils/*.py | ~70% | 80% | 🟢 低 |

---

## 🎯 下一步测试增强

### 1. 添加更多单元测试
```python
# tests/test_router_unit.py

@pytest.mark.asyncio
async def test_intent_detection_accuracy():
    """测试意图识别准确性"""
    router = RouterAgent()
    
    test_cases = [
        ("Faker在直播吗", "直播查询"),
        ("生成今日简报", "简报生成"),
        ("你好", "问候"),
        ("系统状态", "系统状态"),
    ]
    
    for query, expected_intent in test_cases:
        result = await router._smart_intent_detection(query)
        assert result["intent"] == expected_intent
```

### 2. 添加性能测试
```python
# tests/test_performance.py

@pytest.mark.asyncio
async def test_response_time():
    """测试响应时间"""
    import time
    
    app = YouGameExplorer()
    await app.initialize()
    
    try:
        start = time.time()
        result = await app.router.process("Faker在直播吗")
        duration = time.time() - start
        
        assert duration < 3.0, f"响应时间超过3秒: {duration}s"
        logger.info(f"✅ 响应时间测试通过: {duration:.2f}s")
    
    finally:
        await app.shutdown()
```

### 3. 添加并发测试
```python
# tests/test_concurrency.py

@pytest.mark.asyncio
async def test_concurrent_queries():
    """测试并发查询处理"""
    app = YouGameExplorer()
    await app.initialize()
    
    try:
        # 并发执行10个查询
        queries = ["Faker在直播吗"] * 10
        tasks = [app.router.process(q) for q in queries]
        results = await asyncio.gather(*tasks)
        
        # 验证所有查询都成功
        for result in results:
            assert result["success"] is not None
        
        logger.info("✅ 并发测试通过")
    
    finally:
        await app.shutdown()
```

---

## 📝 测试最佳实践

### 1. 测试命名规范
```python
# ✅ 好的命名
def test_router_handles_live_query_correctly():
    pass

def test_data_source_failover_when_api_fails():
    pass

# ❌ 不好的命名
def test_1():
    pass

def test_router():
    pass
```

### 2. 测试组织
```
tests/
├── unit/                    # 单元测试
│   ├── test_router.py
│   ├── test_data_source.py
│   └── test_briefing.py
├── integration/             # 集成测试
│   ├── test_full_system.py
│   └── test_multi_agent.py
├── properties/              # 属性测试
│   ├── test_routing_properties.py
│   └── test_data_properties.py
└── performance/             # 性能测试
    ├── test_response_time.py
    └── test_concurrency.py
```

### 3. 测试数据管理
```python
# tests/conftest.py

import pytest

@pytest.fixture
def sample_live_data():
    """示例直播数据"""
    return [
        {
            "user_name": "Faker",
            "game_name": "League of Legends",
            "viewer_count": 45000,
            "title": "Ranked Solo Queue"
        },
        {
            "user_name": "Doublelift",
            "game_name": "League of Legends",
            "viewer_count": 12000,
            "title": "Climbing to Challenger"
        }
    ]

@pytest.fixture
async def mock_router():
    """Mock Router Agent"""
    from src.agents.router_agent import RouterAgent
    router = RouterAgent()
    await router.on_startup()
    yield router
    await router.on_shutdown()
```

---

## 🚀 快速修复命令

```bash
# 1. 创建pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
addopts = -v --tb=short
EOF

# 2. 运行测试
pytest tests/ -v

# 3. 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 4. 查看报告
# Windows: start htmlcov/index.html
# Linux/Mac: open htmlcov/index.html
```

---

**文档创建**: 2026-01-14  
**预计修复时间**: 1-2天  
**目标**: 所有测试通过，覆盖率70%+
