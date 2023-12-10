from dataclasses import dataclass, field
import itertools
import aiohttp


@dataclass
class SessionManager:
    session_configs: list
    sessions: list = field(init=False)
    session_iterator: itertools.cycle = field(init=False)

    def __post_init__(self):
        self.sessions = [
            aiohttp.ClientSession(**config) for config in self.session_configs
        ]
        self.session_iterator = itertools.cycle(self.sessions)

    def get_next_session(self):
        """获取下一个会话实例。"""
        return next(self.session_iterator)

    async def close_all_sessions(self):
        """关闭所有会话。"""
        for session in self.sessions:
            await session.close()


@dataclass
class OpenAIClientManager:
    api_key: str
    url: str = "https://api.openai.com/v1/chat/completions"
    proxy: str = "http://127.0.0.1:7890"
    headers: dict = field(default_factory=dict)

    def __post_init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }


class APIClientStorage:

    def __init__(self, api_keys):
        self.clients = [OpenAIClientManager(api_key=key) for key in api_keys]
        self.client_iterator = itertools.cycle(self.clients)

    def get_next_api_client(self):
        """
        返回下一个 API 客户端。
        """
        return next(self.client_iterator)


def main():
    # 假设这些是你的 ChatGPT API 密钥
    with open('api keys.txt', 'r') as file:
        api_keys = file.read().splitlines()
    session_configs = [{
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    } for api_key in api_keys]

    session_manager = SessionManager(session_configs)
    session = session_manager.get_next_session()
    print(session)
    ###
    api_storage = APIClientStorage(api_keys)

    # 示例：使用一个客户端发送请求
    client = api_storage.get_next_api_client()
    print(client)


# 调用 main 函数
if __name__ == "__main__":
    main()
