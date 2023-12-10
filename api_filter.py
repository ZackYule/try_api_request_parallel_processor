# This code is for v1 of the openai package: pypi.org/project/openai
from openai import OpenAI
import logging
from logger_config import setup_logging

logger = logging.getLogger(__name__)

client = OpenAI()
import time
import openai

# 设置你的 OpenAI API 密钥
openai.api_key = ''


def send_openai_request():
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
        print(f"Error: {e}")


# 每分钟发送四次请求

with open('api keys.txt', 'r') as file:
    api_keys = file.read().splitlines()

new_keys = []
for i, key in enumerate(api_keys):
    openai.api_key = key
    print(f'第{i+1}次尝试，key是: {key}')
    response = send_openai_request()
    if response is None or "error" in response:
        print(f'第{i+1}次尝试失败')
        time.sleep(5)
        continue
    # response2 = send_openai_request()
    # if response2 is None or "error" in response2:
    #     print(f'第{i+1}次尝试失败')
    #     time.sleep(5)
    #     continue
    new_keys.append(key)
    time.sleep(5)

# 打开文件并写入
with open('new api keys.txt', 'w') as file:
    for key in new_keys:
        file.write(key + '\n')
