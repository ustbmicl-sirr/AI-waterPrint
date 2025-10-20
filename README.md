# 屏幕水印系统 (AI-waterPrint)

> 截屏 → 嵌入不可见水印 → 自动识别溯源

## 🚀 快速开始

```bash
bash start.sh              # 运行演示
```

## 📋 工作流程

1. **截屏** - 捕获真实屏幕内容
2. **嵌入水印** - 添加不可见的数字水印（PSNR > 48 dB）
3. **检测溯源** - 自动识别设备 ID 和会话 ID

## 📊 技术指标

- **水印强度**: 1.0 (不可见)
- **PSNR**: 48.13 dB (远高于 40 dB 不可见标准)
- **最大差异**: 1 像素
- **检测准确率**: 100%
- **置信度**: 73.83%
- **块大小**: 8×8 像素
- **载荷**: 32 字节 (设备 ID 16 + 会话 ID 16)

## 📁 项目结构

```
启动脚本:
  • start.sh                - 简单演示
  • start_realtime.sh       - 实时演示

Python 脚本:
  • screen_watermark_system.py      - 简单演示实现
  • screen_watermark_realtime.py    - 实时演示实现

源代码:
  • src/watermark_core.py   - 核心水印算法
  • src/server.py           - REST API 服务器

测试:
  • test_e2e.py             - 端到端测试

配置:
  • requirements.txt        - Python 依赖
```

## 📚 文档

- [软件需求.md](软件需求.md) - 需求规范
- [软件设计.md](软件设计.md) - 设计文档
- [架构图解.md](架构图解.md) - 架构图
- [文档索引.md](文档索引.md) - 文档导航
- [CLAUDE.md](CLAUDE.md) - Claude 指导
