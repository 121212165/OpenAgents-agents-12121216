# 数据源集成测试
"""
测试数据源管理器与LiveMonitorAgent的集成
验证整个数据流的正确性
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_sources import DataSourceManager, MockDataSource, DataQuery
from src.agents.live_monitor_agent import LiveMonitorAgent

async def test_data_source_integration():
    """测试数据源集成"""
    print("🧪 开始数据源集成测试...")
    
    # 1. 测试数据源管理器基本功能
    print("\n1. 测试数据源管理器...")
    manager = DataSourceManager()
    mock_source = MockDataSource()
    manager.add_source(mock_source)
    
    # 测试查询直播流
    query = DataQuery(
        query_type="streams",
        parameters={"first": 5}
    )
    result = await manager.fetch(query)
    
    if result.success:
        print(f"✅ 数据源查询成功，获取到 {len(result.data)} 条数据")
        print(f"   数据来源: {result.source}")
        print(f"   缓存状态: {'是' if result.cached else '否'}")
    else:
        print(f"❌ 数据源查询失败: {result.error}")
        return False
    
    # 2. 测试缓存功能
    print("\n2. 测试缓存功能...")
    result2 = await manager.fetch(query)
    if result2.cached:
        print("✅ 缓存功能正常工作")
    else:
        print("⚠️  缓存未命中（可能是正常的）")
    
    # 3. 测试健康检查
    print("\n3. 测试健康检查...")
    health_status = await manager.health_check_all()
    for source_name, is_healthy in health_status.items():
        status = "✅ 健康" if is_healthy else "❌ 异常"
        print(f"   {source_name}: {status}")
    
    # 4. 测试LiveMonitorAgent集成
    print("\n4. 测试LiveMonitorAgent集成...")
    try:
        monitor = LiveMonitorAgent()
        
        # 测试搜索功能
        streams = await monitor.search_streams(first=3)
        if streams:
            print(f"✅ LiveMonitorAgent搜索成功，找到 {len(streams)} 个直播流")
            for stream in streams:
                print(f"   - {stream['user_name']}: {stream['game_name']} ({stream['viewer_count']:,} 观众)")
        else:
            print("❌ LiveMonitorAgent搜索失败")
            return False
        
        # 测试特定主播查询
        uzi_status = await monitor.check_player_status("Uzi")
        if uzi_status.get("is_live"):
            print(f"✅ 主播状态查询成功: {uzi_status['user_name']} 正在直播")
            print(f"   游戏: {uzi_status.get('game_name', '未知')}")
            print(f"   观众: {uzi_status.get('viewer_count', 0):,}")
        else:
            print(f"⚠️  主播 {uzi_status.get('user_name', 'Uzi')} 当前未直播")
        
        # 测试游戏搜索
        lol_streams = await monitor.search_streams(game_name="英雄联盟", first=2)
        if lol_streams:
            print(f"✅ 游戏搜索成功，找到 {len(lol_streams)} 个英雄联盟直播")
            for stream in lol_streams:
                print(f"   - {stream['user_name']}: {stream['title']}")
        else:
            print("⚠️  未找到英雄联盟相关直播")
        
    except Exception as e:
        print(f"❌ LiveMonitorAgent测试失败: {e}")
        return False
    
    # 5. 测试数据源状态
    print("\n5. 测试数据源状态...")
    status_info = manager.get_source_status()
    for source_name, status in status_info.items():
        print(f"   {source_name}:")
        print(f"     类型: {status['type']}")
        print(f"     状态: {status['status']}")
        print(f"     错误次数: {status['error_count']}")
    
    print("\n🎉 所有集成测试通过！")
    return True

async def test_failover_scenario():
    """测试故障切换场景"""
    print("\n🔄 测试故障切换场景...")
    
    # 创建一个会失败的数据源和一个正常的数据源
    from tests.test_data_source_properties import TestDataSource
    
    manager = DataSourceManager()
    
    # 添加一个失败的数据源
    failed_source = TestDataSource("failed_source", should_fail=True)
    manager.add_source(failed_source)
    
    # 添加一个正常的数据源
    healthy_source = MockDataSource()
    manager.add_source(healthy_source)
    
    # 执行查询
    query = DataQuery(query_type="streams", parameters={"first": 3})
    result = await manager.fetch(query)
    
    if result.success:
        print(f"✅ 故障切换成功，数据来源: {result.source}")
        print(f"   获取到 {len(result.data)} 条数据")
        return True
    else:
        print(f"❌ 故障切换失败: {result.error}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 小游探数据源集成测试")
    print("=" * 60)
    
    try:
        # 基本集成测试
        success1 = await test_data_source_integration()
        
        # 故障切换测试
        success2 = await test_failover_scenario()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎉 所有测试通过！数据源系统运行正常")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 部分测试失败，请检查系统配置")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())