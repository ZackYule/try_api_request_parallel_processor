import os
import time
import logging
import re
import openai
from logger_config import setup_logging

# 设置日志记录
logger = logging.getLogger(__name__)
setup_logging()


def send_openai_request(api_key, client):
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo-1106",
                                                  messages=[{
                                                      "role": "user",
                                                      "content": "hello"
                                                  }],
                                                  temperature=0,
                                                  max_tokens=1024,
                                                  top_p=1,
                                                  frequency_penalty=0,
                                                  presence_penalty=0)
        return response.model_dump_json()
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def read_api_keys(file_path):
    with open(file_path, 'r') as file:
        return file.read().splitlines()


def main():
    api_keys = read_api_keys('api keys.txt')
    new_keys = []

    for i, key in enumerate(api_keys):
        openai.api_key = key
        logger.info(f'第{i+1}次尝试，key是: {key}')

        is_get_limited = False
        client = openai.OpenAI()

        for _ in range(3):
            response = send_openai_request(key, client)
            if response is None or "error" in response:
                logger.info(f'第{i+1}次尝试失败')
                org_id = parse_org_id_from_error(response)
                new_key = f'{key}---{org_id}'
                new_keys.append(new_key)
                is_get_limited = True
                time.sleep(5)
                break
            time.sleep(5)

        if not is_get_limited:
            logger.info(f'第{i+1}次尝试全部通过，key：{key}')
            new_keys.append(f'{key}---succeed')
            time.sleep(5)

    with open('new api keys.txt', 'w') as file:
        for key in new_keys:
            file.write(f'{key}\n')


def parse_org_id_from_error(response):
    if response and 'Rate limit' in response:
        pattern = r"org-([A-Za-z0-9]+)"
        match = re.search(pattern, response)
        return match.group(1) if match else "No match found"
    return 'other'


if __name__ == "__main__":
    main()
