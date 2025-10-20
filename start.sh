#!/bin/bash

# 屏幕水印系统 - 启动脚本
# 功能: 显示器增加水印 → 截屏 → 水印溯源

set -e

ENV_NAME="watermark-env"

# 初始化 conda
eval "$(conda shell.bash hook)"

# 检查环境是否存在，不存在则创建
if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "创建 conda 环境..."
    conda create -n $ENV_NAME python=3.9 -y > /dev/null 2>&1
    conda activate $ENV_NAME
    echo "安装依赖..."
    pip install -q -r requirements.txt
else
    conda activate $ENV_NAME
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║     屏幕水印系统 - 启动                                    ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

python3 screen_watermark_system.py

