import sys

from konnyaku.config import check_config
from konnyaku.entities import Sub
from konnyaku.translator import Translator

if __name__ == "__main__":
    check_config()

    if len(sys.argv) < 2:
        print("Usage: python -m konnyaku <subtitle file> [bangumi subject id]")
        exit(1)

    # 看看有没有 Bangumi Subject ID
    bangumi_subject_id = None
    if len(sys.argv) == 3:
        bangumi_subject_id = sys.argv[2]

    # 字幕文件
    subtitle_file_path = sys.argv[1]
    try:
        sub = Sub(subtitle_file_path)
    except FileNotFoundError as e:
        print(e)
        exit(1)

    # TODO: BGM 信息抽取，注意可能没有 api key，就跳过.

    # 开始翻译
    translator = Translator(sub)


