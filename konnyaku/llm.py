"""
接入大模型
"""

from random import randint
from time import sleep
from openai import OpenAI, RateLimitError
from konnyaku.errors import APIError
from konnyaku.config import (
    MAX_RETRY_TIMES,
    RETRY_WAIT_RANGE,
)
from konnyaku.utils import limit_exception_raiser


class LLM:
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        streaming: bool = False,
        temperature: float = 1.3,
    ):
        """
        初始化模型

        :param api_key: API Key
        :param base_url: API Base URL
        :param model: 模型名称
        :param streaming: 是否使用流式 API
        :param temperature: 模型温度
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.streaming = streaming
        self.temperature = temperature

    def call(self, messages: list[dict], retry=0) -> str:
        """
        调用大模型，返回结果字串

        :param messages: 消息列表
        :return: 结果字串
        :raises RateLimitException: 超出 API 的速率限制
        :raises TRLimitException: 超出 API 的 TPM/RPM 限制
        :raises APIError: 其他 API 异常
        """
        if self.streaming:
            print("(Streaming)", end="\r", flush=True)
        else:
            print("(Non-Streaming)", end="\r", flush=True)

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        try:
            resp = client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                stream=self.streaming,
            )

            call_result = ""

            if self.streaming:
                # 流式 API
                for chunk in resp:
                    if chunk.choices and len(chunk.choices) > 0:
                        # 流式情况下最后一个 chunk 可能无内容返回，仅提示结束
                        if chunk.choices[0].delta.content:
                            chunk_content = chunk.choices[0].delta.content
                            call_result += chunk_content
                            print(chunk_content, end="", flush=True)
                    else:
                        chunk_json = chunk.to_json()
                        limit_exception_raiser(chunk_json)
                print()
                call_result = call_result.strip()
            else:
                if (
                    resp.choices
                    and len(resp.choices) > 0
                    and resp.choices[0].message.content
                ):
                    # 有结果则返回
                    call_result = resp.choices[0].message.content.strip()
                else:
                    # 有些 API 在超限时并不是以 429 返回，而是返回空结果
                    # 检查返回的 JSON 中是否有 error, exceed 等字样
                    resp_json = resp.to_json()
                    limit_exception_raiser(resp_json)

            return call_result

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
                return self.call(messages, retry + 1)
            else:
                print(
                    "Retry times exceeded, maybe you should check the API configuration."
                )
                raise e
