"""
配置读取模块(从环境变量中读取)
"""

from os import environ

# API 请求异常时的重试次数
MAX_RETRY_TIMES = int(environ.get("KYK_MAX_RETRY_TIMES", 3))

# 重试等待的时间随机区间（秒）
RETRY_WAIT_RANGE = (2, 6)

# LLM API Key
LLM_API_KEY = environ.get("KYK_LLM_API_KEY")

# LLM API Base URL
LLM_API_BASE_URL = environ.get("KYK_LLM_API_BASE_URL", None)

# LLM Model
LLM_MODEL = environ.get("KYK_LLM_MODEL")

# LLM Temperature
# 此处根据 DeepSeek 的建议，翻译场景下默认设置为 1.3
LLM_TEMPERATURE = environ.get("KYK_LLM_TEMPERATURE", 1.3)


# 主要用于抓取动画番剧基本信息，给大模型翻译提供背景信息
# 如果留空则不会有这些背景知识
# Bangumi.tv API Key
BANGUMI_API_KEY = environ.get("KYK_BANGUMI_API_KEY")

# 检查配置项
def check_config():
    if not LLM_API_KEY:
        raise ValueError("KYK_LLM_API_KEY is not set")
    if not LLM_API_BASE_URL:
        raise ValueError("KYK_LLM_API_BASE_URL is not set")
    if not LLM_MODEL:
        raise ValueError("KYK_LLM_MODEL is not set")
