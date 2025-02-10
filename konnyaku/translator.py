"""
翻译模块
"""

from konnyaku.entities import Sub
from konnyaku.llm import call_llm


class Translator:
    """
    翻译类
    """

    def __init__(self, sub: Sub):
        """
        初始化

        :param sub: 字幕对象
        """
        self.sub = sub
        # 已翻译的行
        self.translated = []
