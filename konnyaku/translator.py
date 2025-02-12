"""
翻译模块
"""

import re

from konnyaku.subs import Sub
from konnyaku.llm import LLM
from konnyaku.config import (
    TRANSLATE_SYSTEM_PREPROMPT,
    TRANSLATE_LINES_PER_REQUEST,
)
from konnyaku.errors import (
    RateLimitException,
    TRLimitException,
    TranslateError,
    SummarizeError,
    TranslateMismatchException,
)
from konnyaku.utils import RetrySleeper


class Translator:
    """
    翻译类
    """

    def __init__(
        self,
        sub: Sub,
        trans_llm: LLM,
        summary_llm: LLM | None,
        bgm_subject_info: str = None,
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
        sys_prompt = TRANSLATE_SYSTEM_PREPROMPT

        # 示例角色信息
        sys_prompt += (
            "【术语表示例】\n"
            "<角色术语表>\n"
            "千反田える -> 千反田爱瑠\n"
            "</角色术语表>\n\n"
        )

        if self.bgm_subject_info:
            sys_prompt += "【作品背景知识】\n" f"\n{self.bgm_subject_info}\n\n"

        if self.summary_text:
            sys_prompt += "【前情提要】\n" f"{self.summary_text}\n\n"

        sys_prompt += (
            "【日文假名翻译规则】\n"
            "1. 若 角色术语表、前情提要 或 上下文 中**能找到假名对应的中文名**时，使用该中文名。\n"
            "2. 否则**必须**把假名转换为**英文字母拼写的罗马音**。\n\n"
            "【字幕格式】\n"
            "字幕片段以 <sub> 开头，以 </sub> 结尾，每行格式为 [台词编号]一句台词 。\n\n"
            "【输入格式】\n"
            "1. <prev> 和 </prev> 之间为**上一批翻译**的最后几句台词。\n"
            "2. <sub> 和 </sub> 之间为本次需要翻译的台词。\n\n"
            "【字幕翻译规则】\n"
            '1. 如果输入中的 <sub> 或 </sub> 有缺失，**必须**仅返回一个字母"f"。\n'
            "2. 在翻译后**必须**以和【字幕格式】同样的格式返回。\n"
            "3. 台词是分批翻译的，如果有上一批的台词，你必须保证翻译**衔接通顺**。\n"
            f"4. 台词中的换行符已经用 {self.sub.line_break_holder} 替代，请保留。\n"
            "5. 必须保持**台词编号和输入的一致**。\n"
            "6. 日文**必须**遵循假名翻译规则。\n\n"
        )

        messages.append({"role": "system", "content": sys_prompt})

        # 给 LLM 对话示例
        messages.append(
            {
                "role": "user",
                "content": (
                    "<sub>\n"
                    "[3]今夜は月が綺麗ですね\n"
                    f"[4]（巴マミ）{self.sub.line_break_holder}もう何も怖くない\n"
                    "[5]（千反田える）私、気になります！\n"
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
                    f"[4]（巴Mami）{self.sub.line_break_holder}已经没什么好怕的了\n"
                    "[5]（千反田爱瑠）我很好奇！\n"
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
        # 没有指定摘要模型就不总结
        if not self.summary_llm:
            return ""

        print("Summarizing~")
        # 摘要总结系统提示词
        SUMMARY_SYSTEM_PROMPT = (
            "【角色定义】\n"
            "你是一个专业剧情分析师，擅长从复杂内容中提取核心信息。\n\n"
            "【输入来源】\n"
            "需整合用户提供的：\n"
            "1. <前情提要>：已有的故事背景与铺垫\n"
            "2. <台词>：每行一句的对话或描述\n\n"
            "【输出要求】\n"
            "用**精炼扼要的一句话**完成总结，必须包含：\n"
            "1. 核心剧情进展（关键转折）\n"
            "2. 涉及的角色（包括前情提要，**所有出现的角色都必须**写出来）\n"
            "3. 角色之间的主要戏剧冲突\n"
            "4. 如果有前情提要，必须在**前情提要的基础上**延续总结\n\n"
            "【强制格式】\n"
            "必须按此模板输出：\n"
            "<summary>【角色A | 角色B | ...】剧情主体（需体现因果逻辑，**必须遵循上方的输出要求**）</summary>\n"
            "* 必须以 <summary> 开头，以 </summary> 结尾\n\n"
            "【禁忌】\n"
            "× 禁止添加主观解读 × 禁止使用比喻修辞 × 避免时间状语"
        )

        messages = [{"role": "system", "content": SUMMARY_SYSTEM_PROMPT}]

        prompt_text = ""

        if self.summary_text:
            prompt_text += f"<前情提要>\n{self.summary_text}\n</前情提要>\n"

        prompt_text += "<台词>\n"
        for line in sub_lines:
            # 总结时把台词中的 \N 替换为空格
            line = line.replace(r"\N", " ")
            prompt_text += f"{line}\n"
        prompt_text += "</台词>\n"

        messages.append({"role": "user", "content": prompt_text})

        rate_sleeper = RetrySleeper(
            max_retry_times=5, max_wait_before_retry=40, start_wait_time=2
        )

        tr_sleeper = RetrySleeper(
            max_retry_times=3, max_wait_before_retry=100, start_wait_time=60
        )

        summary_pattern = re.compile(r"<summary>([\s\S]+?)</summary>")

        while True:
            try:
                response = self.summary_llm.call(messages)
                matches = summary_pattern.match(response)
                if not matches:
                    raise SummarizeError("Unexpected response format.")
                # 提取摘要
                response = matches.group(1)
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
            numbered_sub_lines = self.sub.get_numbered_lines(
                processed_lines, lines_per_request
            )

            # 生成提示词
            messages = self._gen_prompt()

            user_input = ""

            # 把上一批的最后 5 行加入提示词，防止上下文断开
            numbered_last_5_lines = self.sub.tail_translated(n=5, numbered=True)
            if len(numbered_last_5_lines) > 0:
                prev_sub_lines = "\n".join(numbered_last_5_lines)
                user_input += f"<prev>\n{prev_sub_lines}\n</prev>\n"

            user_input += f"<sub>\n{numbered_sub_lines}\n</sub>"

            messages.append({"role": "user", "content": user_input})

            try:
                response = self.trans_llm.call(messages)
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

                numbered_translated_lines = response.split("\n")

                # 没有头
                if (
                    len(numbered_translated_lines) < 2
                    or "<sub>" not in numbered_translated_lines[0]
                ):
                    print(f"Unexpected response: {response}...Retry...(╥﹏╥)")
                    continue

                numbered_translated_lines = numbered_translated_lines[
                    1:
                ]  # 去除首行 <sub>

                # 最后一行的序号应该是这个
                expected_last_index = (
                    min(processed_lines + lines_per_request, sub_len) - 1
                )

                # 别忘了，也可能超出输出限制
                # 检查翻译结果是否有头有尾
                if "</sub>" not in numbered_translated_lines[-1]:
                    # 超出输出限制导致截断
                    # 把已经翻译的部分加入结果，注意倒数两行都不能要
                    # 因为不知道最后两行是不是完整的
                    numbered_translated_lines = numbered_translated_lines[:-2]
                    self.sub.append_translated(
                        numbered_translated_lines, expected_last_index
                    )
                    # 退避翻译的行数
                    lines_per_request = len(numbered_translated_lines)
                    print("Output was truncated, will request less lines...(๑•́︿•̀๑)")
                else:
                    # 正常情况
                    numbered_translated_lines = numbered_translated_lines[:-1]
                    self.sub.append_translated(
                        numbered_translated_lines, expected_last_index
                    )

                if processed_lines + lines_per_request < sub_len:
                    # 不是最后一批，还需要生成摘要
                    # 解析带编号行，准备生成摘要
                    parsed_lines = [
                        line["text"]
                        for line in self.sub.parse_numbered_lines(
                            numbered_translated_lines
                        )
                    ]
                    self.summary_text = self._summarize(parsed_lines)

            except TranslateMismatchException as e:
                # 漏翻了，修正 processed_lines，重新翻译漏翻的部分
                print(f"Translate line mismatch: {e}, fixing...")
                processed_lines = e.next_index
                continue

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

            print(
                f"Translated {min(processed_lines,sub_len)}/{sub_len} lines.(ノ´∀`)ノ"
            )

        # 最后把翻译的行写回字幕
        self.sub.bake_translated()

        print("Translation completed!＼(＾▽＾)／")

        return self.sub
