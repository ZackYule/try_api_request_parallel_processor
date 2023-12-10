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


@dataclass
class APIRequest:
    request_json: dict
    task_id: str = '1'
    attempts_left: int = 3
    result: list = field(default_factory=list)
    delay: int = 3

    async def call_openai_api(
        self,
        api_key,
    ):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        proxy = "http://127.0.0.1:7890"
        """Calls the OpenAI API and saves results."""
        logging.info(f"Starting request #{self.task_id}")
        error = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url=url,
                        headers=headers,
                        proxy=proxy,
                        json=self.request_json,
                ) as response:
                    response = await response.json()
                if "error" in response:

                    error = response
                    if "Rate limit" in response["error"].get("message", ""):
                        logging.warning(
                            f"Request {self.task_id} failed with Rate limit error {response['error']}"
                        )
                    else:
                        logging.warning(
                            f"Request {self.task_id} failed with error {response['error']}"
                        )

        except (
                Exception
        ) as e:  # catching naked exceptions is bad practice, but in this case we'll log & save them
            logging.warning(
                f"Request {self.task_id} failed with Exception {e}")
            error = e

        if error:
            self.result.append(error)
            if self.attempts_left:
                time.sleep(self.delay)
                # 在这里重新进行访问
                print('xxx')
        else:
            return response


async def main():
    api_key = "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"
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

    client = APIRequest(request_json=data)
    responses = []
    for i in range(4):
        response = await client.call_openai_api(api_key=api_key, )
        responses.append(response)
    print(responses)


if __name__ == "__main__":

    asyncio.run(main())
