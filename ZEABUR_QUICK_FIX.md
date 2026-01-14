# Zeabur 502错误快速修复指南

## 问题诊断

你的应用在Zeabur上出现502错误的根本原因是：
- **Zeabur提供 `PORT` 环境变量**（云平台标准）
- **你的代码读取 `OPENAGENTS_PORT`**（自定义变量）
- **端口不匹配导致Zeabur无法连接到你的应用**

## 已修复的内容

### 1. 创建了端口配置模块 ✅
- 文件: `src/utils/server_config.py`
- 功能: 按优先级读取 PORT → OPENAGENTS_PORT → 8000
- 主机: 始终绑定到 0.0.0.0（接受外部连接）

### 2. 更新了主程序 ✅
- 文件: `src/main.py`
- 改动: 使用 `get_server_config()` 替代硬编码配置

### 3. 更新了启动脚本 ✅
- 文件: `zeabur-start.py` 和 `deploy-zeabur/zeabur-start.py`
- 改动: 移除 OPENAGENTS_PORT 设置，让Zeabur的PORT生效

## 部署步骤

### 方案A: 重新部署（推荐）

1. **提交代码到Git**
   ```bash
   git add .
   git commit -m "fix: 修复Zeabur端口配置，使用PORT环境变量"
   git push
   ```

2. **在Zeabur重新部署**
   - 进入你的Zeabur项目
   - 点击 "Redeploy" 或等待自动部署
   - Zeabur会自动设置PORT环境变量

3. **验证部署**
   - 访问你的应用URL
   - 检查 `/health` 端点: `https://你的域名/health`
   - 应该看到: `{"status": "healthy", ...}`

### 方案B: 手动设置环境变量（临时方案）

如果你不想重新部署，可以在Zeabur控制台手动设置：

1. 进入Zeabur项目设置
2. 找到环境变量配置
3. 确认 `PORT` 变量存在（Zeabur自动设置）
4. 重启服务

## 验证修复

### 本地测试
```bash
# 测试端口配置
python test_zeabur_fix.py

# 模拟Zeabur环境启动
set PORT=8080
python zeabur-start.py
```

### 检查日志
部署后查看Zeabur日志，应该看到：
```
服务器配置: host=0.0.0.0, port=<Zeabur分配的端口>
PORT环境变量: <Zeabur分配的端口>
健康检查服务器启动在 http://0.0.0.0:<端口>
```

## 下一步优化（可选）

根据spec中的任务列表，还可以继续实现：

1. **Task 2**: 实现完整的Web服务器和健康检查
2. **Task 3**: 添加API查询端点
3. **Task 5**: 实现错误恢复和重试逻辑
4. **Task 6**: 添加异常处理和日志

但目前的修复应该足以解决502错误！

## 故障排查

如果部署后仍有问题：

1. **检查Zeabur日志**
   - 确认PORT环境变量被正确读取
   - 查看是否有端口绑定错误

2. **检查健康检查**
   - Zeabur可能配置了健康检查端点
   - 确保 `/health` 端点正常响应

3. **检查启动时间**
   - 如果应用启动太慢，Zeabur可能超时
   - 考虑优化初始化流程

## 联系支持

如果问题持续，可以：
- 查看Zeabur文档: https://zeabur.com/docs
- 检查Zeabur Agent日志（在错误页面点击"查看"）
- 联系Zeabur支持团队
