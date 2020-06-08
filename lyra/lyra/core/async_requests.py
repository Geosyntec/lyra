from typing import Dict

import orjson
import aiohttp


async def send_request(url: str, payload: Dict):
    async with aiohttp.ClientSession(
        json_serialize=lambda x: orjson.dumps(x).decode()
    ) as session:
        async with session.post(url, json=payload) as response:
            response = await response.json(loads=orjson.loads, content_type=None)
    return response
