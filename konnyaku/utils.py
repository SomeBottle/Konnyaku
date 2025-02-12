"""
一些工具方法
"""

from konnyaku.errors import (
    RateLimitException,
    TRLimitException,
    Unknown429Exception,
    APIError,
)
from konnyaku.bangumi import BangumiAPI
from time import sleep

TPM_RPM_LIMIT_KEYWORDS = ["TPM", "RPM", "TOKENS PER MINUTE", "REQUESTS PER MINUTE"]
RATE_LIMIT_KEYWORDS = ["ERROR", "EXCEED"]


def limit_exception_raiser(e: Exception | str, is_429=False) -> None:
    """
    抛出指定的异常。根据异常字符串来判断是 TPM/RPM 限制还是并发限制，这两种都有可能返回 429

    :param e: 异常对象或字符串
    :param is_429: 是否已经确认肯定是 429 异常。
    :raises RateLimitException: 超出 API 的速率限制
    :raises TRLimitException: 超出 API 的 TPM/RPM 限制
    :raises Unknown429Exception: 未知 429 异常
    :raises e: 其他异常
    """
    if isinstance(e, Exception):
        e = str(e)

    for keyword in TPM_RPM_LIMIT_KEYWORDS:
        if keyword in e.upper():
            raise TRLimitException(e)

    for keyword in RATE_LIMIT_KEYWORDS:
        if keyword in e.upper():
            raise RateLimitException(e)

    # 如果是 429 异常，但是没有找到关键字，那么就抛出 Unknown429Exception
    if is_429:
        raise Unknown429Exception(e)

    raise APIError(e)


def extract_bangumi_info(subject_id: str) -> str:
    """
    从 Bangumi API 中提取番剧信息，给 LLM 提供背景信息

    :param subject_id: 番剧 ID
    :return: 番剧信息字串
    """
    api = BangumiAPI()
    subject_info = api.get_subject_info(subject_id)
    character_infos = api.get_subject_all_character_infos(subject_id)
    result = ""

    # 基本信息
    if "name" in subject_info:
        chs_name = subject_info["name_cn"] if "name_cn" in subject_info else ""
        result += f"<名字>《{subject_info['name']}》({chs_name})</名字>\n"
    if "platform" in subject_info:
        result += f"<平台>{subject_info['platform']}</平台>\n"
    if "summary" in subject_info:
        result += f"<简介>\n{subject_info['summary']}\n</简介>\n"

    result += "\n"

    # 角色信息
    if len(character_infos) > 0:
        result += "<角色信息>\n| 名字 | 担当 | 性别 |\n| --- | --- | --- | --- |\n"
        for character in character_infos:
            result += f"| {character['name']} | {character['relation']} | {character['gender']} |\n"
        result += "</角色信息>\n"

        # 角色术语表
        result += "\n<角色术语表>\n"
        for character in character_infos:
            if character["name_chs"]:
                result += f"{character['name']} -> {character['name_chs']}\n"
        result += "</角色术语表>\n"

    return result


class RetrySleeper:
    """
    重试等待类（先指数退避后线性）
    """

    def __init__(
        self,
        max_retry_times: int = 2,
        max_wait_before_retry: int = 10,
        start_wait_time: int = 1,
    ):
        """
        初始化

        :param max_retry_times: 最大重试次数
        :param max_wait_before_retry: 重试前的最大等待时间（秒）
        """
        self.max_retry_times = max_retry_times
        self.max_wait_before_retry = max_wait_before_retry
        self.linear_wait = False  # 是否启动线性退避
        self.retry_times = 0
        self.next_wait_time = start_wait_time

    def reset(self):
        """
        重置重试次数和退避情况
        """
        self.retry_times = 0
        self.next_wait_time = 1
        self.linear_wait = False

    def sleep(self) -> bool:
        """
        等待

        :return: 是否可以重试
        """

        if self.retry_times >= self.max_retry_times:
            return False

        print(f"Retrying...({self.retry_times + 1}/{self.max_retry_times})")

        wait_time = self.next_wait_time
        self.retry_times += 1
        if wait_time * 2 >= self.max_wait_before_retry / 2:
            # 超过 1/2 的最大等待时间后启动线性退避
            self.linear_wait = True
        if self.linear_wait:
            self.next_wait_time = min(wait_time + 1, self.max_wait_before_retry)
        else:
            self.next_wait_time = min(wait_time * 2, self.max_wait_before_retry)

        sleep(wait_time)

        return True
