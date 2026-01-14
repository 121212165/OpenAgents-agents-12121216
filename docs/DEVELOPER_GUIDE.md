# 开发者指南

**版本**: MVP v1.0  
**更新日期**: 2026-01-14

## 目录

- [开发环境搭建](#开发环境搭建)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [开发流程](#开发流程)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [贡献指南](#贡献指南)

---

## 开发环境搭建

### 系统要求

- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.10 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 2GB 可用空间

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/yougame-explorer.git
cd yougame-explorer
```

#### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者安装最小依赖（用于生产环境）
pip install -r requirements.minimal.txt
```

#### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
# Windows: notepad .env
# macOS/Linux: nano .env
```

必需的环境变量：

```bash
# LLM配置（至少配置一个）
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# 可选：Twitch API
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

# 系统配置
LOG_LEVEL=INFO
CACHE_TTL=300
```

#### 5. 验证安装

```bash
# 运行快速验证
python quick_verify.py

# 应该看到：
# ✅ Agent创建成功
# ✅ 所有测试通过
# 🎉 系统运行良好！
```

### IDE 配置

#### VS Code（推荐）

1. 安装推荐扩展：
   - Python
   - Pylance
   - Python Test Explorer

2. 配置 `.vscode/settings.json`:

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true
}
```

#### PyCharm

1. 配置 Python 解释器：
   - File → Settings → Project → Python Interpreter
   - 选择虚拟环境中的 Python

2. 配置测试框架：
   - File → Settings → Tools → Python Integrated Tools
   - Default test runner: pytest

---

## 项目结构

```
yougame-explorer/
├── .kiro/                    # Kiro配置
│   ├── specs/               # 规格文档
│   └── steering/            # 指导文档
├── config/                   # 配置文件
│   └── players.yaml         # 主播配置
├── docs/                     # 文档
│   ├── API_REFERENCE.md     # API参考
│   ├── DEVELOPER_GUIDE.md   # 开发者指南（本文档）
│   ├── USER_GUIDE.md        # 用户手册
│   └── ARCHITECTURE.md      # 架构文档
├── src/                      # 源代码
│   ├── agents/              # Agent实现
│   │   ├── router_agent.py
│   │   ├── live_monitor_agent.py
│   │   ├── briefing_agent.py
│   │   └── data_source_agent.py
│   ├── utils/               # 工具类
│   │   ├── llm_client.py
│   │   ├── data_sources.py
│   │   ├── common.py
│   │   └── error_handler.py
│   ├── main.py              # 主入口
│   └── web_ui.py            # Web界面
├── tests/                    # 测试
│   ├── test_e2e_scenarios.py
│   ├── test_routing_simplified.py
│   └── test_multi_agent_collaboration.py
├── .env.example             # 环境变量模板
├── pytest.ini               # Pytest配置
├── requirements.txt         # 依赖列表
├── quick_verify.py          # 快速验证脚本
└── README.md                # 项目说明
```

### 核心模块说明

#### src/agents/

包含所有Agent实现：

- `router_agent.py`: 路由Agent，负责意图识别和任务分发
- `live_monitor_agent.py`: 直播监控Agent
- `briefing_agent.py`: 简报生成Agent
- `data_source_agent.py`: 数据源Agent

#### src/utils/

工具类和辅助函数：

- `llm_client.py`: LLM客户端封装
- `data_sources.py`: 数据源管理
- `common.py`: 通用工具函数
- `error_handler.py`: 错误处理和恢复

#### tests/

测试文件：

- `test_e2e_scenarios.py`: 端到端场景测试
- `test_routing_simplified.py`: 路由功能测试
- `test_multi_agent_collaboration.py`: 多Agent协作测试

---

## 代码规范

### Python 代码风格

遵循 **PEP 8** 规范，使用 **Black** 进行代码格式化。

#### 命名规范

```python
# 类名：大驼峰
class RouterAgent:
    pass

# 函数名：小写+下划线
def process_query():
    pass

# 常量：大写+下划线
MAX_RETRIES = 3

# 私有方法：前缀下划线
def _internal_method():
    pass
```

#### 类型注解

```python
from typing import Dict, List, Optional

def process_query(
    query: str,
    context: QueryContext
) -> Dict[str, Any]:
    """
    处理查询
    
    Args:
        query: 查询文本
        context: 查询上下文
        
    Returns:
        处理结果字典
    """
    pass
```

#### 文档字符串

使用 Google 风格的文档字符串：

```python
def example_function(param1: str, param2: int) -> bool:
    """
    函数简短描述。
    
    详细描述（可选）。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        
    Returns:
        返回值的描述
        
    Raises:
        ValueError: 当参数无效时
        
    Example:
        >>> example_function("test", 42)
        True
    """
    pass
```

### 代码组织

#### 导入顺序

```python
# 1. 标准库
import os
import sys
from datetime import datetime

# 2. 第三方库
import asyncio
from loguru import logger

# 3. 本地模块
from src.agents.router_agent import RouterAgent
from src.utils.common import load_env
```

#### 类结构

```python
class ExampleAgent(WorkerAgent):
    """类文档字符串"""
    
    # 1. 类变量
    DEFAULT_TIMEOUT = 30
    
    def __init__(self):
        """初始化方法"""
        # 2. 实例变量
        self.state = "initialized"
        
    # 3. 公共方法
    async def process(self, query: str) -> Dict:
        """公共方法"""
        pass
    
    # 4. 私有方法
    def _internal_logic(self) -> None:
        """私有方法"""
        pass
    
    # 5. 生命周期方法
    async def on_startup(self) -> None:
        """启动方法"""
        pass
    
    async def on_shutdown(self) -> None:
        """关闭方法"""
        pass
```

### 错误处理

```python
# 使用具体的异常类型
try:
    result = await agent.process(query)
except ValueError as e:
    logger.error(f"参数错误: {e}")
    raise
except Exception as e:
    logger.error(f"未知错误: {e}")
    # 降级处理
    return fallback_response()
finally:
    # 清理资源
    await cleanup()
```

### 日志规范

```python
from loguru import logger

# 使用合适的日志级别
logger.debug("调试信息")      # 详细的调试信息
logger.info("正常信息")       # 正常的操作信息
logger.warning("警告信息")    # 警告但不影响运行
logger.error("错误信息")      # 错误但可以恢复
logger.critical("严重错误")   # 严重错误，可能导致崩溃

# 包含上下文信息
logger.info(f"处理查询: {query}, 用户: {user_id}")

# 记录异常
try:
    risky_operation()
except Exception as e:
    logger.exception("操作失败")  # 自动记录堆栈跟踪
```

---

## 开发流程

### 1. 创建新功能

#### 步骤

1. **创建分支**
```bash
git checkout -b feature/your-feature-name
```

2. **编写代码**
   - 遵循代码规范
   - 添加类型注解
   - 编写文档字符串

3. **编写测试**
```python
# tests/test_your_feature.py
import pytest

@pytest.mark.asyncio
async def test_your_feature():
    # 测试代码
    assert result == expected
```

4. **运行测试**
```bash
pytest tests/test_your_feature.py -v
```

5. **提交代码**
```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 2. 修复Bug

#### 步骤

1. **创建分支**
```bash
git checkout -b fix/bug-description
```

2. **重现Bug**
   - 编写失败的测试用例
   - 确认Bug存在

3. **修复Bug**
   - 修改代码
   - 确保测试通过

4. **提交代码**
```bash
git commit -m "fix: fix bug description"
```

### 3. 代码审查

#### 审查清单

- [ ] 代码符合规范
- [ ] 有适当的测试覆盖
- [ ] 文档已更新
- [ ] 没有引入新的警告
- [ ] 性能没有明显下降

---

## 测试指南

### 测试类型

#### 1. 单元测试

测试单个函数或方法：

```python
def test_intent_detection():
    """测试意图识别"""
    router = RouterAgent()
    intent = router._detect_intent("Faker在直播吗")
    assert intent == "直播查询"
```

#### 2. 集成测试

测试多个组件协作：

```python
@pytest.mark.asyncio
async def test_agent_collaboration():
    """测试Agent协作"""
    router = RouterAgent()
    live_monitor = LiveMonitorAgent()
    router.register_agent("live_monitor", live_monitor)
    
    result = await router.process("Faker在直播吗")
    assert result["success"] is True
```

#### 3. 端到端测试

测试完整的用户场景：

```python
@pytest.mark.asyncio
async def test_complete_workflow():
    """测试完整工作流"""
    # 创建系统
    system = await setup_system()
    
    # 执行查询
    result = await system["router"].smart_process(
        "生成今日简报",
        context
    )
    
    # 验证结果
    assert result["success"] is True
    assert len(result["response"]) > 50
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_e2e_scenarios.py

# 运行特定测试
pytest tests/test_e2e_scenarios.py::test_greeting_scenario

# 显示详细输出
pytest -v -s

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试最佳实践

1. **使用Fixture**
```python
@pytest.fixture
async def router_system():
    """创建测试系统"""
    router = RouterAgent()
    await router.on_startup()
    yield router
    await router.on_shutdown()
```

2. **参数化测试**
```python
@pytest.mark.parametrize("query,expected_intent", [
    ("你好", "问候"),
    ("Faker在直播吗", "直播查询"),
    ("生成简报", "简报生成"),
])
def test_intent_detection(query, expected_intent):
    intent = detect_intent(query)
    assert intent == expected_intent
```

3. **Mock外部依赖**
```python
from unittest.mock import AsyncMock, patch

@patch('src.utils.llm_client.LLMClient.chat')
async def test_with_mock(mock_chat):
    mock_chat.return_value = "模拟响应"
    result = await agent.process(query)
    assert "模拟响应" in result
```

---

## 调试技巧

### 1. 使用日志

```python
# 临时增加日志级别
logger.add("debug.log", level="DEBUG")

# 在关键位置添加日志
logger.debug(f"变量值: {variable}")
logger.debug(f"函数调用: {function_name}({args})")
```

### 2. 使用断点

```python
# 在代码中设置断点
import pdb; pdb.set_trace()

# 或使用breakpoint()（Python 3.7+）
breakpoint()
```

### 3. 使用IPython

```python
# 在代码中启动IPython shell
from IPython import embed
embed()
```

### 4. 异步调试

```python
# 打印异步任务状态
import asyncio

tasks = asyncio.all_tasks()
for task in tasks:
    print(f"Task: {task.get_name()}, Done: {task.done()}")
```

### 5. 性能分析

```python
import time

start = time.time()
result = await expensive_operation()
elapsed = time.time() - start
logger.info(f"操作耗时: {elapsed:.2f}s")
```

---

## 贡献指南

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type类型

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

#### 示例

```bash
feat(router): add intent confidence threshold

- Add confidence threshold configuration
- Improve intent detection accuracy
- Update tests

Closes #123
```

### Pull Request流程

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request
5. 等待代码审查
6. 合并到主分支

### 代码审查标准

- 代码质量
- 测试覆盖
- 文档完整性
- 性能影响
- 安全性

---

## 常见问题

### Q: 如何添加新的Agent？

A: 参考现有Agent实现，继承`WorkerAgent`基类：

```python
from openagents import WorkerAgent

class MyAgent(WorkerAgent):
    def __init__(self):
        super().__init__()
        # 初始化代码
    
    async def process(self, message):
        # 处理逻辑
        pass
```

### Q: 如何添加新的数据源？

A: 实现`DataSource`接口：

```python
from src.utils.data_sources import DataSource

class MyDataSource(DataSource):
    async def fetch(self, query):
        # 获取数据
        pass
    
    async def health_check(self):
        # 健康检查
        pass
```

### Q: 如何调试异步代码？

A: 使用`asyncio`的调试模式：

```python
import asyncio
asyncio.run(main(), debug=True)
```

---

## 相关资源

- [API参考文档](API_REFERENCE.md)
- [用户手册](USER_GUIDE.md)
- [架构文档](ARCHITECTURE.md)
- [OpenAgents文档](https://docs.openagents.com)
- [Python异步编程](https://docs.python.org/3/library/asyncio.html)

---

**文档维护**: Kiro AI Assistant  
**最后更新**: 2026-01-14
