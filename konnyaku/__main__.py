import sys

from konnyaku.config import (
    check_config,
    LLM_API_KEY,
    LLM_API_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_API_STREAMING,
)
from konnyaku.subs import Sub
from konnyaku.translator import Translator
from konnyaku.llm import LLM
from konnyaku.utils import extract_bangumi_info
from konnyaku.errors import TranslateError

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
    except FileNotFoundError | ValueError as e:
        print(e)
        exit(1)

    # BGM 信息抽取，注意可能没有 api key，就跳过.
    bgm_subject_info = None
    if bangumi_subject_id:
        print("Fetching bangumi info...∑(っ °Д °;)っ")
        try:
            bgm_subject_info = extract_bangumi_info(bangumi_subject_id)
            print(f"----------\n{bgm_subject_info}\n----------")
        except Exception as e:
            print(e)
            print("Failed to fetch Bangumi subject info, skipping...(´；д；`)")

    # 开始翻译
    translator_llm = LLM(
        api_key=LLM_API_KEY,
        base_url=LLM_API_BASE_URL,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        streaming=LLM_API_STREAMING,
    )
    summary_llm = translator_llm

    translator = Translator(
        sub,
        trans_llm=translator_llm,
        summary_llm=summary_llm,
        bgm_subject_info=bgm_subject_info,
    )

    print("Translating...(•̀ω•́✧)")

    try:
        sub_chs = translator.translate()
    except TranslateError as e:
        print("Failed to translate the subtitle file (´；д；`)")
        print(e)
        exit(1)

    print("Exporting...(´∀`)")
    sub.export("output_chs.ass")
