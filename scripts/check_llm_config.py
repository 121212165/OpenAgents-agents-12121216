#!/usr/bin/env python3
"""
LLM配置检查脚本
检查大模型配置是否正确，并提供配置建议
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.llm_client import LLMClient
from loguru import logger

def check_env_file():
    """检查环境变量文件"""
    print("🔍 检查环境变量配置...")
    
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists():
        print("❌ 未找到 .env 文件")
        if env_example.exists():
            print("💡 建议：复制 .env.example 为 .env 并配置API密钥")
            print(f"   cp {env_example} {env_file}")
        return False
    
    print("✅ 找到 .env 文件")
    return True

def check_api_keys():
    """检查API密钥配置"""
    print("\n🔑 检查API密钥配置...")
    
    # 检查各种API密钥
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_base = os.getenv("OPENAI_BASE_URL", "")
    
    configs = []
    
    if openai_key and "openrouter.ai" in openai_base:
        configs.append("OpenRouter")
        print("✅ 检测到 OpenRouter 配置")
    elif anthropic_key:
        configs.append("Claude")
        print("✅ 检测到 Claude 配置")
    elif openai_key and "api.openai.com" in openai_base:
        configs.append("OpenAI")
        print("✅ 检测到 OpenAI 配置")
    elif openai_key and "localhost" in openai_base:
        configs.append("Ollama")
        print("✅ 检测到 Ollama 配置")
    
    if not configs:
        print("❌ 未检测到有效的API配置")
        print("\n💡 配置建议：")
        print("1. OpenRouter（推荐，有免费额度）：")
        print("   - 注册：https://openrouter.ai/")
        print("   - 设置 OPENAI_API_KEY=your_openrouter_key")
        print("   - 设置 OPENAI_BASE_URL=https://openrouter.ai/api/v1")
        print("   - 设置 OPENAI_MODEL=xiaomi/mimo-v2-flash:free")
        print("\n2. 本地Ollama（完全免费）：")
        print("   - 安装：https://ollama.ai/")
        print("   - 运行：ollama serve")
        print("   - 设置 OPENAI_BASE_URL=http://localhost:11434/v1")
        print("   - 设置 OPENAI_MODEL=llama3.2:3b")
        return False
    
    return True

async def test_llm_connection():
    """测试LLM连接"""
    print("\n🧪 测试LLM连接...")
    
    try:
        client = LLMClient()
        stats = client.get_usage_stats()
        
        print(f"📊 LLM状态：")
        print(f"   提供商: {stats['provider']}")
        print(f"   模型: {stats['model']}")
        print(f"   API配置: {'✅' if stats['api_configured'] else '❌'}")
        print(f"   仅降级模式: {'是' if stats['fallback_only'] else '否'}")
        
        if not stats['api_configured']:
            print("⚠️  未配置API密钥，将使用降级模式")
            return True  # 降级模式也是可以工作的
        
        # 测试简单调用
        print("\n🔄 测试API调用...")
        result = await client.process_with_fallback(
            "intent_classification",
            "你好"
        )
        
        if result.success:
            print(f"✅ API调用成功")
            print(f"   响应来源: {result.source}")
            print(f"   响应时间: {result.response_time:.2f}s")
            if result.tokens_used > 0:
                print(f"   使用Token: {result.tokens_used}")
        else:
            print(f"❌ API调用失败: {result.error}")
            print("💡 将使用降级模式，功能有限但可正常运行")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM客户端初始化失败: {e}")
        return False

def print_configuration_guide():
    """打印配置指南"""
    print("\n📖 配置指南：")
    print("\n1. 免费方案（推荐新手）：")
    print("   - 使用OpenRouter免费模型")
    print("   - 每日有一定免费额度")
    print("   - 注册简单，即用即得")
    
    print("\n2. 本地方案（推荐开发者）：")
    print("   - 安装Ollama运行本地模型")
    print("   - 完全免费，无限制")
    print("   - 需要一定硬件资源")
    
    print("\n3. 付费方案（推荐生产环境）：")
    print("   - OpenAI GPT系列")
    print("   - Claude系列")
    print("   - 质量最高，速度最快")
    
    print("\n4. 降级方案（保底）：")
    print("   - 不配置任何API")
    print("   - 使用内置规则引擎")
    print("   - 功能有限但可运行")

async def main():
    """主函数"""
    print("🚀 小游探 LLM配置检查工具")
    print("=" * 50)
    
    # 检查环境文件
    env_ok = check_env_file()
    
    # 检查API密钥
    api_ok = check_api_keys()
    
    # 测试连接
    connection_ok = await test_llm_connection()
    
    print("\n" + "=" * 50)
    print("📋 检查结果汇总：")
    print(f"   环境文件: {'✅' if env_ok else '❌'}")
    print(f"   API配置: {'✅' if api_ok else '❌'}")
    print(f"   连接测试: {'✅' if connection_ok else '❌'}")
    
    if env_ok and connection_ok:
        print("\n🎉 配置检查完成！系统可以正常运行。")
        if not api_ok:
            print("⚠️  注意：当前使用降级模式，建议配置API以获得更好体验。")
    else:
        print("\n❌ 配置存在问题，请参考上述建议进行修复。")
        print_configuration_guide()
    
    return env_ok and connection_ok

if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 运行检查
    success = asyncio.run(main())
    sys.exit(0 if success else 1)