# Qwen3-ASR 一键部署开发任务

## 项目背景
阿里 Qwen3-ASR 是业界最强开源语音识别模型系列，支持 52 种语言/方言识别。
官方仓库只有 Gradio Demo 和 vLLM serve，没有生产级 UI、REST API 和 MCP。
我们要把它做成**生产级 All-in-One Docker 部署方案**。

## 参考项目（必须先读！）
- `~/upload/faster-whisper-web/` — **核心参考**，UI 结构、API 设计、GPU 管理、MCP 全部参考此项目
  - `app/server.py` — FastAPI 后端
  - `app/templates/index.html` — 暗色主题 UI
  - `app/gpu_manager.py` — GPU 显存管理
  - `app/mcp_server.py` — fastmcp MCP 服务
  - `Dockerfile` + `docker-compose.yml` + `start.sh`
- `~/upload/qwen3-tts/` — 另一个参考，UI 多语言切换、参数面板设计

## 原始项目代码
- `~/upload/Qwen3-ASR/` — 原始 Qwen3-ASR 代码
  - `qwen_asr/inference/qwen3_asr.py` — 核心推理（Qwen3ASRModel）
  - `qwen_asr/inference/qwen3_forced_aligner.py` — 时间戳对齐
  - `qwen_asr/cli/demo.py` — Gradio Demo（**不用 Gradio，参考其参数和逻辑**）
  - `examples/` — 使用示例（transformers + vLLM + streaming）

## 机器环境
- GPU: 4x NVIDIA L40S (46GB each)
- **使用 GPU 2**（最空闲，CUDA_VISIBLE_DEVICES=2）
- CUDA 12.x, nvidia-docker 已配置
- 端口: **8200**（主服务 UI+API）, **8201**（MCP）

## 核心交付物

### 1. 项目结构
```
~/upload/Qwen3-ASR/
├── app/
│   ├── server.py          ← FastAPI 后端（核心）
│   ├── templates/
│   │   └── index.html     ← 暗色主题 UI（纯 HTML/CSS/JS）
│   ├── gpu_manager.py     ← GPU 显存管理（空闲自动卸载）
│   └── mcp_server.py      ← fastmcp MCP 服务
├── tests/
│   ├── test_api.py        ← API 全覆盖测试
│   └── test_mcp.py        ← MCP 测试
├── Dockerfile             ← All-in-One（含三个模型）
├── docker-compose.yml
├── start.sh               ← 一键启动（自动选 GPU）
├── .env.example
└── .gitignore
```

### 2. UI 界面（最重要！要非常炫酷）

**⚠️ 绝对不用 Gradio！纯 HTML/CSS/JS 暗色主题。**

**必须参考 `~/upload/faster-whisper-web/app/templates/index.html` 的设计模式。**

功能要求：
- 🎤 **麦克风实时录音** + 📁 **文件上传**（拖拽 + 点击）
- 🌐 **52 语言选择下拉**（分组：常用 / 中文方言 / 其他）+ Auto 自动检测
- 📊 **模型切换**：1.7B / 0.6B 下拉选择
- ⏱️ **时间戳开关**：启用后显示时间戳可视化（参考原 Gradio demo 的可视化）
- 🔄 **流式识别开关**：启用后实时显示识别结果
- 📈 **性能面板**：处理时间 / 音频时长 / RTF(实时率) / GPU 显存
- 🖥️ **GPU 状态面板**：显存使用 + 模型状态 + 释放按钮
- 🌍 **多语言 UI**：右上角切换 EN/CN/TW/JP
- 🎨 **暗色主题**：深色背景 + 霓虹高亮 + 毛玻璃卡片
- 📱 **响应式**：移动端友好

### 3. API 接口（FastAPI）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | UI 页面 |
| `/health` | GET | 健康检查（版本+GPU+模型状态+队列） |
| `/api/status` | GET | 详细状态（GPU/模型/支持语言列表） |
| `/api/transcribe` | POST | **主功能**：语音识别 |
| `/api/transcribe/stream` | WebSocket | 流式识别 |
| `/api/languages` | GET | 支持语言列表 |
| `/api/gpu-offload` | POST | 释放 GPU 显存 |
| `/docs` | GET | Swagger 文档 |

**`/api/transcribe` 请求参数：**
- `file`: 音频文件（multipart/form-data）
- `language`: 语言代码（可选，默认 auto）
- `model`: 模型选择（qwen3-asr-1.7b / qwen3-asr-0.6b）
- `return_timestamps`: bool（需要 ForcedAligner）
- `dtype`: bfloat16 / float16

**响应：**
```json
{
  "text": "识别结果文本",
  "language": "Chinese",
  "timestamps": [...],  // 可选
  "duration_seconds": 5.2,
  "process_time_seconds": 0.8,
  "rtf": 0.15
}
```

**响应 Headers：** X-Time-Load, X-Time-Process, X-Time-Total

### 4. MCP 接口（fastmcp）

```python
from fastmcp import FastMCP
mcp = FastMCP("qwen3-asr")

@mcp.tool()
async def transcribe(audio_path: str, language: str = "auto", model: str = "qwen3-asr-1.7b", return_timestamps: bool = False) -> dict:
    """语音识别：支持52种语言"""
    ...

@mcp.tool()
async def get_status() -> dict:
    """获取服务状态"""
    ...

@mcp.tool()
async def get_languages() -> list:
    """获取支持的语言列表"""
    ...

@mcp.tool()
async def gpu_offload() -> dict:
    """释放GPU显存"""
    ...
```

### 5. Docker（All-in-One）

**基础镜像：** `nvidia/cuda:12.4.1-devel-ubuntu22.04`

**模型内嵌（运行时零下载）：**
- Qwen3-ASR-1.7B (~3.4G)
- Qwen3-ASR-0.6B (~1.2G)  
- Qwen3-ForcedAligner-0.6B (~1.2G)

**flash-attn：必须用预编译 wheel！**
```dockerfile
RUN pip install --no-cache-dir \
  "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.9cxx11abiTRUE-cp312-cp312-linux_x86_64.whl"
```
⚠️ 先确认容器内 Python/CUDA/PyTorch/ABI 版本再选正确的 wheel！

**docker-compose.yml 关键配置：**
```yaml
services:
  qwen3-asr:
    build: .
    ports:
      - "0.0.0.0:8200:8200"
      - "0.0.0.0:8201:8201"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["2"]
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=2
    restart: unless-stopped
```

**start.sh：**
```bash
#!/bin/bash
# 自动选最空闲 GPU
GPU_ID=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | sort -t',' -k2 -n | head -1 | cut -d',' -f1)
export NVIDIA_VISIBLE_DEVICES=$GPU_ID
docker compose up -d
```

### 6. 测试套件（与开发同等重要！）

参考 `~/upload/opus-smart-router/tests/test_e2e_full.py` 的测试深度。

**tests/test_api.py 必须覆盖：**
- /health 返回 200 + JSON（包含 model_loaded, gpu 信息）
- /api/status 返回完整状态
- /api/transcribe 正常识别（用测试音频）
- /api/transcribe 多语言（至少测 en, zh, ja）
- /api/transcribe 带时间戳
- /api/transcribe 不同模型（1.7B vs 0.6B）
- /api/transcribe 错误处理（无文件、无效格式、超大文件）
- /api/languages 返回语言列表
- /api/gpu-offload + 再识别（自动重载）
- /docs Swagger 可访问
- 并发请求不死锁
- CORS headers

**测试代码行数目标 ≥ 源码行数。**

## GPU 管理要求
- 模型懒加载（首次请求时才加载）
- 空闲超时自动卸载（默认 10 分钟）
- 手动释放按钮/API
- 模型切换时自动释放旧模型再加载新模型
- 显存使用实时监控

## 输出保障指令
- 你必须完成所有要求的工作，不得跳过或简化
- 每个功能都要实际实现并测试，不要写占位符代码
- UI 必须是纯 HTML/CSS/JS，绝对不用 Gradio
- 遇到问题记录并尝试解决，不跳过
- 完成后运行 pytest tests/ -v 全部通过
- flash-attn 必须用预编译 wheel，不源码编译
