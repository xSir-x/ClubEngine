#!/bin/bash

# 设置项目路径
PROJECT_DIR="~/tennis_buddy_back_end/ClubEngine"
SCRIPT_PATH="$PROJECT_DIR/stats/user_stats.py"

# 激活虚拟环境（如果使用虚拟环境，取消下面一行的注释并修改路径）
# source $PROJECT_DIR/venv/bin/activate

# 执行 Python 脚本
cd "$PROJECT_DIR"
python3 "$SCRIPT_PATH"
