"""
翻译模块
"""

from konnyaku.subs import Sub
from konnyaku.llm import LLM
from konnyaku.config import (
    TRANSLATE_SYSTEM_PROMPT,
    TRANSLATE_LINES_PER_REQUEST,
)
from konnyaku.errors import (
    RateLimitException,
    TRLimitException,
    TranslateError,
    SummarizeError,
)
from konnyaku.utils import RetrySleeper


class Translator:
    """
    翻译类
    """

    def __init__(
        self, sub: Sub, trans_llm: LLM, summary_llm: LLM, bgm_subject_info: str = None
    ):
        """
        初始化

        :param sub: 字幕对象
        :param trans_llm: 翻译 LLM
        :param summary_llm: 摘要 LLM
        :param bgm_subject_info: Bangumi 番剧信息
        """
        self.sub = sub
        self.bgm_subject_info = bgm_subject_info
        self.summary_text = ""
        self.trans_llm = trans_llm
        self.summary_llm = summary_llm

    def _gen_prompt(self) -> list[dict]:
        """
        生成提示词

        :return: 提示词 messages 列表
        """
        messages = []
        sys_prompt = TRANSLATE_SYSTEM_PROMPT

        if self.bgm_subject_info:
            sys_prompt += (
                "下方是作品的背景知识，供参考：\n"
                f"<背景知识>\n{self.bgm_subject_info}\n</背景知识>\n\n"
            )

        if self.summary_text:
            sys_prompt += (
                "下方是上文已经翻译的部分剧情摘要，供参考：\n"
                f"<摘要>\n{self.summary_text}\n</摘要>\n\n"
            )

        sys_prompt += (
            "字幕片段以 <sub> 开头，以 </sub> 结尾，每行格式为 [编号]一句台词 。\n"
            f"台词中的换行符已经用 {self.sub.line_break_holder} 替代，请保留。\n"
            "在翻译后你**必须**以同样的格式返回。\n"
            '如果输入的 <sub> 或 </sub> 有缺失，**必须**仅返回"f"。\n'
        )

        messages.append({"role": "system", "content": sys_prompt})

        # 给 LLM 对话示例
        messages.append(
            {
                "role": "user",
                "content": (
                    "<sub>\n"
                    "[3]今夜は月が綺麗ですね\n"
                    "[4]もう何も怖くない\n"
                    "[5]私、気になります！\n"
                    "</sub>"
                ),
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": (
                    "<sub>\n"
                    "[3]今晚的月色真美啊\n"
                    "[4]已经没什么好怕的了\n"
                    "[5]我很好奇！\n"
                    "</sub>"
                ),
            }
        )
        messages.append(
            {
                "role": "user",
                "content": "[28]test\n</sub>",
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": "f",
            }
        )

        return messages

    def _summarize(self, sub_lines: list[str]) -> str:
        """
        对之前生成的翻译结果生成摘要

        :param sub_lines: 台词列表，不带编号
        :raises SummarizeError: 摘要出错
        :return: 摘要文本
        """
        print("Summarizing~")
        # 摘要总结系统提示词
        SUMMARY_SYSTEM_PROMPT = (
            "你是擅长剧情总结的助理。\n"
            "你需要根据用户给出的<摘要>和<台词>（台词一行一句），以**精炼扼要**的语言总结为**一句话**，要求能涵盖剧情要点，切记**不要**丢掉之前摘要中的要点。\n"
            "台词中的 \\N 可以忽略。\n"
            "请注意，你的输出**必须**以<summary>开头，以</summary>结尾。\n"
        )

        messages = [{"role": "system", "content": SUMMARY_SYSTEM_PROMPT}]

        prompt_text = ""

        if self.summary_text:
            prompt_text += f"<摘要>\n{self.summary_text}\n</摘要>\n"

        prompt_text += "<台词>\n"
        for line in sub_lines:
            prompt_text += f"{line}\n"
        prompt_text += "</台词>\n"

        messages.append({"role": "user", "content": prompt_text})

        rate_sleeper = RetrySleeper(
            max_retry_times=5, max_wait_before_retry=40, start_wait_time=2
        )

        tr_sleeper = RetrySleeper(
            max_retry_times=3, max_wait_before_retry=100, start_wait_time=60
        )

        while True:
            try:
                response = self.summary_llm.call(messages)
                if not response.startswith("<summary>") or not response.endswith(
                    "</summary>"
                ):
                    raise SummarizeError("Unexpected response format.")

                break
            except RateLimitException:
                if rate_sleeper.sleep():
                    continue
                else:
                    raise SummarizeError(
                        "Rate limit exceeded when summarizing, and cannot be solved.（´；д；`）"
                    )
            except TRLimitException:
                if tr_sleeper.sleep():
                    continue
                else:
                    raise SummarizeError(
                        "TPM/RPM limit exceeded when summarizing, and cannot be solved.（´；д；`）"
                    )
            except Exception as e:
                raise SummarizeError(e)

        # 去掉 <summary> 标签
        response = response.replace("<summary>", "").replace("</summary>", "")

        return response

    def translate(self) -> Sub:
        """
        翻译字幕

        :raises TranslateError: 翻译出错
        :return: 翻译结果字幕
        """

        # 获取字幕行数
        sub_len = len(self.sub)

        # 每次请求的行数
        lines_per_request = TRANSLATE_LINES_PER_REQUEST

        # 目前处理到的行数
        processed_lines = 0

        rate_sleeper = RetrySleeper(
            max_retry_times=5, max_wait_before_retry=40, start_wait_time=2
        )

        tr_sleeper = RetrySleeper(
            max_retry_times=3, max_wait_before_retry=100, start_wait_time=60
        )

        print("Start translating...(ﾉ≧ڡ≦)")

        # 取出一批进行翻译
        while processed_lines < sub_len:
            sub_lines = self.sub.get_lines(processed_lines, lines_per_request)

            # 生成提示词
            messages = self._gen_prompt()
            messages.append({"role": "user", "content": f"<sub>\n{sub_lines}\n</sub>"})

            try:
                response = self.trans_llm.call(messages)
                """
                如果正常，此处 response 格式为:
                <sub>
                [3]今晚的月色真美啊
                [4]已经没什么好怕的了
                [5]我很好奇！
                </sub>
                """
                # 请求成功了，重置退避
                rate_sleeper.reset()
                tr_sleeper.reset()
                # 除了异常外，还可能输入上下文过长导致截断
                if response == "f":
                    # 如果截断，processed_lines 折半退避
                    print("Context too long, retrying...(๑•́︿•̀๑)")
                    lines_per_request = lines_per_request // 2
                    if lines_per_request == 0:
                        # 这说明前置提示词太长了
                        raise TranslateError(
                            "Pre-prompt too long, and cannot be solved.（´；д；`）"
                        )
                    continue

                translated_lines = response.split("\n")

                # 没有头
                if len(translated_lines) < 2 or "<sub>" not in translated_lines[0]:
                    print(f"Unexpected response: {response}...Retry...(╥﹏╥)")
                    continue

                translated_lines = translated_lines[1:]  # 去除首行 <sub>

                # 别忘了，也可能超出输出限制
                # 检查翻译结果是否有头有尾
                if "</sub>" not in translated_lines[-1]:
                    # 超出输出限制导致截断
                    # 把已经翻译的部分加入结果，注意倒数两行都不能要
                    # 因为不知道最后两行是不是完整的
                    translated_lines = translated_lines[:-2]
                    self.sub.append_translated(translated_lines)
                    # 退避翻译的行数
                    lines_per_request = len(translated_lines)
                    print("Output was truncated, will request less lines...(๑•́︿•̀๑)")
                else:
                    # 正常情况
                    translated_lines = translated_lines[:-1]
                    self.sub.append_translated(translated_lines)

                # 解析带编号行，准备生成摘要
                parsed_lines = [
                    line["text"] for line in self.sub.parse_lines(translated_lines)
                ]
                self.summary_text = self._summarize(parsed_lines)

            except SummarizeError as e:
                print(f"Summarize error: {e}, this may not be a big problem.")

            except RateLimitException:
                print("Rate limit exceeded...∑(°口°๑)")
                if rate_sleeper.sleep():
                    continue
                else:
                    raise TranslateError(
                        "Rate limit exceeded, and cannot be solved.（´；д；`）"
                    )
            except TRLimitException:
                print("TPM/RPM limit exceeded...∑(°口°๑)")
                if tr_sleeper.sleep():
                    continue
                else:
                    raise TranslateError(
                        "TPM/RPM limit exceeded, and cannot be solved.（´；д；`）"
                    )
            except Exception as e:
                print("Unexpected error ocurred...(╥﹏╥)")
                raise TranslateError(e)

            processed_lines += lines_per_request

            print(f"Translated {processed_lines}/{sub_len} lines.(ノ´∀`)ノ")

        # 最后把翻译的行写回字幕
        self.sub.bake_translated()

        print("Translation completed!＼(＾▽＾)／")

        return self.sub
