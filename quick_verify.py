#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 快速验证脚本 - 确保系统能正常工作
"""
快速验证小游探系统的核心功能
运行: python quick_verify.py
"""

import asyncio
import sys
import io
from pathlib import Path
from datetime import datetime

# 设置Windows控制台编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from loguru import logger
from src.agents.router_agent import RouterAgent, QueryContext
from src.agents.live_monitor_agent import LiveMonitorAgent
from src.agents.briefing_agent import BriefingAgent
from src.agents.data_source_agent import DataSourceAgent


class QuickVerifier:
    """快速验证器"""
    
    def __init__(self):
        self.router = None
        self.results = []
        
    async def setup(self):
        """设置系统"""
        print("\n" + "="*60)
        print("🚀 小游探快速验证")
        print("="*60 + "\n")
        
        print("📦 步骤1: 创建Agent...")
        try:
            data_source = DataSourceAgent()
            live_monitor = LiveMonitorAgent()
            briefing_agent = BriefingAgent()
            self.router = RouterAgent()
            
            self.router.register_agent("live_monitor", live_monitor)
            self.router.register_agent("briefing_agent", briefing_agent)
            self.router.register_agent("data_source", data_source)
            
            await data_source.on_startup()
            await live_monitor.on_startup()
            await briefing_agent.on_startup()
            await self.router.on_startup()
            
            print("✅ Agent创建成功\n")
            return True
        except Exception as e:
            print(f"❌ Agent创建失败: {e}\n")
            return False
    
    async def test_query(self, query: str, expected_success: bool = True):
        """测试单个查询"""
        print(f"🔍 测试查询: {query}")
        
        try:
            context = QueryContext(
                user_id="verify_user",
                session_id="verify_session",
                timestamp=datetime.now()
            )
            
            start_time = datetime.now()
            result = await self.router.smart_process(query, context)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            success = result.get("success", False)
            response = result.get("response", "")
            intent = result.get("intent", "未知")
            
            if success == expected_success:
                print(f"✅ 测试通过")
                print(f"   意图: {intent}")
                print(f"   响应: {response[:80]}...")
                print(f"   耗时: {elapsed:.2f}s\n")
                self.results.append(("PASS", query))
                return True
            else:
                print(f"❌ 测试失败")
                print(f"   期望成功: {expected_success}, 实际: {success}")
                print(f"   响应: {response[:80]}...\n")
                self.results.append(("FAIL", query))
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}\n")
            self.results.append(("ERROR", query))
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("📋 步骤2: 运行核心功能测试\n")
        
        # 测试1: 问候
        await self.test_query("你好")
        
        # 测试2: 直播查询
        await self.test_query("Faker在直播吗？")
        
        # 测试3: 简报生成
        await self.test_query("生成今日简报")
        
        # 测试4: 系统状态
        await self.test_query("系统状态")
        
        print("✅ 核心功能测试完成\n")
    
    def print_summary(self):
        """打印测试总结"""
        print("="*60)
        print("📊 测试总结")
        print("="*60 + "\n")
        
        passed = sum(1 for r in self.results if r[0] == "PASS")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        errors = sum(1 for r in self.results if r[0] == "ERROR")
        total = len(self.results)
        
        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  错误: {errors}")
        print()
        
        if failed > 0 or errors > 0:
            print("失败的测试:")
            for status, query in self.results:
                if status != "PASS":
                    print(f"  {status}: {query}")
            print()
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        if success_rate >= 80:
            print("🎉 系统运行良好！")
            return True
        elif success_rate >= 60:
            print("⚠️  系统基本可用，但有些问题需要修复")
            return False
        else:
            print("❌ 系统存在严重问题，需要立即修复")
            return False


async def main():
    """主函数"""
    verifier = QuickVerifier()
    
    # 设置系统
    if not await verifier.setup():
        print("❌ 系统设置失败，无法继续测试")
        sys.exit(1)
    
    # 运行测试
    await verifier.run_all_tests()
    
    # 打印总结
    success = verifier.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
        sys.exit(1)
