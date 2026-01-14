#!/bin/bash
# 小游探云端部署打包脚本

echo "正在创建云端部署包..."

# 创建部署目录
mkdir -p deploy-package

# 复制必要文件
cp -r src deploy-package/
cp -r config deploy-package/
cp requirements.txt deploy-package/
cp Dockerfile deploy-package/
cp docker-compose.yml deploy-package/
cp .env.example deploy-package/
cp README.md deploy-package/
cp -r docs deploy-package/

# 创建启动脚本
cat > deploy-package/start.sh << 'EOF'
#!/bin/bash
echo "启动小游探..."
python src/main.py --openagents
EOF

chmod +x deploy-package/start.sh

# 创建部署说明
cat > deploy-package/DEPLOY.md << 'EOF'
# 小游探云端部署包

## 快速部署

### 1. Sealos 部署（推荐）
1. 访问：https://template.hzh.sealos.run/deploy?templateName=openagents
2. 上传此部署包
3. 配置环境变量（复制.env.example到.env并修改）
4. 点击部署

### 2. Zeabur 部署
1. 访问：https://zeabur.com/zh-TW/events?code=openagents_2025
2. 创建新项目
3. 上传此部署包
4. 配置环境变量
5. 部署

### 3. Docker 部署
```bash
docker-compose up -d
```

## 环境变量配置

复制 .env.example 为 .env，然后配置：

```bash
# OpenAgents 配置
OPENAGENTS_HOST=0.0.0.0
OPENAGENTS_PORT=8000

# LLM API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=xiaomi/mimo-v2-flash:free
```

## 健康检查

部署后访问：http://your-domain/health

## 支持

如有问题，请查看 docs/DEPLOYMENT.md
EOF

echo "✅ 云端部署包创建完成：deploy-package/"
echo "📦 包含文件："
ls -la deploy-package/

echo ""
echo "🚀 下一步："
echo "1. 压缩部署包：zip -r yougame-deploy.zip deploy-package/"
echo "2. 选择云服务平台部署"
echo "3. 上传部署包"
echo "4. 配置环境变量"