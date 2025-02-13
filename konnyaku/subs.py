"""
字幕处理
"""

import pysubs2
import re

from os import path
from konnyaku.errors import TranslateMismatchException

LINE_BREAK_HOLDER = "<br>"


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

    def _escape_n(self, text: str) -> str:
        """
        把字幕文本中的 \\n \\N 替换为占位符

        :param text: 文本
        :return: 替换后的文本
        """
        return text.replace(r"\n", self.line_break_holder).replace(
            r"\N", self.line_break_holder
        )

    def _unescape_n(self, text: str) -> str:
        """
        把字幕文本中的占位符替换为 \\N

        :param text: 文本
        :return: 替换后的文本
        """
        return text.replace(self.line_break_holder, r"\N")

    def parse_numbered_lines(self, lines: list[str]) -> list[dict]:
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
                parsed_lines.append({"index": ind, "text": self._unescape_n(text)})
            else:
                # 格式错误
                raise ValueError(f"Unexpected line format: {line}")
        return parsed_lines

    def append_translated(self, translated_lines: list[str], expected_last_index: int):
        """
        解析并添加已翻译行。添加前会进行检查，确保序号连续且正确，否则会抛出异常请求重新翻译

        :param translated_lines: 已翻译行，带编号，每行格式为 [编号]一句台词
        :param expected_last_index: 期望的最后一行序号
        :raises ValueError: 翻译格式问题
        :raises TranslateMismatchException: 翻译行序号不匹配，有漏翻
        """
        if not translated_lines:
            return
        parsed_lines = self.parse_numbered_lines(translated_lines)

        first_line_index = parsed_lines[0]["index"]
        last_line_index = parsed_lines[-1]["index"]

        expected_first_index = len(self._translated_lines)

        # 先检查从 first_line_index 到 last_line_index 的序号是否连续
        i = 1
        while i < len(parsed_lines):
            if parsed_lines[i]["index"] != parsed_lines[i - 1]["index"] + 1:
                # 在 i 处序号不连续了
                raise TranslateMismatchException(
                    "Translated lines index not continuous.",
                    next_index=expected_first_index,
                )
            i += 1

        # 检查首尾行序号是否正确
        if first_line_index != expected_first_index:
            raise TranslateMismatchException(
                f"Translated lines first index mismatch, should be {expected_first_index}, got {first_line_index}. set next index:  {expected_first_index}",
                next_index=expected_first_index,
            )

        if last_line_index < expected_last_index:
            raise TranslateMismatchException(
                f"Translated lines last index mismatch, should be {expected_last_index}, got {last_line_index}. set next index: {expected_first_index}",
                next_index=expected_first_index,
            )
        elif last_line_index > expected_last_index:
            # 莫名其妙多翻译了，按理来说不会有这种情况
            raise ValueError(
                f"Translated lines end index unexpected, expected {expected_last_index} but got {last_line_index}."
            )

        # 如果序号正确则加入
        self._translated_lines.extend(
            [(line["index"], line["text"]) for line in parsed_lines]
        )

    def tail_translated(self, n=3, numbered=True) -> list[str]:
        """
        获取最后几行已翻译的台词

        :param n: 行数
        :param numbered: 是否带编号
        :return: 最后三行已翻译的台词
        """
        if len(self._translated_lines) < n:
            return []
        if numbered:
            return [
                f"[{ind}]{self._escape_n(text)}"
                for ind, text in self._translated_lines[-n:]
            ]
        else:
            return [text for _, text in self._translated_lines[-n:]]

    def bake_translated(self):
        """
        把已翻译的行写回字幕 pysubs2 对象
        """
        for i, text in self._translated_lines:
            self._subs[i].text = text

    def get_numbered_lines(self, start_ind=0, nums=150) -> str:
        """
        获取带编号的字幕行

        :param start_ind: 起始行下标
        :param nums: 行数
        :return: 字幕行字串，每行格式为 [编号]一句台词
        """
        sub_lines = []
        for i, line in enumerate(self._text_lines[start_ind : start_ind + nums]):
            # 把字幕中的 \n、\N 替换为特殊占位符
            sub_lines.append(f"[{start_ind+i}]{self._escape_n(line)}")

        return "\n".join(sub_lines)

    def export(self, file_path: str):
        """
        导出字幕

        :param file_path: 导出路径
        """
        self._subs.save(file_path)

    def __len__(self):
        return len(self._text_lines)
