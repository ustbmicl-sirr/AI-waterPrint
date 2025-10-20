"""
水印嵌入与检测核心模块
实现基础的 DWT + DCT + QIM 水印算法
"""

import numpy as np
from scipy import signal
from scipy.fftpack import dct, idct
import pywt
import hashlib
import struct


class WatermarkEmbedder:
    """水印嵌入器"""
    
    def __init__(self, device_id: str, session_id: str):
        """
        初始化水印嵌入器
        
        Args:
            device_id: 设备标识符
            session_id: 会话标识符
        """
        self.device_id = device_id
        self.session_id = session_id
        self.payload = self._create_payload()
        
    def _create_payload(self) -> bytes:
        """创建水印载荷 (32 bytes)"""
        # 格式: device_id(16) + session_id(16)
        device_bytes = self.device_id.encode('utf-8')[:16].ljust(16, b'\x00')
        session_bytes = self.session_id.encode('utf-8')[:16].ljust(16, b'\x00')
        return device_bytes + session_bytes
    
    def _payload_to_bits(self) -> np.ndarray:
        """将载荷转换为比特序列"""
        bits = []
        for byte in self.payload:
            for i in range(8):
                bits.append((byte >> i) & 1)
        return np.array(bits, dtype=np.float32)
    
    def embed(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        嵌入水印到图像 (LSB + 块平均值方法)
        使用不可见水印强度 (PSNR > 40 dB)

        Args:
            image: 输入图像 (H, W) 或 (H, W, C)
            strength: 水印强度 (1.0 = 不可见, 2.0 = 可见)

        Returns:
            带水印的图像
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            image = np.mean(image, axis=2)

        image = image.astype(np.uint8)
        h, w = image.shape

        # 获取比特序列
        bits = self._payload_to_bits()

        # 直接在空间域嵌入水印
        watermarked = image.astype(np.float32)
        bit_index = 0

        # 使用 8x8 块进行嵌入
        block_size = 8
        # 不可见水印强度: 1.0 对应 ±1 像素变化 (PSNR > 40 dB)
        delta_base = strength

        for i in range(0, h - block_size + 1, block_size):
            for j in range(0, w - block_size + 1, block_size):
                bit = int(bits[bit_index % len(bits)])
                # 获取块
                block = watermarked[i:i+block_size, j:j+block_size]

                # 根据比特值调整块的所有像素
                if bit == 1:
                    # 增加块的亮度
                    delta = delta_base
                else:
                    # 降低块的亮度
                    delta = -delta_base

                watermarked[i:i+block_size, j:j+block_size] = block + delta
                bit_index += 1

        # 裁剪到有效范围
        result = np.clip(watermarked, 0, 255)

        return result.astype(np.uint8)
    
    def _embed_in_subband(self, subband: np.ndarray, strength: float) -> np.ndarray:
        """在子带中嵌入水印"""
        h, w = subband.shape
        bits = self._payload_to_bits()

        # 计算子带的标准差用于自适应强度
        std_val = np.std(subband)
        adaptive_strength = strength * std_val if std_val > 0 else strength

        # 将比特序列重复平铺以覆盖整个子带
        bit_index = 0
        watermark = np.zeros_like(subband, dtype=np.float32)

        for i in range(h):
            for j in range(w):
                bit = bits[bit_index % len(bits)]
                # QIM 量化: 将比特映射到系数
                # 使用更强的信号: (2*bit - 1) 给出 -1 或 +1
                watermark[i, j] = (2 * bit - 1) * adaptive_strength
                bit_index += 1

        return subband + watermark


class WatermarkDetector:
    """水印检测器"""
    
    def __init__(self):
        """初始化水印检测器"""
        pass
    
    def detect(self, image: np.ndarray) -> dict:
        """
        检测并解码水印 (块差异方法)

        Args:
            image: 输入图像 (H, W) 或 (H, W, C)

        Returns:
            检测结果字典
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            image = np.mean(image, axis=2)

        image = image.astype(np.uint8)
        h, w = image.shape

        # 直接从空间域提取水印
        extracted_bits = []
        block_size = 8

        # 只提取前 256 个块（对应 256 比特 = 32 字节）
        block_count = 0
        max_blocks = 256

        # 第一遍：收集所有块的平均值
        block_means = []
        for i in range(0, h - block_size + 1, block_size):
            for j in range(0, w - block_size + 1, block_size):
                block = image[i:i+block_size, j:j+block_size]
                block_means.append(np.mean(block))
                if len(block_means) >= max_blocks:
                    break
            if len(block_means) >= max_blocks:
                break

        block_means = np.array(block_means[:max_blocks])

        # 使用中位数作为阈值（对异常值更鲁棒）
        global_threshold = np.median(block_means)

        # 第二遍：提取比特
        block_count = 0
        for i in range(0, h - block_size + 1, block_size):
            for j in range(0, w - block_size + 1, block_size):
                if block_count >= max_blocks:
                    break

                block = image[i:i+block_size, j:j+block_size]
                mean_val = np.mean(block)

                # 使用中位数阈值判断比特
                bit = 1 if mean_val > global_threshold else 0
                extracted_bits.append(bit)
                block_count += 1

            if block_count >= max_blocks:
                break

        # 确保有足够的比特
        while len(extracted_bits) < 256:
            extracted_bits.append(0)

        extracted_bits = np.array(extracted_bits[:256], dtype=np.int32)

        # 解码载荷
        payload = self._bits_to_payload(extracted_bits)

        # 解析设备 ID 和会话 ID
        device_id = payload[:16].rstrip(b'\x00').decode('utf-8', errors='ignore')
        session_id = payload[16:32].rstrip(b'\x00').decode('utf-8', errors='ignore')

        # 计算置信度
        confidence = self._calculate_confidence(extracted_bits)

        # 检测到水印的条件: 有效的设备 ID 且置信度足够高
        found = len(device_id) > 0 and confidence > 0.5

        return {
            'found': found,
            'device_id': device_id,
            'session_id': session_id,
            'confidence': confidence,
            'payload': payload.hex()
        }
    
    def _extract_from_subband(self, subband: np.ndarray) -> np.ndarray:
        """从子带中提取水印比特"""
        h, w = subband.shape
        bits = []

        # 计算子带的平均值作为阈值
        mean_val = np.mean(subband)

        for i in range(h):
            for j in range(w):
                # 软判决: 根据系数与平均值的关系判断比特
                bit = 1 if subband[i, j] > mean_val else 0
                bits.append(bit)

        return np.array(bits, dtype=np.int32)
    
    def _bits_to_payload(self, bits: np.ndarray) -> bytes:
        """将比特序列转换为载荷"""
        # 取前 256 比特 (32 bytes)
        bits = bits[:256]

        payload = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) < 8:
                byte_bits = np.pad(byte_bits, (0, 8-len(byte_bits)))

            byte_val = 0
            for j, bit in enumerate(byte_bits):
                byte_val |= (int(bit) << j)

            payload.append(byte_val)

        return bytes(payload)

    def _extract_with_voting(self, subband: np.ndarray, block_size: int = 8) -> np.ndarray:
        """使用分块投票的方式提取水印比特"""
        h, w = subband.shape
        bits = []

        # 计算子带的平均值作为阈值
        mean_val = np.mean(subband)

        # 分块处理，确保覆盖整个子带
        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                # 获取块 (可能不完整)
                block = subband[i:min(i+block_size, h), j:min(j+block_size, w)]
                # 计算块内大于平均值的像素比例
                ratio = np.sum(block > mean_val) / block.size
                # 投票: 如果大多数像素大于平均值，则为 1
                bit = 1 if ratio > 0.5 else 0
                bits.append(bit)

        # 确保有足够的比特 (至少 256 比特用于 32 字节载荷)
        while len(bits) < 256:
            bits.append(0)

        return np.array(bits[:256], dtype=np.int32)
    
    def _calculate_confidence(self, bits: np.ndarray) -> float:
        """计算检测置信度"""
        # 简单的置信度计算: 比特的一致性
        if len(bits) == 0:
            return 0.0
        
        # 计算多数比特
        majority = np.bincount(bits).argmax()
        consistency = np.sum(bits == majority) / len(bits)
        
        return float(consistency)

