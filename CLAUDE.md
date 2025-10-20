# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-waterPrint is a screen watermarking and tracing system that embeds invisible digital watermarks into display output. The system consists of three major components:

1. **Overlay Service** - Embeds watermarks into screen output at the OS compositor level
2. **Detection SDK** - Detects and decodes watermarks from screenshots/recordings
3. **Management Service** - Manages devices, sessions, and generates tracing reports

## Quick Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Or use the automated setup with conda
bash quick_start.sh
```

### Running Tests
```bash
# End-to-end test (requires server running)
python test_e2e.py

# Start the Flask server first (in separate terminal)
python src/server.py
```

### Development Workflow
```bash
# Run simple demo
python screen_watermark_system.py

# Run realtime interactive demo
python screen_watermark_realtime.py --duration 60

# Run all tests
bash run_test.sh
```

## Architecture

### Core Algorithm Flow

**Embedding Pipeline:**
```
Device ID + Session ID → Payload (32 bytes)
  → Bit Encoding → Block-based Embedding (8×8 blocks)
  → Spatial Domain Modulation → Watermarked Image
```

**Detection Pipeline:**
```
Watermarked Image → Block Analysis (8×8 blocks)
  → Local Threshold Detection → Bit Extraction
  → Payload Reconstruction → Device/Session ID
```

### Key Modules

**[src/watermark_core.py](src/watermark_core.py)** - Core watermark algorithm
- `WatermarkEmbedder` - Embeds watermarks using spatial domain block encoding
  - Creates 32-byte payload from device_id (16 bytes) + session_id (16 bytes)
  - Embeds in 8×8 blocks by modulating block brightness
  - Strength parameter controls robustness vs. visibility tradeoff
- `WatermarkDetector` - Detects and decodes watermarks
  - Uses local adaptive thresholding to handle brightness variations
  - Extracts bits from 8×8 blocks using neighbor-based thresholds
  - Returns detection result with confidence score

**[src/server.py](src/server.py)** - Flask REST API server
- Device enrollment and management
- Session creation and tracking
- Detection result storage
- Tracing report generation
- In-memory storage (devices, detections dictionaries)

**[test_e2e.py](test_e2e.py)** - End-to-end testing
- Creates test images
- Tests embedding pipeline
- Tests detection pipeline
- Tests full API workflow
- Validates detection accuracy

## Technical Details

### Watermark Payload Structure
```
Total: 32 bytes
├─ device_id: 16 bytes (UTF-8 encoded, null-padded)
└─ session_id: 16 bytes (UTF-8 encoded, null-padded)
```

### Embedding Algorithm
- Uses spatial domain block-based encoding (not frequency domain DWT+DCT as described in design docs)
- 8×8 block size for bit encoding
- Each block encodes one bit by adjusting brightness:
  - Bit 1: Increase block brightness by +strength
  - Bit 0: Decrease block brightness by -strength
- Recommended strength: 2.0 (balance between robustness and visibility)

### Detection Algorithm
- Local adaptive thresholding approach
- For each 8×8 block:
  - Compute mean of neighboring blocks as threshold
  - Compare block mean to local threshold
  - Extract bit: 1 if above threshold, 0 otherwise
- Confidence based on bit consistency across image

### REST API Endpoints

**Device Management:**
- `POST /v1/devices/enroll` - Register new device
- `GET /v1/devices/{device_id}` - Get device info

**Session Management:**
- `POST /v1/sessions` - Create new session

**Detection:**
- `POST /v1/detect` - Submit detection result
- `GET /v1/detections/{detection_id}` - Query detection

**Reports:**
- `POST /v1/reports` - Generate tracing report
- `GET /v1/health` - Health check

## Important Implementation Notes

### Algorithm Simplification
The current implementation uses a **simplified spatial domain algorithm** for proof-of-concept purposes. The detailed design documents describe a more sophisticated frequency-domain approach (DWT+DCT+QIM) that is not yet implemented. Key differences:

**Current Implementation (watermark_core.py):**
- Direct spatial domain embedding in 8×8 blocks
- Simple brightness modulation
- Local threshold detection

**Design Specification (软件设计.md):**
- Frequency domain: 2-level DWT + DCT + QIM
- Sync templates with sinusoidal grids
- Multi-scale tiling at 64×64 and 128×128
- JND adaptive strength adjustment
- Blue noise dithering
- BCH/RS error correction
- AES-256-GCM encryption + HMAC-SHA256 signing

When implementing new features, refer to [软件设计.md](软件设计.md) for the full production-grade algorithm specifications.

### Key Parameters
- Default embedding strength: 2.0 (in watermark_core.py)
- Minimum confidence threshold: 0.5
- Block size: 8×8 pixels
- Image format: Grayscale (RGB averaged to grayscale)

## Development Guidelines

### When Adding Features
1. Read the design specifications in [软件设计.md](软件设计.md) for architectural guidance
2. The core algorithm is in [src/watermark_core.py](src/watermark_core.py)
3. API endpoints go in [src/server.py](src/server.py)
4. Add tests to [test_e2e.py](test_e2e.py)

### Testing Strategy
1. Start Flask server: `python src/server.py`
2. Run e2e test: `python test_e2e.py`
3. Verify all three stages pass:
   - Watermark embedding
   - Watermark detection
   - Server API workflow

### Performance Targets (from design docs)
- Detection success rate (TPR): ≥ 95%
- False positive rate (FPR): ≤ 10⁻⁶
- Equal error rate (EER): ≤ 2%
- Visibility (MOS): ≥ 4/5
- Client CPU usage: < 3%
- Client GPU usage: < 5%

## Documentation Index

Primary documentation (all in Chinese):
- [README.md](README.md) - Project overview and quick start
- [软件需求.md](软件需求.md) - Complete requirements specification
- [软件设计.md](软件设计.md) - Detailed architecture and design
- [架构图解.md](架构图解.md) - Architecture diagrams
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide with expected outputs
- [文档索引.md](文档索引.md) - Documentation navigation

## Common Patterns

### Creating a Watermark
```python
from watermark_core import WatermarkEmbedder

embedder = WatermarkEmbedder(
    device_id="DEVICE-001",
    session_id="SESSION-001"
)
watermarked_image = embedder.embed(image, strength=2.0)
```

### Detecting a Watermark
```python
from watermark_core import WatermarkDetector

detector = WatermarkDetector()
result = detector.detect(watermarked_image)
# result contains: found, device_id, session_id, confidence, payload
```

### API Usage
```python
import requests

# Enroll device
response = requests.post('http://127.0.0.1:5000/v1/devices/enroll', json={
    'device_id': 'DEVICE-001',
    'device_name': 'Monitor-1',
    'location': 'Office-A'
})

# Create session
response = requests.post('http://127.0.0.1:5000/v1/sessions', json={
    'device_id': 'DEVICE-001',
    'session_name': 'Session-1'
})

# Submit detection
response = requests.post('http://127.0.0.1:5000/v1/detect', json={
    'device_id': 'DEVICE-001',
    'session_id': 'SESSION-001',
    'payload': 'hex_string',
    'confidence': 0.95
})
```

## Dependencies

Core libraries (see [requirements.txt](requirements.txt)):
- numpy - Array operations
- scipy - Signal processing
- opencv-python - Image I/O and processing
- PyWavelets - Wavelet transforms (for future DWT implementation)
- Flask - REST API server
- requests - HTTP client
- pillow - Image handling
- mss - Screen capture
- pynput - Keyboard/mouse input
