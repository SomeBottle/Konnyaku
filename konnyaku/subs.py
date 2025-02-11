"""
字幕处理
"""

import pysubs2
import re

from os import path

LINE_BREAK_HOLDER = "[N]"


class Sub:
    """
    字幕类
    """

    def __init__(self, file_path):
        """
        初始化

        :param file_path: 字幕文件路径
        :raises FileNotFoundError: 字幕文件不存在
        :raises ValueError: 读取字幕文件失败
        """
        self._path = file_path
        if not path.exists(file_path):
            raise FileNotFoundError(f"Subtitle file {file_path} does not exist.")
        try:
            # 读入内存
            self._subs = pysubs2.load(file_path)
            # 把字幕按行提取出来
            self._text_lines = [line.text for line in self._subs]
        except pysubs2.Pysubs2Error as e:
            raise ValueError(f"Failed to load subtitle file: {e}")

        # 已经翻译的行
        self._translated_lines = []

    @property
    def line_break_holder(self) -> str:
        """
        获取换行符占位符

        :return: 换行符占位符
        """
        return LINE_BREAK_HOLDER

    def len(self) -> int:
        """
        获取字幕行数

        :return: 字幕行数
        """
        return len(self._text_lines)

    def parse_lines(self, lines: list[str]) -> list[dict]:
        """
        解析带编号的字串行，形如 [编号]一句台词

        :param lines: 带编号的台词列表
        :return: 解析后的台词列表 [{"index": 编号, "text": 台词}, ...]
        :raises ValueError: 格式问题
        """
        pattern = re.compile(r"\[(\d+)\](.*)")
        parsed_lines = []
        for line in lines:
            match = pattern.match(line)
            if match and len(match.groups()) == 2:
                ind = int(match.group(1))
                text = match.group(2)
                # 替换掉特殊占位符
                text = text.replace(self.line_break_holder, r"\N")
                parsed_lines.append({"index": ind, "text": text})
            else:
                # 格式错误
                raise ValueError(f"Unexpected line format: {line}")
        return parsed_lines

    def append_translated(self, translated_lines: list[str]):
        """
        解析并添加已翻译行

        :param translated_lines: 已翻译行
        :raises ValueError: 翻译格式问题
        """
        if not translated_lines:
            return
        pattern = re.compile(r"\[(\d+)\](.*)")
        parsed_lines = self.parse_lines(translated_lines)

        # 检查序号是否正确
        if parsed_lines[0]["index"] != len(self._translated_lines):
            raise ValueError("Translated lines index mismatch.")

        # 如果序号正确则加入
        self._translated_lines.extend([line["text"] for line in parsed_lines])

    def bake_translated(self):
        """
        把已翻译的行写回字幕 pysubs2 对象
        """
        for i, line in enumerate(self._translated_lines):
            self._subs[i].text = line

    def get_lines(self, start_ind=0, nums=150) -> str:
        """
        获取字幕行

        :param start_ind: 起始行下标
        :param nums: 行数
        :return: 字幕行字串，每行格式为 [编号]一句台词
        """
        sub_lines = []
        for i, line in enumerate(self._text_lines[start_ind : start_ind + nums]):
            # 把字幕中的 \n、\N 替换为特殊占位符
            line = line.replace(r"\n", self.line_break_holder).replace(
                r"\N", self.line_break_holder
            )
            sub_lines.append(f"[{start_ind+i}]{line}")

        return "\n".join(sub_lines)

    def export(self, file_path: str):
        """
        导出字幕

        :param file_path: 导出路径
        """
        self._subs.save(file_path)

    def __len__(self):
        return len(self._text_lines)
