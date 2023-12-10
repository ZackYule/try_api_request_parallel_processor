from openai import OpenAI
import itertools
import time
from dataclasses import (
    dataclass,
    field,
)

# 假设这些是你的 ChatGPT API 密钥
with open('api keys.txt', 'r') as file:
    api_keys = file.read().splitlines()

clients = [OpenAI(api_key=key) for key in api_keys]

# 创建一个迭代器，用于轮询密钥
client_iterator = itertools.cycle(clients)


def get_next_client():
    """
    返回下一个 API 密钥。
    """
    return next(client_iterator)


@dataclass
class OpenAIBot(OpenAI):

    def __init__(self, api_key):
        super.__init__(api_key)
