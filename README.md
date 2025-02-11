# Konnyaku
A simple and **robust** LLM workflow for anime subtitle file translation.

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

    编辑启动脚本，填入 API Key, Base URL 等信息。  

3. 运行。

    ```bash
    ./run.sh 
    ```