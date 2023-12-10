from openai import OpenAI
import itertools
import time
from dataclasses import (
    dataclass,
    field,
)


@dataclass
class OpenAPIPool():
    url: str = "https://api.openai.com/v1/chat/completions"
    proxy: str = "http://127.0.0.1:7890"
    api_key: str = ""
    headers: dict = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


def get_next_client(client_iterator):
    """
    返回下一个 API 密钥。
    """
    return next(client_iterator)


def main():
    # 假设这些是你的 ChatGPT API 密钥
    with open('api keys.txt', 'r') as file:
        api_keys = file.read().splitlines()

    clients = [OpenAPIPool(api_key=key) for key in api_keys]

    # 创建一个迭代器，用于轮询密钥
    client_iterator = itertools.cycle(clients)
