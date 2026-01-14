# 小游探 Zeabur 部署指南

## 🚨 修复容器重启问题

此版本专门修复了Zeabur部署中的容器重启循环问题：

### ✅ 已修复的问题
- 简化了依赖，移除了可能导致冲突的包
- 优化了启动脚本，增加了错误处理
- 修复了aiohttp导入问题
- 延长了健康检查时间
- 添加了环境变量默认值

## 🚀 Zeabur 部署步骤

### 1. 准备部署
1. 访问 [Zeabur](https://zeabur.com)
2. 登录或注册账号
3. 创建新项目

### 2. 上传代码
1. 选择 "Deploy from Source Code"
2. 上传此文件夹的所有内容
3. 或者连接GitHub仓库

### 3. 配置环境变量
在Zeabur项目设置中添加以下环境变量：

```bash
# 必需配置
OPENAGENTS_HOST=0.0.0.0
OPENAGENTS_PORT=8000

# LLM配置（已预设，可选修改）
OPENAI_API_KEY=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
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=xiaomi/mimo-v2-flash:free

# 可选配置
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### 4. 部署设置
- **构建命令**: 自动检测 (使用Dockerfile)
- **启动命令**: `python zeabur-start.py`
- **端口**: 8000
- **健康检查**: `/health`

### 5. 部署
点击 "Deploy" 按钮，等待部署完成

## 🔍 故障排查

### 如果仍然出现重启问题：

1. **查看日志**
   - 在Zeabur控制台查看详细日志
   - 寻找具体的错误信息

2. **检查资源限制**
   - 确保内存分配足够 (建议512MB+)
   - 检查CPU限制

3. **验证环境变量**
   - 确保所有必需的环境变量都已设置
   - 检查API Key是否有效

4. **手动测试**
   ```bash
   # 本地测试启动脚本
   python zeabur-start.py
   ```

### 常见错误解决方案

**错误**: `ModuleNotFoundError`
**解决**: 检查requirements.txt是否完整

**错误**: `Port already in use`
**解决**: 确保OPENAGENTS_PORT设置为8000

**错误**: `Health check failed`
**解决**: 等待更长时间，健康检查已延长到60秒

## 📊 部署后验证

1. **检查服务状态**
   - 访问分配的URL
   - 检查 `/health` 端点

2. **功能测试**
   - 通过OpenAgents Studio连接
   - 发送测试消息

3. **日志监控**
   - 观察启动日志
   - 确认所有Agent正常初始化

## 🆘 获取帮助

如果问题仍然存在：
1. 复制完整的错误日志
2. 检查环境变量配置
3. 尝试重新部署
4. 联系技术支持

## 📝 部署检查清单

- [ ] 上传了正确的代码包
- [ ] 设置了所有必需的环境变量
- [ ] 端口配置为8000
- [ ] 健康检查路径设置为 `/health`
- [ ] 等待足够的启动时间 (2-3分钟)

部署成功后，你的小游探AI助手就可以在云端运行了！