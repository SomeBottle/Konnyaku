# Konnyaku

![Konnyaku](./image/translate_konnyaku.jpg)  

A simple and **robust** LLM workflow for anime subtitle file translation.

## 演示视频

https://github.com/user-attachments/assets/3f720a85-c7bd-4363-88f1-fa260ca937bd

## 特色

**自动应对**以下问题:  

1. LLM 批量翻译字幕时的输出截断问题（分批翻译字幕，如果仍然过长则自动缩减每一批送入的台词数量）。
2. API 的 TPM/RPM 以及并发限制（自动退避等待）。
3. 漏翻字幕（通过编号进行确认，有问题则重新翻译片段）。
4. 未知的片假名名字（对于人名，直接替换成罗马音；其余的音译）。

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

## 环境变量配置

待完善 （；´д｀）ゞ...  