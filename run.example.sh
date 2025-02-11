#!/bin/bash

if [ $# -lt 1 ]; then
    echo 'Usage: ./run.sh <srt or ass file> [bangumi subject id]'

# See https://bangumi.github.io/api/
export KYK_BANGUMI_API_KEY=

export KYK_LLM_API_KEY=
export KYK_LLM_API_BASE_URL=
export KYK_LLM_MODEL=
# export KYK_LLM_API_STREAMING=1

export KYK_SUM_LLM_API_KEY=
export KYK_SUM_LLM_API_BASE_URL='https://api.siliconflow.cn/v1'
export KYK_SUM_LLM_MODEL='Qwen/Qwen2.5-7B-Instruct'
export KYK_SUM_LLM_API_STREAMING=1

python -m konnyaku $1 $2