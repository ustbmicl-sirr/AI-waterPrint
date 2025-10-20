#!/usr/bin/env python3
"""
屏幕水印系统 - 实时屏幕水印叠加和识别
支持实时渲染、水印叠加、截屏和识别
"""

import sys
import os
import time
import threading
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import mss
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from watermark_core import WatermarkEmbedder, WatermarkDetector


class RealtimeScreenWatermark:
    """实时屏幕水印系统"""
    
    def __init__(self, device_id='DEVICE-SCREEN-001', session_id='SESSION-REALTIME-001'):
        self.device_id = device_id
        self.session_id = session_id
        self.embedder = WatermarkEmbedder(device_id, session_id)
        self.detector = WatermarkDetector()
        self.running = False
        self.screenshot_path = 'realtime_screenshot.png'
        self.watermarked_path = 'realtime_watermarked.png'
        
    def create_frame(self, frame_num, width=1280, height=720):
        """创建单帧内容"""
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # 标题
        draw.text((50, 50), "实时屏幕水印系统", fill='black', font=font_large)
        
        # 内容
        y_pos = 150
        draw.text((50, y_pos), f"设备 ID: {self.device_id}", fill='blue', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), f"会话 ID: {self.session_id}", fill='blue', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), f"帧数: {frame_num}", fill='red', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), f"时间: {time.strftime('%H:%M:%S')}", fill='green', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), "此屏幕已嵌入不可见的数字水印", fill='darkgreen', font=font_medium)
        
        # 底部信息
        draw.text((50, height - 100), 
                 "按 'q' 键截屏并识别水印 | 按 'ESC' 退出", 
                 fill='gray', font=font_small)
        
        return np.array(img)
    
    def embed_watermark_on_frame(self, frame):
        """在帧上嵌入水印"""
        # 转换为灰度
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame
        
        # 嵌入不可见水印 (强度 1.0 = 不可见, PSNR > 40 dB)
        watermarked = self.embedder.embed(gray, strength=1.0)
        
        # 转换回彩色
        watermarked_color = cv2.cvtColor(watermarked, cv2.COLOR_GRAY2RGB)
        
        return watermarked_color, watermarked
    
    def run_realtime(self, duration=30):
        """运行实时水印系统"""
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  实时屏幕水印系统".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        
        print(f"\n⏱️  运行时间: {duration} 秒")
        print("按 'q' 键截屏并识别水印")
        print("按 'ESC' 退出\n")
        
        frame_num = 0
        start_time = time.time()
        last_watermarked = None
        
        try:
            while True:
                # 检查是否超时
                if time.time() - start_time > duration:
                    print("\n⏱️  时间到，退出演示")
                    break
                
                # 创建帧
                frame = self.create_frame(frame_num)
                
                # 嵌入水印
                watermarked_color, watermarked_gray = self.embed_watermark_on_frame(frame)
                last_watermarked = watermarked_gray
                
                # 显示帧
                display_frame = cv2.cvtColor(watermarked_color, cv2.COLOR_RGB2BGR)
                cv2.imshow('屏幕水印系统 - 实时演示', display_frame)
                
                # 处理按键
                key = cv2.waitKey(100) & 0xFF
                
                if key == ord('q'):
                    # 截屏
                    print("\n📸 截屏...")
                    cv2.imwrite(self.watermarked_path, display_frame)
                    print(f"✓ 截屏已保存: {self.watermarked_path}")
                    
                    # 识别水印
                    print("\n🔍 识别水印...")
                    result = self.detector.detect(last_watermarked)
                    
                    # 显示结果
                    self.display_detection_result(result)
                    
                    # 继续或退出
                    print("\n按任意键继续，或按 'ESC' 退出...")
                    key = cv2.waitKey(0) & 0xFF
                    if key == 27:  # ESC
                        break
                
                elif key == 27:  # ESC
                    print("\n👋 退出演示")
                    break
                
                frame_num += 1
        
        finally:
            cv2.destroyAllWindows()
    
    def display_detection_result(self, result):
        """显示检测结果"""
        print("\n" + "="*60)
        print("✅ 水印检测结果")
        print("="*60)
        
        if result:
            print(f"\n检测到水印: {result['found']}")
            print(f"设备 ID: {result['device_id']}")
            print(f"会话 ID: {result['session_id']}")
            print(f"置信度: {result['confidence']:.2%}")
            
            # 验证
            if (result['device_id'] == self.device_id and 
                result['session_id'] == self.session_id):
                print("\n✅ 水印验证成功！")
                print(f"   设备 ID 匹配: {self.device_id}")
                print(f"   会话 ID 匹配: {self.session_id}")
            else:
                print("\n⚠️  水印信息不匹配")
        else:
            print("❌ 未检测到水印")
        
        print("="*60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='实时屏幕水印系统')
    parser.add_argument('--device-id', default='DEVICE-001', help='设备 ID (≤16字节)')
    parser.add_argument('--session-id', default='SESSION-001', help='会话 ID (≤16字节)')
    parser.add_argument('--duration', type=int, default=30, help='运行时间（秒）')
    
    args = parser.parse_args()
    
    system = RealtimeScreenWatermark(
        device_id=args.device_id,
        session_id=args.session_id
    )
    system.run_realtime(duration=args.duration)


if __name__ == '__main__':
    main()

