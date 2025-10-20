"""
简单的 Flask 服务端 API
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
from pathlib import Path

app = Flask(__name__)

# 简单的内存数据存储
devices = {}  # device_id -> device_info
detections = {}  # detection_id -> detection_info
detection_counter = 0


@app.route('/v1/devices/enroll', methods=['POST'])
def enroll_device():
    """
    注册设备
    
    Request:
    {
        "device_id": "DEVICE-001",
        "device_name": "Monitor-1",
        "location": "Office-A"
    }
    """
    data = request.get_json()
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400
    
    devices[device_id] = {
        'device_id': device_id,
        'device_name': data.get('device_name', ''),
        'location': data.get('location', ''),
        'enrolled_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'message': 'Device enrolled successfully'
    }), 201


@app.route('/v1/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """获取设备信息"""
    if device_id not in devices:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify(devices[device_id]), 200


@app.route('/v1/sessions', methods=['POST'])
def create_session():
    """
    创建会话
    
    Request:
    {
        "device_id": "DEVICE-001",
        "session_name": "Session-1"
    }
    """
    data = request.get_json()
    device_id = data.get('device_id')
    
    if device_id not in devices:
        return jsonify({'error': 'Device not found'}), 404
    
    session_id = f"{device_id}-{datetime.now().timestamp()}"
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'device_id': device_id,
        'created_at': datetime.now().isoformat()
    }), 201


@app.route('/v1/detect', methods=['POST'])
def detect_watermark():
    """
    检测水印
    
    Request:
    {
        "device_id": "DEVICE-001",
        "session_id": "SESSION-001",
        "payload": "hex_string",
        "confidence": 0.95
    }
    """
    global detection_counter
    
    data = request.get_json()
    device_id = data.get('device_id')
    session_id = data.get('session_id')
    payload = data.get('payload')
    confidence = data.get('confidence', 0.0)
    
    if not device_id or not payload:
        return jsonify({'error': 'device_id and payload are required'}), 400
    
    detection_counter += 1
    detection_id = f"DET-{detection_counter:06d}"
    
    detection = {
        'detection_id': detection_id,
        'device_id': device_id,
        'session_id': session_id,
        'payload': payload,
        'confidence': confidence,
        'detected_at': datetime.now().isoformat(),
        'status': 'verified' if confidence > 0.8 else 'pending'
    }
    
    detections[detection_id] = detection
    
    return jsonify({
        'success': True,
        'detection_id': detection_id,
        'device_id': device_id,
        'confidence': confidence,
        'status': detection['status']
    }), 201


@app.route('/v1/detections/<detection_id>', methods=['GET'])
def get_detection(detection_id):
    """获取检测结果"""
    if detection_id not in detections:
        return jsonify({'error': 'Detection not found'}), 404
    
    return jsonify(detections[detection_id]), 200


@app.route('/v1/reports', methods=['POST'])
def generate_report():
    """
    生成溯源报告
    
    Request:
    {
        "detection_id": "DET-000001"
    }
    """
    data = request.get_json()
    detection_id = data.get('detection_id')
    
    if detection_id not in detections:
        return jsonify({'error': 'Detection not found'}), 404
    
    detection = detections[detection_id]
    device_id = detection['device_id']
    
    if device_id not in devices:
        return jsonify({'error': 'Device not found'}), 404
    
    device = devices[device_id]
    
    report = {
        'report_id': f"RPT-{detection_id}",
        'detection_id': detection_id,
        'device_id': device_id,
        'device_name': device['device_name'],
        'location': device['location'],
        'confidence': detection['confidence'],
        'detected_at': detection['detected_at'],
        'generated_at': datetime.now().isoformat(),
        'status': 'verified'
    }
    
    return jsonify(report), 201


@app.route('/v1/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'devices_count': len(devices),
        'detections_count': len(detections)
    }), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

