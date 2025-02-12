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
LLM_TEMPERATURE = environ.get("KYK_LLM_TEMPERATURE", 1.0)

# 是否使用流式 API
LLM_API_STREAMING = environ.get("KYK_LLM_API_STREAMING", "0") == "1"


# 摘要生成模型的配置（可以不配置）
SUMMARY_LLM_API_KEY = environ.get("KYK_SUM_LLM_API_KEY")
SUMMARY_LLM_API_BASE_URL = environ.get("KYK_SUM_LLM_API_BASE_URL", None)
SUMMARY_LLM_MODEL = environ.get("KYK_SUM_LLM_MODEL")
SUMMARY_LLM_TEMPERATURE = environ.get("KYK_SUM_LLM_TEMPERATURE", 1.0)
SUMMARY_LLM_API_STREAMING = environ.get("KYK_SUM_LLM_API_STREAMING", "0") == "1"


# 主要用于抓取动画番剧基本信息，给大模型翻译提供背景信息
# 如果留空则不会有这些背景知识
# Bangumi.tv API Key
BANGUMI_API_KEY = environ.get("KYK_BANGUMI_API_KEY")

# 翻译系统前置提示词（后面还有一部分写死的系统提示词）
TRANSLATE_SYSTEM_PREPROMPT = (
    "【角色定义】\n"
    "你是动漫高手，熟练掌握了多国语言。\n"
    "你擅长把用户给出的动画字幕片段中的台词翻译为中文，且尽量翻译得**通顺自然**，能保持**上下文连贯性**，并**符合二次元文化的表达方式**。\n\n"
)

# 一次翻译多少行字幕
TRANSLATE_LINES_PER_REQUEST = 40


# 检查配置项
def check_config():
    if not LLM_API_KEY:
        raise ValueError("KYK_LLM_API_KEY is not set")
    if not LLM_API_BASE_URL:
        raise ValueError("KYK_LLM_API_BASE_URL is not set")
    if not LLM_MODEL:
        raise ValueError("KYK_LLM_MODEL is not set")
    
