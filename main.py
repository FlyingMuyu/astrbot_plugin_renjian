# main.py
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import json
import logging

@register(
    "astrbot_plugin_renjian",
    "FlyingMuyu",
    "《我在人间凑数的日子》散文随机语录",
    "v1.0",
    "https://github.com/FlyingMuyu/astrbot_plugin_renjian"
)
class RenjianQuotes(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://v.api.aa1.cn/api/api-renjian/index.php"
        self.timeout = aiohttp.ClientTimeout(total=10)
        
        # 配置独立会话
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "RenjianQuotesBot/1.0 (+https://github.com/FlyingMuyu)",
                "Accept": "application/json"
            },
            timeout=self.timeout
        )

    def _format_quote(self, text: str) -> str:
        """标准化语录格式"""
        text = text.strip()
        if not text.endswith(("》", "」", "”")):
            return f"{text} ——选自散文《我在人间凑数的日子》"
        return text

    async def _safe_fetch(self):
        """安全获取数据方法"""
        try:
            async with self.session.get(
                self.api_url, 
                params={"type": "json"},
                raise_for_status=True
            ) as resp:
                # 原始文本获取
                raw_data = await resp.text(encoding='utf-8')
                
                # 尝试解析JSON
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败 | 错误位置：{e.lineno}:{e.colno} | 原始数据：{raw_data[:200]}")
                    return None
                
                # 验证数据结构
                if not isinstance(data, dict) or 'renjian' not in data:
                    logger.error(f"数据结构异常 | 数据：{data}")
                    return None
                
                return self._format_quote(data['renjian'])
                
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP错误 | 状态码：{e.status} 原因：{e.message}")
        except aiohttp.ClientError as e:
            logger.error(f"网络错误 | 类型：{type(e).__name__} 信息：{str(e)}")
        except Exception as e:
            logger.error(f"未知错误 | 类型：{type(e).__name__}", exc_info=True)
        return None

    @filter.command("renjian")
    async def command_handler(self, event: AstrMessageEvent):
        """命令处理入口"""
        quote = await self._safe_fetch()
        response = quote or "🌸 语录获取失败，可能服务器在思考人生哲理..."
        yield event.plain_result(response)

    async def terminate(self):
        """清理资源"""
        await self.session.close()
        logger.info("插件资源已清理")

if __name__ == "__main__":
    # 本地测试模式
    import asyncio
    
    class MockEvent:
        def plain_result(self, text):
            print(f"[测试输出] {text}")

    async def test():
        ctx = Context(config={})
        plugin = RenjianQuotes(ctx)
        await plugin.command_handler(MockEvent())
        await plugin.terminate()
    
    # 配置测试日志
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    asyncio.run(test())