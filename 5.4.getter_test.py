from dataclasses import dataclass, field
import aiohttp
import asyncio


@dataclass
class ManagedSession:
    _session: aiohttp.ClientSession = field(default=None, init=False)

    # 其他属性...

    def can_be_used(self) -> bool:
        return False

    @property
    async def session(self) -> aiohttp.ClientSession:
        if self.can_be_used():
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            return self._session
        else:
            return None


async def main(a):
    t = await a.session
    print(t)
    return t


a = ManagedSession()

asyncio.run(main(a))
