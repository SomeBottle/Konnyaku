"""
整一些自定义异常 / 错误
"""


class KonnyakuException(Exception):
    """
    自定义异常基类
    """

    def __init__(self, message):
        if isinstance(message, Exception):
            self.message = str(message)
        else:
            self.message = message

    def __str__(self):
        return self.message


class RateLimitException(KonnyakuException):
    """
    API 超出速率限制引发的异常，往往是因为并发请求过多，需要缓一会儿
    """

    pass


class TRLimitException(KonnyakuException):
    """
    API 对每分钟 Token 和请求次数(TPM/RPM)限制引发的异常
    """

    pass


class TranslateError(KonnyakuException):
    """
    翻译出错
    """

    pass


class SummarizeError(KonnyakuException):
    """
    摘要总结出错
    """

    pass


class APIError(KonnyakuException):
    """
    API 调用出错
    """

    pass


class Unknown429Exception(KonnyakuException):
    """
    未知的 429 异常
    """

    pass


class TranslateMismatchException(KonnyakuException):
    """
    翻译错位异常，往往是漏翻了一些内容
    """

    def __init__(self, message, next_index: int):
        """
        初始化

        :param message: 错误信息
        :param next_index: 期待下次从哪个序号的字幕继续开始翻译
        """
        super().__init__(message)
        self.next_index = next_index
