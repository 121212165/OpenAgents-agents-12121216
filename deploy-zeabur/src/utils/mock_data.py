# 模拟数据生成器
"""
为小游探系统生成真实感的模拟数据
包括直播数据、游戏信息、主播信息等
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

@dataclass
class MockStreamer:
    """模拟主播信息"""
    user_id: str
    user_name: str
    user_login: str
    platform: str
    follower_count: int
    description: str
    profile_image_url: str
    is_partner: bool = False
    language: str = "zh"
    country: str = "CN"

@dataclass
class MockGame:
    """模拟游戏信息"""
    game_id: str
    name: str
    category: str
    popularity_rank: int
    total_viewers: int
    box_art_url: str

class MockDataGenerator:
    """模拟数据生成器"""
    
    def __init__(self):
        self.streamers = self._create_streamers()
        self.games = self._create_games()
        self.stream_titles = self._create_stream_titles()
        self.viewer_fluctuation = {}  # 观众数波动记录
        
        logger.info(f"模拟数据生成器初始化: {len(self.streamers)} 主播, {len(self.games)} 游戏")
    
    def _create_streamers(self) -> List[MockStreamer]:
        """创建模拟主播数据"""
        streamers_data = [
            # 知名电竞选手
            {
                "user_name": "Uzi", "user_login": "uzi", "platform": "虎牙",
                "follower_count": 8500000, "description": "前RNG ADC选手，退役后直播",
                "is_partner": True, "language": "zh", "country": "CN"
            },
            {
                "user_name": "Faker", "user_login": "faker", "platform": "Twitch",
                "follower_count": 3200000, "description": "T1中单选手，三冠王",
                "is_partner": True, "language": "ko", "country": "KR"
            },
            {
                "user_name": "TheShy", "user_login": "theshy", "platform": "虎牙",
                "follower_count": 2800000, "description": "前IG上单选手",
                "is_partner": True, "language": "zh", "country": "CN"
            },
            {
                "user_name": "Rookie", "user_login": "rookie", "platform": "虎牙",
                "follower_count": 2100000, "description": "前IG中单选手",
                "is_partner": True, "language": "zh", "country": "CN"
            },
            
            # 知名主播
            {
                "user_name": "大司马", "user_login": "dasima", "platform": "虎牙",
                "follower_count": 4500000, "description": "知名游戏主播，金牌讲师",
                "is_partner": True, "language": "zh", "country": "CN"
            },
            {
                "user_name": "PDD", "user_login": "pdd", "platform": "虎牙",
                "follower_count": 6200000, "description": "前IG上单选手，现知名主播",
                "is_partner": True, "language": "zh", "country": "CN"
            },
            {
                "user_name": "小团团", "user_login": "xiaotuan", "platform": "虎牙",
                "follower_count": 3800000, "description": "知名女主播",
                "is_partner": True, "language": "zh", "country": "CN"
            },
            
            # 国际主播
            {
                "user_name": "Doublelift", "user_login": "doublelift", "platform": "Twitch",
                "follower_count": 1800000, "description": "前TSM ADC选手",
                "is_partner": True, "language": "en", "country": "US"
            },
            {
                "user_name": "Shroud", "user_login": "shroud", "platform": "Twitch",
                "follower_count": 9200000, "description": "前CS:GO职业选手",
                "is_partner": True, "language": "en", "country": "CA"
            },
            {
                "user_name": "Ninja", "user_login": "ninja", "platform": "Twitch",
                "follower_count": 18500000, "description": "知名Fortnite主播",
                "is_partner": True, "language": "en", "country": "US"
            }
        ]
        
        streamers = []
        for i, data in enumerate(streamers_data):
            streamer = MockStreamer(
                user_id=f"mock_user_{i+1}",
                user_name=data["user_name"],
                user_login=data["user_login"],
                platform=data["platform"],
                follower_count=data["follower_count"],
                description=data["description"],
                profile_image_url=f"https://example.com/avatars/{data['user_login']}.jpg",
                is_partner=data.get("is_partner", False),
                language=data.get("language", "zh"),
                country=data.get("country", "CN")
            )
            streamers.append(streamer)
        
        return streamers
    
    def _create_games(self) -> List[MockGame]:
        """创建模拟游戏数据"""
        games_data = [
            {"name": "英雄联盟", "category": "MOBA", "rank": 1, "viewers": 450000},
            {"name": "王者荣耀", "category": "MOBA", "rank": 2, "viewers": 380000},
            {"name": "绝地求生", "category": "射击", "rank": 3, "viewers": 220000},
            {"name": "Valorant", "category": "射击", "rank": 4, "viewers": 180000},
            {"name": "原神", "category": "RPG", "rank": 5, "viewers": 160000},
            {"name": "Dota 2", "category": "MOBA", "rank": 6, "viewers": 140000},
            {"name": "CS:GO", "category": "射击", "rank": 7, "viewers": 120000},
            {"name": "Fortnite", "category": "射击", "rank": 8, "viewers": 100000},
            {"name": "Apex Legends", "category": "射击", "rank": 9, "viewers": 85000},
            {"name": "炉石传说", "category": "卡牌", "rank": 10, "viewers": 70000}
        ]
        
        games = []
        for i, data in enumerate(games_data):
            game = MockGame(
                game_id=f"game_{i+1}",
                name=data["name"],
                category=data["category"],
                popularity_rank=data["rank"],
                total_viewers=data["viewers"],
                box_art_url=f"https://example.com/games/{data['name']}.jpg"
            )
            games.append(game)
        
        return games
    
    def _create_stream_titles(self) -> Dict[str, List[str]]:
        """创建直播标题模板"""
        return {
            "英雄联盟": [
                "冲击王者！今天必须上分",
                "新版本体验，这个英雄太强了",
                "教学局：如何在低分段carry",
                "深夜Rank，陪你到天亮",
                "世界赛版本分析",
                "单排冲分，目标大师",
                "新英雄首发体验",
                "经典回顾：S赛精彩时刻"
            ],
            "王者荣耀": [
                "巅峰赛冲分中",
                "新赛季上分攻略",
                "教你玩转新英雄",
                "五排开黑，来人！",
                "KPL战术解析",
                "排位必胜套路",
                "新皮肤展示"
            ],
            "绝地求生": [
                "今天吃鸡目标10把",
                "新地图探索",
                "四排开黑，缺人速来",
                "钢枪教学，刚枪技巧",
                "载具玩法大全",
                "决赛圈战术分析"
            ],
            "Valorant": [
                "冲击不朽段位",
                "新特工体验",
                "枪法练习专场",
                "战术配合教学",
                "地图攻略详解",
                "职业比赛复盘"
            ],
            "原神": [
                "新角色抽卡直播",
                "深渊12层满星挑战",
                "世界探索100%",
                "圣遗物刷取攻略",
                "剧情任务通关",
                "角色培养指南"
            ]
        }
    
    def get_random_streamer(self) -> MockStreamer:
        """获取随机主播"""
        return random.choice(self.streamers)
    
    def get_random_game(self) -> MockGame:
        """获取随机游戏"""
        return random.choice(self.games)
    
    def get_random_title(self, game_name: str) -> str:
        """获取随机直播标题"""
        titles = self.stream_titles.get(game_name, ["精彩直播中", "欢迎来到直播间"])
        return random.choice(titles)
    
    def simulate_viewer_count(self, streamer: MockStreamer, base_viewers: int) -> int:
        """模拟观众数波动"""
        # 基于主播粉丝数和时间的观众数模拟
        follower_factor = min(streamer.follower_count / 1000000, 10)  # 粉丝数影响因子
        
        # 时间因素（晚上观众更多）
        current_hour = datetime.now().hour
        if 19 <= current_hour <= 23:  # 黄金时段
            time_factor = 1.5
        elif 14 <= current_hour <= 18:  # 下午
            time_factor = 1.2
        else:  # 其他时间
            time_factor = 0.8
        
        # 随机波动
        fluctuation = random.uniform(0.7, 1.3)
        
        # 计算最终观众数
        final_viewers = int(base_viewers * follower_factor * time_factor * fluctuation)
        
        # 记录波动历史
        key = f"{streamer.user_login}_{datetime.now().strftime('%H')}"
        if key not in self.viewer_fluctuation:
            self.viewer_fluctuation[key] = []
        self.viewer_fluctuation[key].append(final_viewers)
        
        return max(final_viewers, 100)  # 最少100观众
    
    def generate_live_streams(self, count: int = 10, 
                            specific_streamers: List[str] = None,
                            specific_games: List[str] = None) -> List[Dict[str, Any]]:
        """生成直播流数据"""
        streams = []
        
        # 如果指定了特定主播，优先生成他们的数据
        if specific_streamers:
            for streamer_login in specific_streamers:
                streamer = next((s for s in self.streamers if s.user_login == streamer_login), None)
                if streamer:
                    game = self.get_random_game()
                    if specific_games:
                        game_obj = next((g for g in self.games if g.name in specific_games), game)
                        game = game_obj if game_obj else game
                    
                    stream = self._create_stream_data(streamer, game)
                    streams.append(stream)
        
        # 生成剩余的随机直播流
        remaining_count = max(0, count - len(streams))
        for _ in range(remaining_count):
            streamer = self.get_random_streamer()
            
            # 避免重复
            if any(s["user_login"] == streamer.user_login for s in streams):
                continue
            
            game = self.get_random_game()
            if specific_games:
                game_obj = next((g for g in self.games if g.name in specific_games), game)
                game = game_obj if game_obj else game
            
            stream = self._create_stream_data(streamer, game)
            streams.append(stream)
        
        # 按观众数排序
        streams.sort(key=lambda x: x["viewer_count"], reverse=True)
        
        return streams[:count]
    
    def _create_stream_data(self, streamer: MockStreamer, game: MockGame) -> Dict[str, Any]:
        """创建单个直播流数据"""
        base_viewers = random.randint(1000, 50000)
        viewer_count = self.simulate_viewer_count(streamer, base_viewers)
        
        # 生成开播时间（1-8小时前）
        hours_ago = random.randint(1, 8)
        started_at = datetime.now() - timedelta(hours=hours_ago)
        
        return {
            "user_id": streamer.user_id,
            "user_name": streamer.user_name,
            "user_login": streamer.user_login,
            "title": self.get_random_title(game.name),
            "game_name": game.name,
            "game_id": game.game_id,
            "viewer_count": viewer_count,
            "is_live": True,
            "platform": streamer.platform,
            "live_url": f"https://{streamer.platform.lower()}.com/{streamer.user_login}",
            "thumbnail_url": f"https://example.com/thumbnails/{streamer.user_login}_{game.game_id}.jpg",
            "language": streamer.language,
            "started_at": started_at.isoformat(),
            "tags": self._generate_tags(game.name, streamer.language),
            "is_mature": False,
            "follower_count": streamer.follower_count,
            "is_partner": streamer.is_partner
        }
    
    def _generate_tags(self, game_name: str, language: str) -> List[str]:
        """生成直播标签"""
        base_tags = [game_name]
        
        if language == "zh":
            base_tags.extend(["中文", "Chinese"])
        elif language == "ko":
            base_tags.extend(["한국어", "Korean"])
        elif language == "en":
            base_tags.extend(["English"])
        
        # 根据游戏添加特定标签
        game_tags = {
            "英雄联盟": ["LOL", "MOBA", "Ranked", "教学"],
            "王者荣耀": ["KOG", "MOBA", "巅峰赛"],
            "绝地求生": ["PUBG", "吃鸡", "射击"],
            "Valorant": ["FPS", "战术射击"],
            "原神": ["Genshin", "RPG", "二次元"]
        }
        
        if game_name in game_tags:
            base_tags.extend(random.sample(game_tags[game_name], 2))
        
        return base_tags
    
    def generate_trending_topics(self) -> List[Dict[str, Any]]:
        """生成热门话题"""
        topics = [
            {
                "topic": "S14世界赛决赛",
                "category": "电竞赛事",
                "mentions": 45000,
                "trend_score": 95,
                "related_games": ["英雄联盟"]
            },
            {
                "topic": "新英雄上线",
                "category": "游戏更新",
                "mentions": 28000,
                "trend_score": 87,
                "related_games": ["英雄联盟", "王者荣耀"]
            },
            {
                "topic": "主播转会传闻",
                "category": "电竞八卦",
                "mentions": 15000,
                "trend_score": 72,
                "related_games": []
            },
            {
                "topic": "新版本平衡性调整",
                "category": "游戏平衡",
                "mentions": 12000,
                "trend_score": 68,
                "related_games": ["英雄联盟", "Valorant"]
            }
        ]
        
        return topics
    
    def get_streamer_by_login(self, login: str) -> Optional[MockStreamer]:
        """根据登录名获取主播信息"""
        return next((s for s in self.streamers if s.user_login == login), None)
    
    def export_data(self, filename: str = "mock_data.json"):
        """导出模拟数据到文件"""
        data = {
            "streamers": [asdict(s) for s in self.streamers],
            "games": [asdict(g) for g in self.games],
            "stream_titles": self.stream_titles,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"模拟数据已导出到: {filename}")

# 全局实例
mock_generator = MockDataGenerator()

# 测试代码
def test_mock_data():
    """测试模拟数据生成"""
    print("=== 模拟数据生成器测试 ===\n")
    
    # 测试生成直播流
    print("1. 生成随机直播流:")
    streams = mock_generator.generate_live_streams(5)
    for stream in streams:
        print(f"   {stream['user_name']}: {stream['title']}")
        print(f"   游戏: {stream['game_name']}, 观众: {stream['viewer_count']:,}")
        print(f"   平台: {stream['platform']}, 语言: {stream['language']}\n")
    
    # 测试指定主播
    print("2. 生成指定主播直播:")
    specific_streams = mock_generator.generate_live_streams(
        count=3, 
        specific_streamers=["uzi", "faker", "dasima"]
    )
    for stream in specific_streams:
        print(f"   {stream['user_name']}: {stream['viewer_count']:,} 观众")
    
    # 测试热门话题
    print("\n3. 热门话题:")
    topics = mock_generator.generate_trending_topics()
    for topic in topics[:3]:
        print(f"   {topic['topic']}: {topic['mentions']:,} 提及")
    
    # 测试主播查询
    print("\n4. 主播信息查询:")
    streamer = mock_generator.get_streamer_by_login("uzi")
    if streamer:
        print(f"   {streamer.user_name}: {streamer.follower_count:,} 粉丝")
        print(f"   描述: {streamer.description}")

if __name__ == "__main__":
    test_mock_data()