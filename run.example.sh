#!/bin/bash

# ------------- CONFIGURATION START

# See https://bangumi.github.io/api/
export KYK_BANGUMI_API_TOKEN=

export KYK_LLM_API_KEY=
export KYK_LLM_API_BASE_URL=
export KYK_LLM_MODEL=
# export KYK_LLM_API_STREAMING=1

export KYK_SUM_LLM_API_KEY=
export KYK_SUM_LLM_API_BASE_URL='https://api.siliconflow.cn/v1'
export KYK_SUM_LLM_MODEL='deepseek-ai/DeepSeek-V3'
export KYK_SUM_LLM_API_STREAMING=1

# ------------- CONFIGURATION END


output_file="output_chs.ass"

while getopts ":o:" opt; do
    case $opt in
    o)
        output_file="$OPTARG"
        ;;
    esac
done

# Shift parameters to skip '-o <output file path>'
shift $((OPTIND - 1))

if [ $# -lt 1 ]; then
    echo "Usage: $0 [-o <output file path>] <srt or ass file> [bangumi subject id]"
    exit 1
fi


python -m konnyaku $1 $2 -o $output_file
