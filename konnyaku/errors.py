"""
整一些自定义异常 / 错误
"""


class RateLimitException(Exception):
    """
    API 超出速率限制引发的异常，往往是因为并发请求过多，需要缓一会儿
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class TRLimitException(Exception):
    """
    API 对每分钟 Token 和请求次数(TPM/RPM)限制引发的异常
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class Unknown429Exception(Exception):
    """
    未知 429 异常
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class TranslateError(Exception):
    """
    翻译出错
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class SummarizeError(Exception):
    """
    摘要总结出错
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class APIError(Exception):
    """
    API 调用异常
    """

    def __init__(self, message):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message
