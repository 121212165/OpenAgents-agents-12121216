#!/usr/bin/env python3
"""
小游探部署脚本
支持本地、Docker、云服务部署
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"错误: {result.stderr}")
        sys.exit(1)
    return result

def check_requirements():
    """检查部署要求"""
    print("检查部署要求...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 10):
        print(f"错误: 需要Python 3.10+，当前版本: {python_version.major}.{python_version.minor}")
        sys.exit(1)
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    
    # 检查必需文件
    required_files = [
        "requirements.txt",
        "src/main.py",
        ".env.example"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"错误: 缺少必需文件: {file}")
            sys.exit(1)
    
    print("✅ 必需文件检查通过")

def setup_environment():
    """设置环境"""
    print("设置环境...")
    
    # 创建.env文件（如果不存在）
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env")
            print("✅ 已创建.env文件，请根据需要修改配置")
        else:
            print("警告: 没有找到.env.example文件")
    
    # 创建必需目录
    dirs = ["logs", "config"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {dir_name}")

def install_dependencies():
    """安装依赖"""
    print("安装Python依赖...")
    run_command("pip install -r requirements.txt")
    print("✅ 依赖安装完成")

def deploy_local():
    """本地部署"""
    print("开始本地部署...")
    
    check_requirements()
    setup_environment()
    install_dependencies()
    
    print("\n" + "="*50)
    print("本地部署完成！")
    print("="*50)
    print("启动命令:")
    print("  python src/main.py              # 交互模式")
    print("  python src/main.py --demo       # 演示模式")
    print("  python src/main.py --openagents # OpenAgents模式")
    print("="*50)

def deploy_docker():
    """Docker部署"""
    print("开始Docker部署...")
    
    # 检查Docker
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print("错误: 未安装Docker")
        sys.exit(1)
    
    # 检查docker-compose
    result = run_command("docker-compose --version", check=False)
    if result.returncode != 0:
        print("错误: 未安装docker-compose")
        sys.exit(1)
    
    setup_environment()
    
    # 构建和启动
    print("构建Docker镜像...")
    run_command("docker-compose build")
    
    print("启动服务...")
    run_command("docker-compose up -d")
    
    print("\n" + "="*50)
    print("Docker部署完成！")
    print("="*50)
    print("管理命令:")
    print("  docker-compose logs -f          # 查看日志")
    print("  docker-compose stop             # 停止服务")
    print("  docker-compose restart          # 重启服务")
    print("  docker-compose down             # 删除容器")
    print("="*50)

def deploy_cloud():
    """云服务部署指南"""
    print("\n" + "="*50)
    print("云服务部署指南")
    print("="*50)
    
    print("\n1. Sealos 部署（推荐）:")
    print("   - 访问: https://template.hzh.sealos.run/deploy?templateName=openagents")
    print("   - 应用名称: yougame-explorer")
    print("   - 上传项目代码包")
    print("   - 配置环境变量（从.env复制）")
    
    print("\n2. Zeabur 部署:")
    print("   - 访问: https://zeabur.com/zh-TW/events?code=openagents_2025")
    print("   - 创建新项目: yougame-explorer")
    print("   - 导入GitHub仓库或上传代码")
    print("   - 配置环境变量")
    
    print("\n3. 其他云服务:")
    print("   - 使用Docker镜像部署")
    print("   - 确保开放8000端口")
    print("   - 配置健康检查: /health")
    
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description="小游探部署脚本")
    parser.add_argument("mode", choices=["local", "docker", "cloud"], 
                       help="部署模式: local(本地) / docker(Docker) / cloud(云服务指南)")
    
    args = parser.parse_args()
    
    if args.mode == "local":
        deploy_local()
    elif args.mode == "docker":
        deploy_docker()
    elif args.mode == "cloud":
        deploy_cloud()

if __name__ == "__main__":
    main()