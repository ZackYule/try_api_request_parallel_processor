import asyncio
import aiohttp
import time
from dataclasses import (
    dataclass,
    field,
)
import logging
from logger_config import setup_logging

logger = logging.getLogger(__name__)


async def call_openai_api(session, content, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model":
        "gpt-3.5-turbo-1106",
        "messages": [{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": content
        }],
        "max_tokens":
        200
    }
    proxy_url = "http://127.0.0.1:7890"
    # print(data)
    async with session.post(url, proxy=proxy_url, json=data,
                            headers=headers) as response:
        return await response.json()


async def main():
    api_key = "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"
    content = "Translate the following English text to French: 'Hello, how are you?'"

    async with aiohttp.ClientSession() as session:
        response = await call_openai_api(session, content, api_key)
        print(response)


if __name__ == "__main__":

    asyncio.run(main())
