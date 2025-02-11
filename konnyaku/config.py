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

# 是否使用流式 API
LLM_API_STREAMING = environ.get("KYK_LLM_API_STREAMING", "0") == "1"


# 主要用于抓取动画番剧基本信息，给大模型翻译提供背景信息
# 如果留空则不会有这些背景知识
# Bangumi.tv API Key
BANGUMI_API_KEY = environ.get("KYK_BANGUMI_API_KEY")

# 翻译系统提示词
TRANSLATE_SYSTEM_PROMPT = (
    "你是动漫高手，熟练掌握了多国语言。\n"
    "你需要把用户给出的动画字幕片段中的台词翻译为中文，尽量翻译得通顺自然，保持连贯性，符合二次元文化的表达方式。\n"
)

# 一次翻译多少行字幕
TRANSLATE_LINES_PER_REQUEST = 30


# 检查配置项
def check_config():
    if not LLM_API_KEY:
        raise ValueError("KYK_LLM_API_KEY is not set")
    if not LLM_API_BASE_URL:
        raise ValueError("KYK_LLM_API_BASE_URL is not set")
    if not LLM_MODEL:
        raise ValueError("KYK_LLM_MODEL is not set")
