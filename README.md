# Konnyaku

![Konnyaku](./image/translate_konnyaku.jpg)  

A simple and **robust** LLM workflow for anime subtitle file translation.

简单而稳定的动画字幕翻译脚本。

> 老实说翻译魔芋这东西我是真想要，吃一口直接能阅片无数了，畅游全球啊有木有 (ง ื▿ ื)ว  

## 演示视频

https://github.com/user-attachments/assets/83bfa703-2994-44b6-bd37-1e299ed99c84

## 特色

**自动应对**以下问题:  

1. LLM 批量翻译字幕时的输出截断问题（分批翻译字幕，如果仍然过长则自动缩减每一批送入的台词数量）。
2. API 的 TPM/RPM 以及并发限制（自动退避等待）。
3. 漏翻字幕（通过编号进行确认，有问题则重新翻译片段）。
4. 未知的片假名名字（对于人名，直接替换成罗马音；其余的音译）。
5. 翻译结果脱离番剧背景（通过 `bgm.tv` 接口获取番剧背景信息，使翻译结果更加贴切）。

因为本程序几乎没有涉及并发，一般不用担心 API 的并发限制。

## 使用

1. 克隆本项目，安装依赖。

    ```bash
    git clone https://github.com/SomeBottle/Konnyaku.git
    cd Konnyaku
    pip install -r requirements.txt
    ```

2. 新建启动脚本。  

    ```bash
    cp run.example.sh run.sh
    chmod +x run.sh
    ```

    编辑启动脚本，**配置环境变量**，详见下方说明。

3. 运行。

    ```bash
    ./run.sh [-o <output file path>] <srt or ass file> [bangumi subject id]
    # 例: 
    # - 直接翻译字幕，不提供背景信息，不指定输出路径:
    #   ./run.sh ./demo/zenshuu_06.ass
    #   (不指定输出路径则默认输出到同目录下 output_chs.ass)
    #
    # - 提供背景信息(来自 bgm.tv, 例如 https://bgm.tv/subject/486039 中 subject id 为 486039 )，翻译字幕: 
    #   ./run.sh ./demo/zenshuu_06.ass 486039
    #
    # - 指定输出路径: 
    #   ./run.sh -o ./demo/my.ass ./demo/zenshuu_06.ass 486039
    ```

## 配置

本翻译脚本需通过环境变量进行配置，可配置项及其说明如下。  

| 变量名 | 是否必须 | 说明 | 默认值 |
| --- | --- | --- | --- |
| `KYK_LLM_API_KEY` | **是** | （用于翻译字幕） LLM API KEY | 无 |
| `KYK_LLM_API_BASE_URL` | **是** | （用于翻译字幕） LLM API 终结点 URL | 无 |
| `KYK_LLM_MODEL` | **是** | （用于翻译字幕） 选用的 LLM 模型 ID | 无 |
| `KYK_LLM_TEMPERATURE` | 否 | （用于翻译字幕） LLM 温度，如果调高了翻译结果可能不可控 | `1.0` |
| `KYK_LLM_API_STREAMING` | 否 | （用于翻译字幕）是否流式接收 LLM 输出（`1` - 是，`0` - 否），建议为 `1`  | `0` |
| `KYK_SUM_LLM_API_KEY` | 否 | （用于字幕总结） LLM API KEY。💡 如果**不指定则不会进行字幕总结** | 无 |
| `KYK_SUM_LLM_API_BASE_URL` | 否 | （用于字幕总结） LLM API 终结点 URL | 无 |
| `KYK_SUM_LLM_MODEL` | 否 | （用于字幕总结） 选用的 LLM 模型 ID | 无 |
| `KYK_SUM_LLM_TEMPERATURE` | 否 | （用于字幕总结） LLM 温度 | `1.0` |
| `KYK_SUM_LLM_API_STREAMING` | 否 | （用于字幕总结）是否流式接收 LLM 输出（`1` - 是，`0` - 否），建议为 `1`  | `0` |
| `KYK_BANGUMI_API_TOKEN` | 否 | （用于获得番剧背景信息）`bgm.tv` API Token。💡 如果**不指定则不会获取背景信息**，可能影响翻译准确性 | 无 |
| `KYK_MAX_RETRY_TIMES` | 否 | LLM API 请求异常时的最多重试次数 | `3` |

* LLM API 需要**支持 OpenAI 接口风格**。
* 字幕总结可以用稍差一些的模型，有财力 (\$ω\$) 的话还是建议用和翻译模型同等级的模型。
* `bgm.tv` API Token 可以在 [这里](https://next.bgm.tv/demo/access-token) 申请。

## 附: 利用 ffmpeg 从视频中提取字幕流

```bash
# 查看媒体信息
ffmpeg -i <媒体文件路径>

# 提取字幕流
ffmpeg -i <媒体文件路径> -map 0:<流索引> <输出字幕文件路径>

# 比如你可能会看到类似这样的输出:
#   Stream #0:2: Subtitle: subrip (default)
# - 这里的 2 就是字幕流索引

# 提取字幕流为 ass 文件：
#   ffmpeg -i <媒体文件路径> -map 0:2 output.ass
```


## 碎碎念: 为什么要写这个玩意

咱追了 2025 年 1 月新番《全修。》来着，问题是这部被 Crunchyroll 拿下了，没有中文字幕，大陆也没代理商或平台买。民间字幕组产能有限，想第一时间看最多只能啃英肉。  

下载动画资源时咱发现有生肉资源附有日文字幕，于是就想着能不能用 LLM 翻译一下。找了几个相关项目感觉都不太满意，没怎么考虑到 API 限制以及翻译的稳定性。  

> 为什么不拿英文字幕来翻译？Crunchyroll 的英文翻译...我不好说...  

![真拿你没办法](./image/let_me_handle_it.jpg)  

真拿你没办法，那我就自己写一个吧！~~懒到抽筋的我没有整并发编程，至少这样挺稳定的不是吗~~ 

也希望这个脚本能帮助到有同样需求的朋友们。

## License

[MIT](./LICENSE)