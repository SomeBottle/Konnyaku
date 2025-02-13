import argparse

from konnyaku.config import (
    check_config,
    LLM_API_KEY,
    LLM_API_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_API_STREAMING,
    SUMMARY_LLM_API_BASE_URL,
    SUMMARY_LLM_API_KEY,
    SUMMARY_LLM_MODEL,
    SUMMARY_LLM_TEMPERATURE,
    SUMMARY_LLM_API_STREAMING,
)
from konnyaku.subs import Sub
from konnyaku.translator import Translator
from konnyaku.llm import LLM
from konnyaku.utils import extract_bangumi_info
from konnyaku.errors import TranslateError


def main():
    arg_parser = argparse.ArgumentParser(
        usage="python -m konnyaku [-h] [-o output_subtitle_path] <input_subtitle_path> [bgm_subject_id]"
    )

    # 添加位置参数
    arg_parser.add_argument(
        "input",
        type=str,
        help="Input subtitle file path (srt or ass)",
        nargs=1,
        metavar="input_subtitle_path",
    )
    arg_parser.add_argument(
        "bgm_subject_id", type=str, help="Bangumi subject id", nargs="?"
    )

    # 添加可选参数
    arg_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output_chs.ass",
        help="Output subtitle file path",
    )

    args = arg_parser.parse_args()

    # 检查配置
    check_config()

    # 看看有没有 Bangumi Subject ID
    bangumi_subject_id = None
    if args.bgm_subject_id:
        bangumi_subject_id = args.bgm_subject_id

    # 输出文件路径

    # 字幕文件
    subtitle_file_path = args.input[0]
    try:
        sub = Sub(subtitle_file_path)
    except (FileNotFoundError, ValueError) as e:
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

    summary_llm = None

    if SUMMARY_LLM_API_KEY:
        summary_llm = LLM(
            api_key=SUMMARY_LLM_API_KEY,
            base_url=SUMMARY_LLM_API_BASE_URL,
            model=SUMMARY_LLM_MODEL,
            temperature=SUMMARY_LLM_TEMPERATURE,
            streaming=SUMMARY_LLM_API_STREAMING,
        )

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
    sub.export(args.output)


if __name__ == "__main__":
    main()
