"""YouGame Explorer - gaming stream assistant. ~120 lines."""
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
import gradio as gr

from src.config import load_env, load_players, get_host, get_port
from src.data import get_live_streams, get_streamer_status, get_trending_topics

load_env()
players_cfg = load_players()
logger.info(f"YouGame Explorer starting — {len(players_cfg.get('monitored_players', []))} streamers configured")

# ── Intent detection ──────────────────────────────────────────────────

STREAMER_NAMES = [p["name"] for p in players_cfg.get("monitored_players", [])]
ALL_STREAMERS = STREAMER_NAMES + ["Faker", "Uzi", "大司马", "TheShy", "Rookie", "PDD", "小团团",
                                   "Doublelift", "Shroud", "Ninja"]

LIVE_KEYWORDS = re.compile(r"直播|开播|在播|在线|live|streaming", re.I)
BRIEF_KEYWORDS = re.compile(r"简报|日报|汇总|总结|报告|动态|briefing", re.I)
TREND_KEYWORDS = re.compile(r"趋势|热门|排行|trend|hot", re.I)
HELLO_KEYWORDS = re.compile(r"你好|嗨|hello|hi|hey|你是|能做什么|介绍", re.I)


def detect_intent(text: str) -> tuple[str, dict]:
    """Return (intent, entities) from user text."""
    entities: dict = {}

    # Extract streamer name
    for name in ALL_STREAMERS:
        if name.lower() in text.lower():
            entities["streamer"] = name
            break

    # Extract game
    for game in ["英雄联盟", "LOL", "王者荣耀", "Valorant", "绝地求生", "原神", "Fortnite", "CS2", "Dota2"]:
        if game.lower() in text.lower():
            entities["game"] = game
            break

    if LIVE_KEYWORDS.search(text):
        return "live_query", entities
    if BRIEF_KEYWORDS.search(text):
        return "briefing", entities
    if TREND_KEYWORDS.search(text):
        return "trending", entities
    if HELLO_KEYWORDS.search(text):
        return "hello", entities
    return "unknown", entities


# ── Response builders ─────────────────────────────────────────────────

def _fmt_num(n: int) -> str:
    return f"{n / 10000:.1f}万" if n >= 10000 else f"{n / 1000:.1f}千" if n >= 1000 else str(n)


def handle_live_query(entities: dict) -> str:
    name = entities.get("streamer")
    if name:
        s = get_streamer_status(name)
        if not s:
            return f"未找到主播 **{name}**，请检查名称。"
        if s.get("is_live"):
            return (f"🔴 **{s['user_name']}** 正在 {s['platform']} 直播！\n\n"
                    f"📝 标题：{s.get('title', '无标题')}\n"
                    f"🎮 游戏：{s.get('game_name', '')}\n"
                    f"👥 观众：{_fmt_num(s.get('viewer_count', 0))}\n"
                    f"🔗 链接：{s.get('live_url', '')}")
        return f"⚫ **{s['user_name']}** 当前未在直播。"

    game = entities.get("game")
    streams = get_live_streams(game=game, limit=10)
    if not streams:
        return "当前没有找到正在直播的主播。"

    header = f"🔴 **{'热门' if not game else game}直播** — {len(streams)} 位主播在线\n\n"
    lines = []
    for i, s in enumerate(streams[:8], 1):
        lines.append(f"{i}. **{s['user_name']}** — {s['game_name']} | 👥 {_fmt_num(s['viewer_count'])} 观众\n"
                     f"   📝 {s['title']}")
    return header + "\n".join(lines)


def handle_briefing() -> str:
    now = datetime.now()
    streams = get_live_streams(limit=20)
    topics = get_trending_topics()

    parts = [f"📰 **小游探简报** — {now.strftime('%Y年%m月%d日')}\n"]

    if streams:
        total_v = sum(s["viewer_count"] for s in streams)
        parts.append(f"🔥 **直播概况**: {len(streams)} 位主播在线，总观众 {_fmt_num(total_v)}\n")
        for s in streams[:5]:
            parts.append(f"  • {s['user_name']} ({s['game_name']}) — {_fmt_num(s['viewer_count'])} 观众")
    else:
        parts.append("📺 当前暂无主播直播\n")

    if topics:
        parts.append("\n📈 **游戏圈热点**:")
        for t in topics[:3]:
            parts.append(f"  • {t['topic']} — {t['mentions']:,} 提及")

    parts.append(f"\n⏰ 生成时间: {now.strftime('%H:%M:%S')}")
    return "\n".join(parts)


def handle_trending() -> str:
    topics = get_trending_topics()
    lines = ["📈 **游戏圈热门趋势**\n"]
    for i, t in enumerate(topics, 1):
        lines.append(f"{i}. **{t['topic']}** — {t['mentions']:,} 提及 ({t['category']})")
    return "\n".join(lines)


def handle_hello() -> str:
    return ("👋 你好！我是 **小游探**，你的游戏圈 AI 助手。\n\n"
            "我可以帮你：\n"
            "• 🔴 查询主播直播状态 — 如 \"Faker在直播吗？\"\n"
            "• 📰 生成游戏圈简报 — 如 \"生成今日简报\"\n"
            "• 📈 查看热门趋势 — 如 \"热门游戏\"\n\n"
            "直接输入你的问题即可！")


def handle_query(user_input: str) -> str:
    """Main entry: detect intent → build response."""
    if not user_input.strip():
        return ""
    intent, entities = detect_intent(user_input)
    logger.info(f"Query: {user_input!r} → intent={intent}, entities={entities}")

    if intent == "live_query":
        return handle_live_query(entities)
    if intent == "briefing":
        return handle_briefing()
    if intent == "trending":
        return handle_trending()
    if intent == "hello":
        return handle_hello()

    # Unknown — if we found a streamer name, treat as live query
    if entities.get("streamer"):
        return handle_live_query(entities)
    return ("🤔 我不太理解你的问题。试试：\n"
            "• \"Faker在直播吗？\"\n"
            "• \"生成今日简报\"\n"
            "• \"热门趋势\"\n"
            "• 输入 \"帮助\" 查看更多")


# ── Gradio UI ─────────────────────────────────────────────────────────

DEMO_QUERIES = ["你好", "Faker在直播吗？", "Uzi在直播吗？", "生成今日简报", "热门趋势"]

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="小游探 - 游戏圈AI助手", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎮 小游探 — 游戏圈 AI 助手\n基于 Mock 数据的轻量级直播查询与简报生成")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="对话", height=400)
                with gr.Row():
                    msg = gr.Textbox(placeholder="例如：Faker在直播吗？", scale=4, show_label=False)
                    send_btn = gr.Button("发送", variant="primary", scale=1)
                gr.Markdown("### 💡 快捷查询")
                with gr.Row():
                    for q in DEMO_QUERIES:
                        gr.Button(q, size="sm").click(lambda q=q: q, outputs=msg)

            with gr.Column(scale=1):
                gr.Markdown("### 🤖 系统信息\n- **模式**: Mock 数据\n"
                            f"- **主播数**: {len(players_cfg.get('monitored_players', []))}\n"
                            "- **状态**: 🟢 运行中")
                gr.Markdown("### 📖 使用说明\n1. 输入主播名查询直播\n"
                            "2. 输入\"简报\"获取游戏圈动态\n3. 输入\"热门\"查看趋势")

        def respond(user_input, history):
            if not user_input.strip():
                return history, ""
            response = handle_query(user_input)
            history = history + [(user_input, response)]
            return history, ""

        send_btn.click(respond, [msg, chatbot], [chatbot, msg])
        msg.submit(respond, [msg, chatbot], [chatbot, msg])

    return demo


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    port = get_port()
    host = get_host()
    logger.info(f"Starting on {host}:{port}")
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port, share=False)  # nosec B104
