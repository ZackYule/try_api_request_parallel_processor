import asyncio
import aiohttp
import time
import uuid
from dataclasses import (
    dataclass,
    field,
)
import logging
from logger_config import setup_logging

logger = logging.getLogger(__name__)


@dataclass
class StatusTracker:
    """Stores metadata about the script's progress. Only one instance is created."""

    num_tasks_started: int = 0
    num_tasks_in_progress: int = 0  # script ends when this reaches 0
    num_tasks_succeeded: int = 0
    num_tasks_failed: int = 0
    num_rate_limit_errors: int = 0
    num_api_errors: int = 0  # excluding rate limit errors, counted above
    num_other_errors: int = 0
    time_of_last_rate_limit_error: int = 0  # used to cool off after hitting rate limits


@dataclass
class APIRequest:
    request_json: dict
    status_tracker: StatusTracker
    result: list = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    attempts_left: int = 3
    delay: int = 3

    async def call_llm_single(
        self,
        session,
    ):
        url = "https://api.openai.com/v1/chat/completions"
        proxy = "http://127.0.0.1:7890"
        """Calls the OpenAI API and saves results."""
        logging.info(f"Starting request #{self.id}")
        error = None
        try:
            async with session.post(
                    url=url,
                    proxy=proxy,
                    json=self.request_json,
            ) as response:
                response = await response.json()
            if "error" in response:

                error = response
                response = None
                if "Rate limit" in response["error"].get("message", ""):
                    logging.warning(
                        f"Request {self.id} failed with Rate limit error {response['error']}"
                    )
                    self.status_tracker.num_rate_limit_errors += 1
                else:
                    logging.warning(
                        f"Request {self.id} failed with error {response['error']}"
                    )
                    self.status_tracker.num_api_errors += 1

        except (
                Exception
        ) as e:  # catching naked exceptions is bad practice, but in this case we'll log & save them
            logging.warning(f"Request {self.id} failed with Exception {e}")
            self.status_tracker.num_other_errors += 1
            error = e

        if error:
            self.result.append(error)
        else:
            self.status_tracker.num_tasks_in_progress -= 1
            self.status_tracker.num_tasks_succeeded += 1
            return response

    async def call_llm(self, session):
        while self.attempts_left > 0:
            logger.debug(f'发起请求#{self.id}，还有{self.attempts_left - 1}次重试机会')
            response = await self.call_llm_single(session, )
            if response:
                return response
            self.attempts_left -= 1
        logging.error(
            f"Request {self.request_json} failed after all attempts. Saving errors: {self.result}"
        )
        self.status_tracker.num_tasks_in_progress -= 1
        self.status_tracker.num_tasks_failed += 1


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
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    status_tracker = StatusTracker()
    async with aiohttp.ClientSession(headers=headers, ) as session:
        responses = []
        for i in range(4):
            request_client = APIRequest(request_json=data,
                                        status_tracker=status_tracker)
            response = await request_client.call_llm(session=session, )
            if response:
                responses.append(response)
            del request_client
            logger.info('request_client已删除')
        print(responses)
        print(status_tracker)


if __name__ == "__main__":

    asyncio.run(main())
