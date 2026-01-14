#!/usr/bin/env python3
"""
Docker配置测试脚本
"""
import sys
import os
from pathlib import Path

def test_file_structure():
    """测试文件结构"""
    print("🔍 检查文件结构...")
    
    required_files = [
        "src/main.py",
        "requirements.txt",
        "Dockerfile",
        "start.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"✅ {file}")
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    return True

def test_python_import():
    """测试Python导入"""
    print("\n🐍 测试Python导入...")
    
    # 添加项目根目录到路径
    ROOT_DIR = Path(__file__).parent
    sys.path.insert(0, str(ROOT_DIR))
    
    try:
        from src.main import YouGameExplorer
        print("✅ 主程序导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_start_script():
    """测试启动脚本"""
    print("\n🚀 测试启动脚本...")
    
    try:
        with open("start.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        if "from src.main import main" in content:
            print("✅ 启动脚本配置正确")
            return True
        else:
            print("❌ 启动脚本配置错误")
            return False
    except Exception as e:
        print(f"❌ 启动脚本测试失败: {e}")
        return False

def main():
    print("🧪 Docker配置测试")
    print("=" * 40)
    
    tests = [
        test_file_structure,
        test_python_import,
        test_start_script
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 40)
    if all(results):
        print("🎉 所有测试通过！Docker配置正确")
        print("\n📋 Docker命令:")
        print("  docker build -t yougame-explorer .")
        print("  docker run -p 8000:8000 yougame-explorer")
        print("  docker-compose up -d")
    else:
        print("❌ 部分测试失败，请检查配置")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)