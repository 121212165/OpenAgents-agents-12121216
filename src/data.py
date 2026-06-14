"""Data layer - mock streamer data and live status functions."""
import random
from datetime import datetime, timedelta
from typing import Optional

STREAMERS = [
    {"name": "Uzi", "login": "uzi", "platform": "虎牙", "game": "英雄联盟", "followers": 8500000, "desc": "前RNG ADC选手"},
    {"name": "Faker", "login": "faker", "platform": "Twitch", "game": "英雄联盟", "followers": 3200000, "desc": "T1中单，三冠王"},
    {"name": "TheShy", "login": "theshy", "platform": "虎牙", "game": "英雄联盟", "followers": 2800000, "desc": "前IG上单选手"},
    {"name": "Rookie", "login": "rookie", "platform": "虎牙", "game": "英雄联盟", "followers": 2100000, "desc": "前IG中单选手"},
    {"name": "大司马", "login": "dasima", "platform": "虎牙", "game": "英雄联盟", "followers": 4500000, "desc": "金牌讲师"},
    {"name": "PDD", "login": "pdd", "platform": "虎牙", "game": "英雄联盟", "followers": 6200000, "desc": "前IG上单，知名主播"},
    {"name": "小团团", "login": "xiaotuan", "platform": "虎牙", "game": "绝地求生", "followers": 3800000, "desc": "知名女主播"},
    {"name": "Doublelift", "login": "doublelift", "platform": "Twitch", "game": "英雄联盟", "followers": 1800000, "desc": "前TSM ADC"},
    {"name": "Shroud", "login": "shroud", "platform": "Twitch", "game": "Valorant", "followers": 9200000, "desc": "前CS:GO职业选手"},
    {"name": "Ninja", "login": "ninja", "platform": "Twitch", "game": "Fortnite", "followers": 18500000, "desc": "知名Fortnite主播"},
]

TITLES = {
    "英雄联盟": ["冲击王者！", "新版本体验", "教学局", "深夜Rank", "单排冲分"],
    "王者荣耀": ["巅峰赛冲分", "新赛季上分攻略", "五排开黑"],
    "绝地求生": ["今天吃鸡目标10把", "四排开黑", "钢枪教学"],
    "Valorant": ["冲击不朽段位", "新特工体验", "枪法练习"],
    "Fortnite": ["大逃杀冲分", "新赛季体验", "建造练习"],
}


def _make_stream(s: dict) -> dict:
    """Build a mock live-stream dict for one streamer."""
    base = random.randint(1000, 50000)
    factor = min(s["followers"] / 1_000_000, 10)
    hour = datetime.now().hour
    tf = 1.5 if 19 <= hour <= 23 else (1.2 if 14 <= hour <= 18 else 0.8)
    viewers = max(int(base * factor * tf * random.uniform(0.7, 1.3)), 100)
    titles = TITLES.get(s["game"], ["精彩直播中"])
    return {
        "user_name": s["name"],
        "user_login": s["login"],
        "platform": s["platform"],
        "game_name": s["game"],
        "viewer_count": viewers,
        "title": random.choice(titles),
        "live_url": f"https://{s['platform'].lower()}.com/{s['login']}",
        "is_live": True,
        "started_at": (datetime.now() - timedelta(hours=random.randint(1, 8))).isoformat(),
    }


def get_live_streams(game: Optional[str] = None, streamer: Optional[str] = None, limit: int = 10) -> list[dict]:
    """Return mock live streams, optionally filtered by game or streamer name."""
    pool = STREAMERS
    if streamer:
        pool = [s for s in pool if streamer.lower() in s["name"].lower() or streamer.lower() in s["login"].lower()]
    if game:
        pool = [s for s in pool if game.lower() in s["game"].lower()]
    if not pool:
        return []
    # ~70% chance each streamer is live
    live = [_make_stream(s) for s in pool if random.random() < 0.7]
    live.sort(key=lambda x: x["viewer_count"], reverse=True)
    return live[:limit]


def get_streamer_status(name: str) -> Optional[dict]:
    """Check if a specific streamer is live. Returns dict or None."""
    match = next((s for s in STREAMERS if name.lower() in s["name"].lower() or name.lower() in s["login"].lower()), None)
    if not match:
        return None
    if random.random() < 0.7:
        return _make_stream(match)
    return {"user_name": match["name"], "platform": match["platform"], "is_live": False}


def get_trending_topics() -> list[dict]:
    """Return mock trending topics."""
    return [
        {"topic": "S14世界赛决赛", "mentions": 45000, "category": "电竞赛事"},
        {"topic": "新英雄上线", "mentions": 28000, "category": "游戏更新"},
        {"topic": "主播转会传闻", "mentions": 15000, "category": "电竞八卦"},
        {"topic": "新版本平衡性调整", "mentions": 12000, "category": "游戏平衡"},
    ]
