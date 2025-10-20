#!/bin/bash

# 屏幕水印系统 - 实时演示脚本
# 功能: 实时显示屏幕水印，按 'q' 截屏溯源

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
echo "║     屏幕水印系统 - 实时演示                                ║"
echo "║                                                            ║"
echo "║  快捷键:                                                   ║"
echo "║    q   - 截屏并溯源水印                                   ║"
echo "║    ESC - 退出                                              ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

python3 screen_watermark_realtime.py

