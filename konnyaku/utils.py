"""
一些工具方法
"""

from konnyaku.errors import RateLimitException, TRLimitException
from openai import APIError

TPM_RPM_LIMIT_KEYWORDS = ["TPM", "RPM"]
RATE_LIMIT_KEYWORDS = ["error", "exceed"]


def limit_exception_raiser(e: Exception | str, is_429=False) -> None:
    """
    抛出指定的异常。根据异常字符串来判断是 TPM/RPM 限制还是并发限制，这两种都有可能返回 429

    :param e: 异常对象或字符串
    :param is_429: 是否已经确认肯定是 429 异常。如果是则至少按 TPM/RPM 限制处理
    :raises RateLimitException: 超出 API 的速率限制
    :raises TRLimitException: 超出 API 的 TPM/RPM 限制
    :raises e: 其他异常
    """
    if isinstance(e, Exception):
        e = str(e)

    for keyword in TPM_RPM_LIMIT_KEYWORDS:
        if keyword in e:
            raise TRLimitException(e)

    for keyword in RATE_LIMIT_KEYWORDS:
        if keyword in e:
            raise RateLimitException(e)

    # 如果是 429 异常，但是没有找到关键字，那么就按 TPM/RPM 限制顶格处理
    if is_429:
        raise TRLimitException(e)

    raise APIError(e)
