# 小游探云端部署指南

## 🚀 部署包已准备完成

**部署包文件**: `yougame-deploy.zip` (约 197KB)

## 云端部署选项

### 选项1: Sealos 部署（推荐 - 免费）

**优势**: 免费云服务、一键部署、亚洲服务器

**步骤**:
1. 访问 [Sealos 模板](https://template.hzh.sealos.run/deploy?templateName=openagents)
2. 点击"部署应用"
3. 配置应用:
   - 应用名称: `yougame-explorer`
   - 上传 `yougame-deploy.zip`
4. 配置环境变量:
   ```
   OPENAGENTS_HOST=0.0.0.0
   OPENAGENTS_PORT=8000
   OPENAI_API_KEY=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
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL=xiaomi/mimo-v2-flash:free
   ```
5. 点击"部署"
6. 等待部署完成，获取访问URL

### 选项2: Zeabur 部署（免费）

**优势**: 全球加速、简单易用

**步骤**:
1. 访问 [Zeabur](https://zeabur.com/zh-TW/events?code=openagents_2025)
2. 注册账号（可使用兑换码）
3. 创建新项目: `yougame-explorer`
4. 选择"上传代码包"
5. 上传 `yougame-deploy.zip`
6. 在设置中添加环境变量（同上）
7. 点击部署

### 选项3: Railway 部署

**步骤**:
1. 访问 [Railway](https://railway.app)
2. 创建新项目
3. 选择"Deploy from GitHub repo" 或上传代码
4. 配置环境变量
5. 部署

### 选项4: Render 部署

**步骤**:
1. 访问 [Render](https://render.com)
2. 创建 Web Service
3. 连接 GitHub 或上传代码
4. 配置构建命令: `pip install -r requirements.txt`
5. 配置启动命令: `python src/main.py --openagents`
6. 添加环境变量

## 🔧 环境变量配置

**必需配置**:
```bash
OPENAGENTS_HOST=0.0.0.0
OPENAGENTS_PORT=8000
```

**LLM配置** (已配置OpenRouter免费模型):
```bash
OPENAI_API_KEY=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
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=xiaomi/mimo-v2-flash:free
```

**可选配置**:
```bash
LLM_DAILY_LIMIT=45
LLM_CACHE_TTL=3600
LLM_TIMEOUT=10
LOG_LEVEL=INFO
```

## 🏥 部署后验证

1. **健康检查**: 访问 `https://your-app-url/health`
   - 应该返回: `{"status": "healthy", ...}`

2. **功能测试**: 
   - 通过 OpenAgents Studio 连接
   - 发送测试消息: "你好"
   - 查看响应

## 📊 监控和日志

- **日志查看**: 大多数平台提供日志查看功能
- **性能监控**: 检查内存和CPU使用情况
- **错误追踪**: 关注启动错误和运行时错误

## 🔒 安全建议

1. **API Key 保护**: 
   - 不要在代码中硬编码
   - 使用环境变量
   - 定期轮换

2. **访问控制**:
   - 考虑添加认证
   - 限制访问来源

## 🆘 故障排查

### 常见问题

**1. 部署失败**
- 检查 requirements.txt 是否完整
- 确认 Python 版本兼容 (3.10+)
- 查看构建日志

**2. 启动失败**
- 检查环境变量配置
- 确认端口设置正确
- 查看应用日志

**3. 健康检查失败**
- 确认 `/health` 端点可访问
- 检查防火墙设置
- 验证端口绑定

### 获取帮助

- 📖 查看 `docs/DEPLOYMENT.md`
- 🐛 GitHub Issues
- 💬 社区支持

## 🎉 部署成功！

部署完成后，你就可以：
- 通过 OpenAgents Studio 连接使用
- 查询游戏主播直播状态
- 生成游戏圈简报
- 享受 AI 助手服务

**下一步**: 完成 MVP 其他功能开发！