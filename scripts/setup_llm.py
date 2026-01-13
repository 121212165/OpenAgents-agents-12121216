#!/usr/bin/env python3
"""
LLM配置向导
帮助用户快速配置大模型API
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """创建.env文件"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        print("✅ .env文件已存在")
        return True
    
    if not env_example.exists():
        print("❌ 未找到.env.example文件")
        return False
    
    # 复制示例文件
    with open(env_example, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已创建.env文件")
    return True

def setup_openrouter():
    """配置OpenRouter"""
    print("\n🔧 配置OpenRouter（推荐）")
    print("OpenRouter提供多种免费模型，注册简单")
    print("访问：https://openrouter.ai/")
    
    api_key = input("\n请输入OpenRouter API Key（或按回车跳过）: ").strip()
    
    if not api_key:
        return None
    
    # 选择模型
    print("\n选择模型：")
    models = [
        ("1", "xiaomi/mimo-v2-flash:free", "小米模型（免费，推荐）"),
        ("2", "google/gemini-flash-1.5:free", "Google Gemini（免费）"),
        ("3", "meta-llama/llama-3.2-3b-instruct:free", "Meta Llama（免费）"),
        ("4", "microsoft/phi-3-mini-128k-instruct:free", "Microsoft Phi-3（免费）"),
        ("5", "自定义", "输入其他模型名称")
    ]
    
    for num, model, desc in models:
        print(f"  {num}. {desc}")
    
    choice = input("\n请选择模型（默认1）: ").strip() or "1"
    
    if choice == "5":
        model = input("请输入模型名称: ").strip()
    else:
        model_map = {str(i): models[i-1][1] for i in range(1, 5)}
        model = model_map.get(choice, models[0][1])
    
    return {
        "OPENAI_API_KEY": api_key,
        "OPENAI_BASE_URL": "https://openrouter.ai/api/v1",
        "OPENAI_MODEL": model
    }

def setup_claude():
    """配置Claude"""
    print("\n🔧 配置Claude")
    print("Claude是Anthropic的高质量模型，需要付费API")
    print("访问：https://console.anthropic.com/")
    
    api_key = input("\n请输入Anthropic API Key（或按回车跳过）: ").strip()
    
    if not api_key:
        return None
    
    return {
        "ANTHROPIC_API_KEY": api_key,
        "CLAUDE_MODEL": "claude-3-5-sonnet-20241022"
    }

def setup_openai():
    """配置OpenAI"""
    print("\n🔧 配置OpenAI")
    print("OpenAI提供GPT系列模型，需要付费API")
    print("访问：https://platform.openai.com/")
    
    api_key = input("\n请输入OpenAI API Key（或按回车跳过）: ").strip()
    
    if not api_key:
        return None
    
    return {
        "OPENAI_API_KEY": api_key,
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
        "OPENAI_MODEL": "gpt-3.5-turbo"
    }

def setup_ollama():
    """配置Ollama"""
    print("\n🔧 配置Ollama（本地模型）")
    print("Ollama可以在本地运行开源模型，完全免费")
    print("安装：https://ollama.ai/")
    print("使用前请确保Ollama服务正在运行：ollama serve")
    
    confirm = input("\n是否配置Ollama？(y/N): ").strip().lower()
    
    if confirm != 'y':
        return None
    
    # 选择模型
    print("\n选择模型：")
    models = [
        ("1", "llama3.2:3b", "Llama 3.2 3B（推荐，较小）"),
        ("2", "llama3.2:1b", "Llama 3.2 1B（最小）"),
        ("3", "qwen2.5:3b", "Qwen 2.5 3B（中文友好）"),
        ("4", "自定义", "输入其他模型名称")
    ]
    
    for num, model, desc in models:
        print(f"  {num}. {desc}")
    
    choice = input("\n请选择模型（默认1）: ").strip() or "1"
    
    if choice == "4":
        model = input("请输入模型名称: ").strip()
    else:
        model_map = {str(i): models[i-1][1] for i in range(1, 4)}
        model = model_map.get(choice, models[0][1])
    
    return {
        "OPENAI_API_KEY": "ollama",
        "OPENAI_BASE_URL": "http://localhost:11434/v1",
        "OPENAI_MODEL": model
    }

def update_env_file(config):
    """更新.env文件"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ .env文件不存在")
        return False
    
    # 读取现有内容
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新配置
    updated_lines = []
    config_keys = set(config.keys())
    
    for line in lines:
        line = line.rstrip()
        
        # 检查是否是要更新的配置行
        updated = False
        for key, value in config.items():
            if line.startswith(f"{key}=") or line.startswith(f"# {key}="):
                updated_lines.append(f"{key}={value}")
                config_keys.discard(key)
                updated = True
                break
        
        if not updated:
            updated_lines.append(line)
    
    # 添加新的配置项
    for key in config_keys:
        updated_lines.append(f"{key}={config[key]}")
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_lines) + '\n')
    
    print("✅ .env文件已更新")
    return True

def main():
    """主函数"""
    print("🚀 小游探 LLM配置向导")
    print("=" * 50)
    
    # 创建.env文件
    if not create_env_file():
        return False
    
    print("\n选择LLM提供商：")
    print("1. OpenRouter（推荐新手，有免费额度）")
    print("2. Claude（高质量，需付费）")
    print("3. OpenAI（经典选择，需付费）")
    print("4. Ollama（本地运行，完全免费）")
    print("5. 跳过配置（使用降级模式）")
    
    choice = input("\n请选择（默认1）: ").strip() or "1"
    
    config = None
    
    if choice == "1":
        config = setup_openrouter()
    elif choice == "2":
        config = setup_claude()
    elif choice == "3":
        config = setup_openai()
    elif choice == "4":
        config = setup_ollama()
    elif choice == "5":
        print("✅ 跳过LLM配置，将使用降级模式")
        return True
    else:
        print("❌ 无效选择")
        return False
    
    if config:
        if update_env_file(config):
            print("\n🎉 LLM配置完成！")
            print("💡 建议运行以下命令测试配置：")
            print("   python scripts/check_llm_config.py")
        else:
            print("❌ 配置更新失败")
            return False
    else:
        print("✅ 跳过LLM配置")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)