# 虎牙直播 API 客户端（简化版 - 只检测开播状态）
import asyncio
import aiohttp
from typing import Dict, Any
from loguru import logger
from datetime import datetime


class HuyaClient:
    """
    虎牙直播客户端（简化版）

    功能：只检测主播是否开播
    无需 API Key，使用简单的 HTTP 请求
    """

    def __init__(self):
        self.base_url = "https://www.huya.com"
        self.session = None

    async def __aenter__(self):
        """进入上下文"""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.session:
            await self.session.close()

    async def check_live_status(self, room_id: str) -> Dict[str, Any]:
        """
        检查直播间是否开播

        Args:
            room_id: 虎牙房间号

        Returns:
            {
                "is_live": bool,        # 是否在直播
                "room_id": str,
                "checked_at": str
            }
        """
        try:
            url = f"{self.base_url}/{room_id}"

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"请求失败: {response.status}")
                    return self._make_status(room_id, is_live=False)

                html = await response.text()

            # 简单检测：查找直播状态相关的关键词
            # 注意：这是简化版，实际需要根据页面结构调整
            is_live = self._detect_live_status(html)

            return {
                "is_live": is_live,
                "room_id": room_id,
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"检查直播状态失败: {e}")
            return self._make_status(room_id, is_live=False)

    def _detect_live_status(self, html: str) -> bool:
        """
        检测直播状态（简化版）

        方法：查找页面中的关键标识
        注意：实际部署时需要根据虎牙页面结构调整
        """
        # 虎牙直播页面通常包含以下标识：
        # 1. "直播中" 文本
        # 2. 特定的 class 名称
        # 3. JSON 数据中的状态字段

        # 简化版：查找常见的关键词
        live_indicators = [
            "直播中",
            "liveStatus",
            "isLive"
        ]

        for indicator in live_indicators:
            if indicator in html:
                # 进一步检查是否真的在直播
                # 避免误判（页面可能有这些文字但未开播）
                if self._verify_live_status(html):
                    return True

        return False

    def _verify_live_status(self, html: str) -> bool:
        """
        验证直播状态

        避免"直播中"等文字出现在页面上但实际未开播的情况
        """
        # 方法：检查是否有观众数
        # 如果有观众数，说明在直播
        import re

        # 查找观众数模式（如：人气 100万）
        patterns = [
            r'人气.*?(\d+)',
            r'viewer.*?(\d+)',
            r'totalCount.*?(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                viewer_count = int(match.group(1))
                # 如果观众数 > 0，说明在直播
                if viewer_count > 0:
                    return True

        return False

    def _make_status(self, room_id: str, is_live: bool = False) -> Dict[str, Any]:
        """创建状态返回"""
        return {
            "is_live": is_live,
            "room_id": room_id,
            "checked_at": datetime.now().isoformat()
        }


# 测试代码
async def test_huya_client():
    """测试虎牙客户端"""
    print("测试虎牙直播状态检测...\n")

    async with HuyaClient() as client:
        # 测试房间号（需要替换为真实的）
        test_rooms = [
            ("995888", "Uzi"),
            ("5666913", "大司马")
        ]

        for room_id, name in test_rooms:
            print(f"检查 {name} (房间号: {room_id})...")
            result = await client.check_live_status(room_id)

            status = "🔴 直播中" if result['is_live'] else "⚫ 未开播"
            print(f"状态: {status}")
            print(f"检查时间: {result['checked_at']}\n")


if __name__ == "__main__":
    asyncio.run(test_huya_client())
