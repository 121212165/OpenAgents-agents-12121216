#!/usr/bin/env python3
"""
测试Zeabur部署修复
验证PORT环境变量正确读取
"""
import os
import sys

# 模拟Zeabur环境
os.environ['PORT'] = '8080'

from src.utils.server_config import get_server_config

def test_port_config():
    """测试端口配置"""
    print("="*50)
    print("测试Zeabur端口配置修复")
    print("="*50)
    
    # 测试1: PORT环境变量
    print("\n测试1: 使用PORT环境变量")
    os.environ['PORT'] = '8080'
    if 'OPENAGENTS_PORT' in os.environ:
        del os.environ['OPENAGENTS_PORT']
    
    host, port = get_server_config()
    assert host == "0.0.0.0", f"主机应为0.0.0.0，实际为{host}"
    assert port == 8080, f"端口应为8080，实际为{port}"
    print(f"✅ 通过: host={host}, port={port}")
    
    # 测试2: OPENAGENTS_PORT回退
    print("\n测试2: 回退到OPENAGENTS_PORT")
    if 'PORT' in os.environ:
        del os.environ['PORT']
    os.environ['OPENAGENTS_PORT'] = '9000'
    
    host, port = get_server_config()
    assert host == "0.0.0.0", f"主机应为0.0.0.0，实际为{host}"
    assert port == 9000, f"端口应为9000，实际为{port}"
    print(f"✅ 通过: host={host}, port={port}")
    
    # 测试3: 默认端口
    print("\n测试3: 使用默认端口")
    if 'PORT' in os.environ:
        del os.environ['PORT']
    if 'OPENAGENTS_PORT' in os.environ:
        del os.environ['OPENAGENTS_PORT']
    
    host, port = get_server_config()
    assert host == "0.0.0.0", f"主机应为0.0.0.0，实际为{host}"
    assert port == 8000, f"端口应为8000，实际为{port}"
    print(f"✅ 通过: host={host}, port={port}")
    
    # 测试4: 无效端口
    print("\n测试4: 处理无效端口")
    os.environ['PORT'] = 'invalid'
    
    host, port = get_server_config()
    assert host == "0.0.0.0", f"主机应为0.0.0.0，实际为{host}"
    assert port == 8000, f"端口应回退到8000，实际为{port}"
    print(f"✅ 通过: host={host}, port={port}")
    
    print("\n" + "="*50)
    print("所有测试通过！✅")
    print("="*50)

if __name__ == "__main__":
    try:
        test_port_config()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
