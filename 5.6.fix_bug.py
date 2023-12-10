import asyncio
import aiohttp
import time
import random
import uuid
from dataclasses import (
    dataclass,
    field,
)
import logging
from logger_config import setup_logging

logger = logging.getLogger(__name__)


@dataclass
class IterCycle:
    items: list = field(default_factory=list)
    index: int = 0

    def add(self, item):
        self.items.append(item)

    def remove(self, item):
        if item in self.items:
            item_index = self.items.index(item)
            self.items.remove(item)
            # 如果移除的元素在当前索引之前或者是当前索引，需要调整索引
            if item_index <= self.index:
                self.index -= 1
            # 检查列表是否为空，以避免 ZeroDivisionError
            if len(self.items) == 0:
                self.index = 0
            else:
                self.index %= len(self.items)

    def count_items(self):
        return len(self.items)

    def __iter__(self):
        return self

    def __next__(self):
        if not self.items:
            raise StopIteration
        item = self.items[self.index]
        self.index = (self.index + 1) % len(self.items)
        return item


@dataclass
class ManagedSession:
    config: dict
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    _session: aiohttp.ClientSession = None
    bucket_capacity: int = 1
    refill_rate: float = 1 / 20
    tokens: float = 3
    last_used: float = field(default_factory=time.time)

    def refill_tokens(self):
        now = time.time()
        elapsed = now - self.last_used
        self.tokens = min(self.bucket_capacity,
                          self.tokens + elapsed * self.refill_rate)
        logger.debug(
            f'managed_session:{self.id} Refill tokens to >> {self.tokens:.2f}')

    def can_be_used(self):
        self.refill_tokens()
        if self.tokens >= 1:
            self.tokens -= 1
            logger.debug(
                f'managed_session:{self.id} 被调用 tokens to >> {self.tokens:.2f}'
            )
            return True
        else:
            logger.debug(
                f'managed_session:{self.id} 调用失败 tokens to >> {self.tokens:.2f}'
            )
            return False

    @property
    async def session(self):
        if self.can_be_used():
            logger.debug(f'调用session成功，并返回，session_id:{self.id}')
            now = time.time()
            self.last_used = now
            if self._session is None or self._session.closed:
                self._session = self.create_session_from_config()
            return self._session
        else:
            return None

    def create_session_from_config(self):
        # 在这里解析 config 字典，并提取相关配置
        # 示例: 提取代理和超时设置
        timeout = aiohttp.ClientTimeout(connect=self.config.get('timeout', 30))
        headers = self.config.get('headers')

        # 创建并返回 aiohttp.ClientSession 实例
        session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return session

    async def close(self):
        if self._session is not None and not self._session.closed:
            logger.info(f'session #{self.id} 正在关闭')
            await self._session.close()
        else:
            logger.info(f'session #{self.id} 已经关闭或不存在，无需关闭')


@dataclass
class SessionManager:
    session_configs: list
    waiting_sessions: list = field(default_factory=list)
    used_sessions: IterCycle = field(init=False)
    session_timeout: int = 300  # 会话超时时间（秒）

    def __post_init__(self):
        if len(self.session_configs) == 0:
            logger.error(
                'The session configs passed in SessionManager are empty, which is not allowed.'
            )
            raise ValueError('Session configs must not be empty.')
        random.shuffle(self.session_configs)
        self.waiting_sessions = [
            ManagedSession(config) for config in self.session_configs
        ]
        self.used_sessions = IterCycle([self.waiting_sessions.pop()])

    async def get_next_session(self):
        # 首先检查可用会话列表
        for _ in range(self.used_sessions.count_items()):
            logger.debug('在used_sessions表中寻找可用session')
            managed_session = next(self.used_sessions)
            session = await managed_session.session
            if session is not None:
                logger.debug(
                    f'在used_sessions表中找到可用session:{managed_session.id}')
                return session

        logger.info('used_sessions表中无可用会话，从waiting_sessions中寻找')
        # 然后检查等待列表
        for managed_session in self.waiting_sessions:
            logger.debug('寻找waiting_sessions中可用的session')
            session = await managed_session.session
            if session is not None:
                # 将可用的会话移到可用列表
                logger.debug(f'找到可用的session，#{managed_session.id}')
                logger.debug(f'session的config为{managed_session.config}')
                logger.debug(f'session的请求头为{session.headers}')
                self.waiting_sessions.remove(managed_session)
                self.used_sessions.add(managed_session)
                return session

        # 所有会话都不可用，返回None
        logger.warning(
            'All keys are in use, please wait a moment before making another call.'
        )
        return

    async def close_inactive_sessions(self):
        """关闭长时间不用的会话。"""
        current_time = time.time()
        for _ in range(self.used_sessions.count_items()):
            managed_session = next(self.used_sessions)
            if current_time - managed_session.last_used > self.session_timeout:
                await managed_session.close()
                self.used_sessions.remove(managed_session)
                self.waiting_sessions.append(managed_session)

    async def close_all_sessions(self):
        # 关闭所有会话
        for _ in range(self.used_sessions.count_items()):
            managed_session = next(self.used_sessions)
            await managed_session.close()
            self.used_sessions.remove(managed_session)
            self.waiting_sessions.append(managed_session)


# 使用示例
async def main():
    with open('api keys.txt', 'r') as file:
        api_keys = file.read().splitlines()

    session_configs = [{
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    } for api_key in api_keys]
    # 创建会话管理器
    manager = SessionManager(session_configs)

    count_succeed = 0
    count_filed = 0
    # 获取并使用会话
    for _ in range(2):  # 尝试多次获取会话
        print(f"开始第{_+1}个")
        session = await manager.get_next_session()
        responses = []
        if session:
            logger.debug(f'session的请求头是：f{session.headers}')
            content = "Translate the following English text to French: 'Hello, how are you?'"
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
            url = "https://api.openai.com/v1/chat/completions"
            proxy = "http://127.0.0.1:7890"
            async with session.post(
                    url=url,
                    proxy=proxy,
                    json=data,
            ) as response:
                response = await response.json()
                logger.info(response)
            responses.append(response)
            # 使用 session 发起请求...
            count_succeed += 1
            logger.debug(f"使用会话进行请求，成功{count_succeed}次")
            logger.debug("session")
        else:
            count_filed += 1
            logger.debug(f"没有可用会话，失败{count_filed}次")
            time.sleep(11)  # 等待一些时间再试
    logger.info(responses)
    # 最后，关闭所有会话
    await manager.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(main())
