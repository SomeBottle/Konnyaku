"""
接入大模型
"""

from random import randint
from time import sleep
from openai import OpenAI, RateLimitError, APIError
from konnyaku.errors import RateLimitException, TRLimitException
from konnyaku.config import (
    LLM_API_KEY,
    LLM_API_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_RETRY_TIMES,
    RETRY_WAIT_RANGE,
)
from konnyaku.utils import limit_exception_raiser


def call_llm(messages: list[dict], retry=0) -> str:
    """
    调用大模型，返回结果字串

    :param messages: 消息列表
    :return: 结果字串
    :raises RateLimitException: 超出 API 的速率限制
    :raises TRLimitException: 超出 API 的 TPM/RPM 限制
    :raises APIError: 其他 API 异常
    """
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE_URL)

    try:
        resp = client.chat.completions.create(
            messages=messages, model=LLM_MODEL, temperature=LLM_TEMPERATURE
        )
        if resp.choices and len(resp.choices) > 0 and resp.choices[0].message:
            # 有结果则返回
            return resp.choices[0].message.content.strip()
        else:
            # 有些 API 在超限时并不是以 429 返回，而是返回空结果
            # 检查返回的 JSON 中是否有 error, exceed 等字样
            resp_json = resp.to_json()
            limit_exception_raiser(resp_json)

    except RateLimitError as e:
        # 429 超限问题，进行退避
        limit_exception_raiser(e, is_429=True)

    except APIError as e:
        # 其他问题则触发本方法的重试
        if retry < MAX_RETRY_TIMES:
            print(
                f"Unexpected API error: {e}, retrying...({retry + 1}/{MAX_RETRY_TIMES})"
            )
            sleep(randint(*RETRY_WAIT_RANGE))
            return call_llm(messages, retry + 1)
        else:
            print("Retry times exceeded, maybe you should check the API configuration.")
            raise e
