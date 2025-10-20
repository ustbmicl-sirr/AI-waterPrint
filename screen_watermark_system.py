#!/usr/bin/env python3
"""
屏幕水印系统 - 实时屏幕渲染、水印叠加、截屏和识别
完整的端到端演示脚本
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


class ScreenWatermarkSystem:
    """屏幕水印系统"""
    
    def __init__(self, device_id='DEVICE-SCREEN-001', session_id='SESSION-DEMO-001'):
        self.device_id = device_id
        self.session_id = session_id
        self.embedder = WatermarkEmbedder(device_id, session_id)
        self.detector = WatermarkDetector()
        self.running = False
        self.screenshot_path = 'screen_screenshot.png'
        self.watermarked_screenshot_path = 'screen_watermarked.png'
        
    def capture_screen(self):
        """截屏真实屏幕内容"""
        print("\n📸 正在截屏真实屏幕...")

        try:
            with mss.mss() as sct:
                # 获取主屏幕
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                # 转换为 numpy 数组
                img = np.array(screenshot)

                # 转换 BGRA 到 RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

                # 保存原始截屏
                cv2.imwrite(self.screenshot_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                print(f"✓ 屏幕截图已保存: {self.screenshot_path}")
                print(f"  分辨率: {img.shape[1]}x{img.shape[0]}")

                return img
        except Exception as e:
            print(f"❌ 截屏失败: {e}")
            print("  使用演示内容代替...")
            return self.create_demo_content()

    def create_demo_content(self, width=1280, height=720):
        """创建演示内容（备用）"""
        print("\n📝 创建演示内容...")

        # 创建图像
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)

        # 添加文本
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # 标题
        draw.text((50, 50), "屏幕水印系统演示", fill='black', font=font_large)

        # 内容
        y_pos = 150
        draw.text((50, y_pos), f"设备 ID: {self.device_id}", fill='blue', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), f"会话 ID: {self.session_id}", fill='blue', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), "此屏幕已嵌入不可见的数字水印", fill='green', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), "水印包含设备和会话信息", fill='green', font=font_medium)
        y_pos += 80
        draw.text((50, y_pos), "截屏后可以识别水印并溯源", fill='green', font=font_medium)

        # 底部信息
        draw.text((50, height - 100), f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                 fill='gray', font=font_small)

        # 保存原始图像
        img.save(self.screenshot_path)
        print(f"✓ 演示内容已创建: {self.screenshot_path}")

        return np.array(img)
    
    def embed_watermark(self, image_array):
        """嵌入水印"""
        print("\n🎨 嵌入水印...")
        
        # 转换为灰度
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # 嵌入不可见水印 (强度 1.0 = 不可见, PSNR > 40 dB)
        watermarked = self.embedder.embed(gray, strength=1.0)
        
        # 转换回彩色（为了显示）
        watermarked_color = cv2.cvtColor(watermarked, cv2.COLOR_GRAY2RGB)
        
        # 保存带水印的图像
        cv2.imwrite(self.watermarked_screenshot_path, cv2.cvtColor(watermarked_color, cv2.COLOR_RGB2BGR))
        print(f"✓ 水印已嵌入: {self.watermarked_screenshot_path}")
        
        return watermarked
    
    def detect_watermark(self, image_path):
        """检测水印"""
        print("\n🔍 检测水印...")
        
        # 读取图像
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"❌ 无法读取图像: {image_path}")
            return None
        
        # 检测水印
        result = self.detector.detect(image)
        
        return result
    
    def display_results(self, detection_result):
        """显示检测结果"""
        print("\n" + "="*60)
        print("✅ 水印检测结果")
        print("="*60)
        
        if detection_result:
            print(f"\n检测到水印: {detection_result['found']}")
            print(f"设备 ID: {detection_result['device_id']}")
            print(f"会话 ID: {detection_result['session_id']}")
            print(f"置信度: {detection_result['confidence']:.2%}")
            print(f"载荷: {detection_result['payload']}")
            
            # 验证
            if (detection_result['device_id'] == self.device_id and 
                detection_result['session_id'] == self.session_id):
                print("\n✅ 水印验证成功！")
                print(f"   设备 ID 匹配: {self.device_id}")
                print(f"   会话 ID 匹配: {self.session_id}")
            else:
                print("\n⚠️  水印信息不匹配")
                print(f"   期望设备 ID: {self.device_id}")
                print(f"   实际设备 ID: {detection_result['device_id']}")
                print(f"   期望会话 ID: {self.session_id}")
                print(f"   实际会话 ID: {detection_result['session_id']}")
        else:
            print("❌ 未检测到水印")
        
        print("="*60 + "\n")
    
    def run_demo(self):
        """运行完整演示"""
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  屏幕水印系统 - 完整演示".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")

        try:
            # 步骤 1: 截屏真实屏幕
            print("\n[步骤 1/3] 截屏真实屏幕")
            image_array = self.capture_screen()

            # 步骤 2: 嵌入水印
            print("\n[步骤 2/3] 嵌入水印")
            watermarked = self.embed_watermark(image_array)

            # 步骤 3: 检测水印
            print("\n[步骤 3/3] 检测水印")
            detection_result = self.detect_watermark(self.watermarked_screenshot_path)

            # 显示结果
            self.display_results(detection_result)

            print("✅ 演示完成！")

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    system = ScreenWatermarkSystem(
        device_id='DEVICE-001',  # 保持在 16 字节以内
        session_id='SESSION-001'  # 保持在 16 字节以内
    )
    system.run_demo()


if __name__ == '__main__':
    main()

