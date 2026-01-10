# 部署指南

## 本地开发部署

### 环境要求

- Python 3.10 或更高版本
- pip（Python 包管理器）
- Git（可选，用于克隆项目）

### 安装步骤

#### 1. 获取项目代码

```bash
# 如果使用 Git
git clone https://github.com/your-username/yougame-explorer.git
cd yougame-explorer

# 或直接下载 ZIP 解压
```

#### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件（可选）
# Windows: notepad .env
# macOS / Linux: nano .env
```

#### 5. 启动项目

```bash
python src/main.py
```

---

## 云服务部署

### Sealos 一键部署（推荐）

**优势**：免费云服务、一键部署、亚洲服务器

#### 步骤：

1. **访问 Sealos 模板**
   - 打开：https://template.hzh.sealos.run/deploy?templateName=openagents
   - 或联系小助手领取优惠券

2. **配置应用**
   - 应用名称：`yougame-explorer`
   - 镜像：使用 OpenAgents 官方镜像
   - 环境变量：从 `.env` 复制

3. **部署**
   - 点击"部署"按钮
   - 等待几秒，应用自动启动

4. **访问**
   - 获取分配的 URL
   - 通过 Studio 连接

---

### Zeabur 一键部署

**优势**：免费云服务、全球加速

#### 步骤：

1. **访问 Zeabur**
   - 打开：https://zeabur.com/zh-TW/events?code=openagents_2025
   - 注册账号（可使用兑换码）

2. **创建新项目**
   - 项目名称：`yougame-explorer`

3. **部署服务**
   - 选择"预构建服务"
   - 导入 GitHub 仓库
   - 或上传代码包

4. **配置环境变量**
   - 在设置中添加 `.env` 中的变量

5. **启动**
   - 自动构建和部署
   - 获取访问 URL

---

## Docker 部署

### 使用 Docker Compose

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 手动 Docker

```bash
# 构建镜像
docker build -t yougame-explorer .

# 运行容器
docker run -d \
  --name yougame-explorer \
  -p 8000:8000 \
  --env-file .env \
  yougame-explorer
```

---

## 配置说明

### 必需配置

无需配置即可运行基础功能！

### 可选配置

#### LLM API（用于高级功能）

```bash
# Claude API（推荐）
ANTHROPIC_API_KEY=your_key_here

# 或 OpenAI API
OPENAI_API_KEY=your_key_here
```

#### 虎牙监控

```yaml
# config/players.yaml
monitored_players:
  - name: "主播名"
    huya_id: "房间号"
    priority: "high"  # high/medium/low
```

---

## 健康检查

### 检查服务状态

```bash
# 测试 Python 环境
python --version

# 测试依赖
python -c "import aiohttp; print('OK')"

# 测试导入
python -c "from src.agents.router_agent import RouterAgent; print('OK')"
```

### 常见错误

#### 错误：ModuleNotFoundError

```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

#### 错误：Permission denied

```bash
# Linux / macOS
chmod +x src/main.py
```

#### 错误：Port already in use

```bash
# 修改端口
# .env 文件
OPENAGENTS_PORT=8001
```

---

## 监控和日志

### 查看日志

```bash
# 日志文件位置
tail -f logs/yougame.log

# 或使用日志查看工具
```

### 性能监控

（可选）集成 Prometheus + Grafana

---

## 更新部署

### 拉取最新代码

```bash
git pull origin main

# 或重新下载代码包
```

### 更新依赖

```bash
pip install -r requirements.txt --upgrade
```

### 重启服务

```bash
# 停止当前运行
# 然后重新启动
python src/main.py
```

---

## 安全建议

### 敏感信息保护

```bash
# 确保 .env 在 .gitignore 中
echo ".env" >> .gitignore

# 不要在代码中硬编码 API Key
```

### 访问控制

```yaml
# config/network.yaml
security:
  enable_auth: true  # 生产环境建议启用
```

---

## 备份和恢复

### 备份数据

```bash
# 备份配置
cp -r config/ config.backup/

# 备份日志
cp -r logs/ logs.backup/
```

### 恢复

```bash
# 恢复配置
cp -r config.backup/* config/
```

---

## 故障排查

### 问题：无法检测直播状态

**可能原因**：
1. 网络问题
2. 虎牙页面结构变化
3. 房间号错误

**解决方案**：
```bash
# 测试网络连接
ping www.huya.com

# 验证房间号
# 访问 https://www.huya.com/房间号
# 确认页面可访问
```

### 问题：启动失败

**检查步骤**：
```bash
# 1. 检查 Python 版本
python --version

# 2. 检查依赖
pip list | grep aiohttp

# 3. 查看错误日志
cat logs/yougame.log
```

---

## 获取帮助

- 📖 [文档](README.md)
- 💬 [Discord 社区](https://discord.com/invite/openagents)
- 🐛 [GitHub Issues](https://github.com/openagents-org/openagents/issues)

---

**部署成功后，就可以开始使用小游探了！** 🎉
