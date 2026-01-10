# 🚀 快速开始指南

## 第一步：安装依赖

```bash
# 进入项目目录
cd yougame-explorer

# 安装 Python 依赖
pip install -r requirements.txt
```

## 第二步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件（可选，暂时不需要配置 API Key）
```

## 第三步：运行程序

```bash
# 启动小游探
python src/main.py
```

## 测试查询

启动后，你可以尝试以下查询：

```
你: 你好
小游探: 你好！我是小游探，你的游戏圈 AI 助手 🎮

你可以帮我：
- 查询主播直播状态（如：Uzi 直播了吗？）
- 生成游戏圈简报（如：生成今日简报）
- 分析游戏圈动态

请问有什么可以帮助你的？

你: Uzi 直播了吗
小游探: 📺 Uzi 当前未在直播

你: 生成今日简报
小游探: 📰 【小游探日报】2025年1月10日
==================================================
🔥 当前直播中 (0 人)
暂无主播直播
...
```

## 常见问题

### Q1: 提示找不到模块

```bash
# 确保在项目根目录
cd yougame-explorer

# 确认 Python 版本
python --version  # 应该是 3.10+
```

### Q2: 虎牙房间号不对

编辑 `config/players.yaml`，更新正确的房间号：

```yaml
monitored_players:
  - name: "Uzi"
    huya_id: "正确的房间号"  # 替换这里
```

### Q3: 如何添加更多主播？

在 `config/players.yaml` 中添加：

```yaml
  - name: "主播名"
    huya_id: "房间号"
    team: "战队"
    role: "位置"
    game: "游戏"
    priority: "medium"
```

## 下一步

- 阅读 [README.md](README.md) 了解完整功能
- 查看 [src/](src/) 目录学习代码结构
- 参考 [config/](config/) 自定义配置

---

**有问题？** 查看 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
