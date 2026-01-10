# 开发指南

## 项目结构

```
yougame-explorer/
├── config/                 # 配置文件
│   ├── network.yaml       # 网络配置
│   └── players.yaml       # 主播列表
├── docs/                  # 文档
│   ├── DEPLOYMENT.md      # 部署指南
│   └── DEVELOPMENT.md     # 开发指南（本文件）
├── src/                   # 源代码
│   ├── agents/           # Agent 实现
│   │   ├── router_agent.py
│   │   ├── live_monitor_agent.py
│   │   └── briefing_agent.py
│   ├── utils/            # 工具函数
│   │   ├── common.py
│   │   └── huya_api.py
│   └── main.py           # 入口文件
├── tests/                # 测试
├── logs/                 # 日志
├── .env.example          # 环境变量模板
├── .gitignore
├── requirements.txt      # 依赖列表
├── QUICKSTART.md         # 快速开始
└── README.md             # 项目介绍
```

## 核心概念

### Agent 架构

小游探采用**多 Agent 协作架构**：

```
用户请求
    ↓
Router Agent（路由中枢）
    ↓
├─→ LiveMonitor Agent（直播监控）
├─→ BriefingAgent（简报生成）
└─→ （未来：更多 Agent）
```

### 设计模式

1. **Router Pattern**：Router Agent 作为中央调度器
2. **Event-Driven**：Agent 之间通过事件通信
3. **Dependency Injection**：Agent 依赖通过构造函数注入

## 开发环境设置

### 安装开发依赖

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8  # 开发工具
```

### 代码风格

使用 Black 格式化代码：

```bash
black src/
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_router_agent.py

# 显示详细输出
pytest -v tests/
```

## 添加新功能

### 1. 添加新的 Agent

创建新文件 `src/agents/new_agent.py`：

```python
from loguru import logger

class NewAgent:
    def __init__(self):
        self.name = "New Agent"
        logger.info(f"{self.name} 初始化")

    async def process(self, input_data):
        # 处理逻辑
        result = "处理结果"
        return result
```

在 `src/main.py` 中注册：

```python
from src.agents.new_agent import NewAgent

# 在 initialize() 中
self.new_agent = NewAgent()
self.router.new_agent = self.new_agent
```

### 2. 添加新的数据源

创建 `src/utils/new_api.py`：

```python
import aiohttp

class NewAPIClient:
    async def fetch_data(self):
        async with aiohttp.ClientSession() as session:
            # 实现数据获取
            pass
```

### 3. 添加新的配置

在 `config/network.yaml` 中添加：

```yaml
custom_config:
  setting1: "value1"
  setting2: "value2"
```

在代码中读取：

```python
from src.utils.common import load_yaml_config

config = load_yaml_config("config/network.yaml")
custom = config.get("custom_config")
```

## 调试技巧

### 启用调试日志

```python
# .env 文件
LOG_LEVEL=DEBUG
```

### 单元测试

```bash
# 测试单个 Agent
python -m pytest tests/test_router_agent.py -v

# 测试 API 客户端
python src/utils/huya_api.py
```

### 交互式调试

```python
# 使用 Python 调试器
import pdb; pdb.set_trace()

# 或使用 IPython
from IPython import embed; embed()
```

## 性能优化

### 异步并发

```python
# 并发查询多个主播
tasks = [
    self.check_player_status(player)
    for player in players
]
results = await asyncio.gather(*tasks)
```

### 缓存策略

```python
# 使用缓存避免频繁请求
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_function(key):
    # ...
```

### 限流控制

```python
# 控制请求频率
import asyncio

async def rate_limited_request(url):
    await asyncio.sleep(1)  # 延迟1秒
    # 发起请求
```

## 测试指南

### 单元测试示例

```python
# tests/test_router_agent.py
import pytest
from src.agents.router_agent import RouterAgent

@pytest.mark.asyncio
async def test_greeting():
    router = RouterAgent()
    result = await router.process("你好")
    assert result["success"] == True
    assert "小游探" in result["response"]
```

### 集成测试

```python
# tests/test_integration.py
import pytest
from src.main import YouGameExplorer

@pytest.mark.asyncio
async def test_full_workflow():
    app = YouGameExplorer()
    await app.initialize()

    result = await app.router.process("生成简报")
    assert result["success"] == True
```

## 贡献指南

### 提交代码

1. Fork 项目
2. 创建分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m "Add new feature"`
4. 推送分支：`git push origin feature/new-feature`
5. 创建 Pull Request

### 代码审查清单

- [ ] 代码符合 PEP 8 规范
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 通过了所有测试
- [ ] 添加了新的测试用例

## 常见问题

### Q: 如何调试虎牙 API？

```python
# 运行测试脚本
python src/utils/huya_api.py

# 查看详细日志
LOG_LEVEL=DEBUG python src/main.py
```

### Q: 如何添加新的直播平台？

1. 创建 `src/utils/platform_api.py`
2. 实现相似的接口
3. 在 `LiveMonitorAgent` 中集成

### Q: 如何优化性能？

- 使用缓存减少重复请求
- 并发处理多个任务
- 优化数据库查询
- 使用更快的算法

## 资源链接

- [OpenAgents 文档](https://openagents.org/docs)
- [Python 异步编程](https://docs.python.org/3/library/asyncio.html)
- [aiohttp 文档](https://docs.aiohttp.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)

---

**Happy Coding!** 🚀
