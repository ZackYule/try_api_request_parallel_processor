import aiohttp
import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class ManagedSession:
    session: aiohttp.ClientSession = field(
        default_factory=aiohttp.ClientSession)
    last_used: float = field(default_factory=time.time)
    is_available: bool = True

    async def close(self):
        await self.session.close()
        self.is_available = False


@dataclass
class SessionManager:
    session_configs: list
    sessions: list = field(init=False)
    session_timeout: int = 300  # 会话超时时间（秒）

    def __post_init__(self):
        self.sessions = [ManagedSession() for _ in self.session_configs]

    def get_next_session(self):
        """获取下一个可用的会话实例。如果没有可用的会话，则创建新的会话。"""
        for managed_session in self.sessions:
            if managed_session.is_available:
                managed_session.last_used = time.time()
                return managed_session.session

        # 如果没有可用的会话，创建新的会话
        new_session = ManagedSession()
        self.sessions.append(new_session)
        return new_session.session

    async def close_inactive_sessions(self):
        """关闭长时间不用的会话。"""
        current_time = time.time()
        for managed_session in self.sessions:
            if managed_session.is_available and current_time - managed_session.last_used > self.session_timeout:
                await managed_session.close()

    async def close_all_sessions(self):
        """关闭所有会话。"""
        for managed_session in self.sessions:
            await managed_session.close()


# 使用示例
async def main():
    # 创建会话管理器
    manager = SessionManager(session_configs=[{}])

    # 获取并使用会话
    session = manager.get_next_session()
    # 使用 session 发起请求...
    # ...

    # 定期关闭长时间不用的会话
    await manager.close_inactive_sessions()

    # 最后，关闭所有会话
    await manager.close_all_sessions()


asyncio.run(main())
