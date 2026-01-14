# 小游探 Web UI 使用指南

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动Web界面

```bash
python src/web_ui.py
```

界面将在 http://localhost:7860 启动

## 功能特性

### 🎯 核心功能

1. **智能对话**: 自然语言交互，理解你的意图
2. **直播查询**: 查询主播是否在直播
3. **简报生成**: 获取游戏圈最新动态
4. **系统监控**: 实时查看系统状态

### 🤖 Agent协作可视化

右侧日志窗口实时显示：
- 意图识别结果
- 使用的Agent
- 处理时间
- 协作过程

### 💡 快捷查询

界面提供常用查询按钮：
- "你好" - 测试基本对话
- "Faker在直播吗？" - 查询直播状态
- "生成今日简报" - 获取游戏动态
- "系统状态" - 查看系统健康
- "最近有什么热门游戏？" - 热门查询

## 使用示例

### 查询主播直播状态

```
用户: Faker在直播吗？
小游探: 🔴 Faker 正在 Twitch 直播！
       📝 标题：Ranked Solo Queue
       🎮 游戏：League of Legends
       👥 观众：45,000
```

### 生成游戏简报

```
用户: 生成今日简报
小游探: 📰 【小游探简报 - 2026-01-14】

       🔥 热门直播
       1. Faker - League of Legends (45,000观众)
       2. Doublelift - League of Legends (12,000观众)
       
       📊 今日统计
       - 在线主播: 3位
       - 总观众数: 120,000
```

## 快速验证

运行快速验证脚本确保系统正常：

```bash
python quick_verify.py
```

这将测试：
- Agent创建和初始化
- 基本对话功能
- 直播查询功能
- 简报生成功能
- 系统状态查询
- 错误处理

## 端到端测试

运行完整的端到端测试：

```bash
pytest tests/test_e2e_scenarios.py -v
```

测试覆盖：
- 真实用户场景
- 响应时间要求
- 并发查询处理
- 数据源可靠性
- Agent协作

## 配置

### 环境变量

在 `.env` 文件中配置：

```env
# LLM配置
LLM_PROVIDER=openai  # 或 anthropic
OPENAI_API_KEY=your_key_here

# Twitch API（可选）
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_secret

# Web UI配置
WEB_UI_PORT=7860
WEB_UI_SHARE=false
```

### 数据源

系统支持多数据源自动切换：
1. Twitch API（主要数据源）
2. Mock数据（备用数据源）
3. 缓存数据（离线模式）

## 故障排查

### 问题1: 界面无法启动

```bash
# 检查端口是否被占用
netstat -ano | findstr :7860

# 更换端口
python src/web_ui.py --port 8080
```

### 问题2: Agent初始化失败

```bash
# 运行快速验证
python quick_verify.py

# 查看日志
cat logs/yougame.log
```

### 问题3: 响应时间过长

- 检查网络连接
- 确认LLM API可用
- 查看Agent日志了解瓶颈

## 性能优化

### 响应时间

- 目标: < 3秒
- 使用缓存减少API调用
- 并发处理多Agent任务

### 资源使用

- 内存: < 500MB
- CPU: 正常负载 < 20%
- 网络: 按需请求

## 下一步

1. **添加更多功能**: 扩展查询类型
2. **优化UI**: 改进界面设计
3. **增强Agent**: 添加更多智能功能
4. **部署上线**: 云端部署指南

## 反馈

遇到问题或有建议？
- 查看日志: `logs/yougame.log`
- 运行测试: `pytest tests/test_e2e_scenarios.py`
- 快速验证: `python quick_verify.py`
