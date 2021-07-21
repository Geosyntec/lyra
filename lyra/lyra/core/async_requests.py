from typing import Any, Dict

import aiohttp
import orjson


async def send_request(url: str, payload: Dict, delay: float = None) -> Dict[str, Any]:
    async with aiohttp.ClientSession(
        json_serialize=lambda x: orjson.dumps(x).decode()
    ) as session:
        async with session.post(url, json=payload) as response:
            result: Dict[str, Any] = await response.json(
                loads=orjson.loads, content_type=None
            )
    return result
