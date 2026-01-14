"""
性能测试脚本 - 任务五：性能优化和用户体验
测试Agent并发处理、缓存性能和响应格式化
"""

import asyncio
import time
from datetime import datetime
from loguru import logger

# 测试配置
TEST_CONFIG = {
    "queries": [
        "Uzi直播了吗",
        "Faker直播了吗",
        "生成今日简报",
        "热门游戏有哪些",
        "系统状态"
    ],
    "iterations": 3,  # 每个查询重复次数
    "max_concurrent": 5  # 最大并发数
}


class PerformanceTest:
    """性能测试器"""
    
    def __init__(self):
        self.results = []
    
    async def test_concurrent_queries(self, agent):
        """测试并发查询性能"""
        logger.info("=" * 60)
        logger.info("测试1: 并发查询性能")
        logger.info("=" * 60)
        
        queries = TEST_CONFIG["queries"]
        
        for concurrent_count in [1, 3, 5]:
            logger.info(f"\n并发数: {concurrent_count}")
            
            start_time = time.time()
            
            # 创建并发任务
            tasks = [
                agent.process(query)
                for query in queries[:concurrent_count]
            ]
            
            # 执行并测量时间
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # 记录结果
            success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
            avg_time = total_time / concurrent_count
            
            logger.info(f"✅ 总耗时: {total_time:.2f}s")
            logger.info(f"✅ 成功: {success_count}/{concurrent_count}")
            logger.info(f"✅ 平均响应: {avg_time:.2f}s")
            
            self.results.append({
                "test": "concurrent_queries",
                "concurrent_count": concurrent_count,
                "total_time": total_time,
                "avg_time": avg_time,
                "success_rate": f"{success_count}/{concurrent_count}"
            })
    
    async def test_cache_performance(self, agent):
        """测试缓存性能"""
        logger.info("\n" + "=" * 60)
        logger.info("测试2: 缓存性能")
        logger.info("=" * 60)
        
        query = "Uzi直播了吗"
        
        # 第一次查询（缓存未命中）
        logger.info(f"\n第一次查询 '{query}' (缓存未命中)")
        start_time = time.time()
        result1 = await agent.process(query)
        first_time = time.time() - start_time
        
        logger.info(f"⏱️ 耗时: {first_time:.3f}s")
        logger.info(f"✅ 结果: {result1.get('success')}")
        
        # 第二次查询（应该命中缓存）
        logger.info(f"\n第二次查询 '{query}' (缓存命中)")
        start_time = time.time()
        result2 = await agent.process(query)
        cached_time = time.time() - start_time
        
        logger.info(f"⏱️ 耗时: {cached_time:.3f}s")
        logger.info(f"✅ 结果: {result2.get('success')}")
        
        # 计算性能提升
        if first_time > 0:
            speedup = first_time / cached_time
            improvement = ((first_time - cached_time) / first_time) * 100
            logger.info(f"\n🚀 性能提升: {speedup:.2f}x")
            logger.info(f"📉 时间减少: {improvement:.1f}%")
        
        self.results.append({
            "test": "cache_performance",
            "first_query_time": first_time,
            "cached_query_time": cached_time,
            "speedup": first_time / cached_time if cached_time > 0 else 0
        })
    
    async def test_response_format(self, agent):
        """测试响应格式"""
        logger.info("\n" + "=" * 60)
        logger.info("测试3: 响应格式化")
        logger.info("=" * 60)
        
        test_queries = [
            ("直播查询", "Uzi直播了吗"),
            ("简报生成", "生成今日简报"),
            ("系统状态", "系统状态")
        ]
        
        for intent, query in test_queries:
            logger.info(f"\n测试: {intent}")
            logger.info(f"查询: {query}")
            
            result = await agent.process(query)
            
            if result.get('success'):
                response = result.get('response', '')
                logger.info(f"✅ 响应长度: {len(response)} 字符")
                
                # 检查是否包含表情符号
                emoji_count = sum(1 for c in response if ord(c) > 127)
                logger.info(f"✅ 表情符号: {emoji_count} 个")
                
                # 显示响应预览
                preview = response[:200] + "..." if len(response) > 200 else response
                logger.info(f"📝 响应预览:\n{preview}\n")
            else:
                logger.error(f"❌ 查询失败: {result.get('response')}")
        
        self.results.append({
            "test": "response_format",
            "status": "completed"
        })
    
    def print_summary(self):
        """打印测试总结"""
        logger.info("\n" + "=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)
        
        for result in self.results:
            test_name = result.get("test", "unknown")
            logger.info(f"\n📊 {test_name}:")
            
            for key, value in result.items():
                if key != "test":
                    logger.info(f"   • {key}: {value}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有测试完成")
        logger.info("=" * 60)


async def run_performance_tests(agent):
    """运行所有性能测试"""
    logger.info("🚀 开始性能测试...")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = PerformanceTest()
    
    try:
        # 测试1: 并发查询
        await tester.test_concurrent_queries(agent)
        
        # 测试2: 缓存性能
        await tester.test_cache_performance(agent)
        
        # 测试3: 响应格式
        await tester.test_response_format(agent)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 打印总结
    tester.print_summary()


if __name__ == "__main__":
    # 导入Router Agent
    import sys
    from pathlib import Path
    
    # 添加项目根目录到路径
    ROOT_DIR = Path(__file__).parent.parent
    sys.path.insert(0, str(ROOT_DIR))
    
    from src.agents.router_agent import RouterAgent
    from src.agents.live_monitor_agent import LiveMonitorAgent
    from src.agents.briefing_agent import BriefingAgent
    from src.agents.data_source_agent import DataSourceAgent
    
    async def main():
        logger.info("初始化Agent...")
        
        # 创建Agent实例
        data_source = DataSourceAgent()
        live_monitor = LiveMonitorAgent()
        briefing = BriefingAgent()
        router = RouterAgent()
        
        # 注册Agent
        router.register_agent("data_source", data_source)
        router.register_agent("live_monitor", live_monitor)
        router.register_agent("briefing_agent", briefing)
        
        # 启动Agent
        await data_source.on_startup()
        await live_monitor.on_startup()
        await briefing.on_startup()
        await router.on_startup()
        
        logger.info("Agent初始化完成\n")
        
        # 运行测试
        await run_performance_tests(router)
    
    asyncio.run(main())
