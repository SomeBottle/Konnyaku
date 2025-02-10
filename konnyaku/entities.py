"""
存放一些实体类
"""

from os import path


class Sub:
    """
    字幕类
    """

    def __init__(self, file_path):
        """
        初始化

        :param file_path: 字幕文件路径
        :raises FileNotFoundError: 字幕文件不存在
        """
        self.path = file_path
        if not path.exists(file_path):
            raise FileNotFoundError(f"Subtitle file {file_path} does not exist.")
        # 读入内存
        self.lines = []
        with open(file_path, "r", encoding="utf-8") as f:
            self.lines = f.readlines()
