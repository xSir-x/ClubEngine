#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT_PATH="$SCRIPT_DIR/user_stats.py"

# 激活虚拟环境（如果使用虚拟环境，取消下面一行的注释并修改路径）
# source $PROJECT_DIR/venv/bin/activate

# 切换到项目目录
cd "$PROJECT_DIR"

# 执行 Python 脚本
python3 "$SCRIPT_PATH"
