[English](README.md) | [简体中文](README_zh.md) | [繁體中文](README_tw.md) | [日本語](README_jp.md)

# 🎙️ Qwen3-ASR Docker Deployment

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/qwen3-asr)](https://hub.docker.com/r/neosun/qwen3-asr)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/Qwen3-ASR)](https://github.com/neosun100/Qwen3-ASR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Production-ready All-in-One Docker deployment for **Qwen3-ASR** — Alibaba's state-of-the-art open-source ASR supporting **52 languages/dialects**, timestamps, streaming, dark-theme UI, REST API & MCP.

![UI Screenshot](assets/screenshot.png)

---

## ✨ Features

- 🌐 **52 Languages & Dialects** — 30 languages + 22 Chinese dialects, auto language detection
- ⏱️ **Forced Alignment Timestamps** — word/character level via Qwen3-ForcedAligner-0.6B
- 🔄 **Streaming Transcription** — real-time results via WebSocket
- 🎨 **Dark Theme UI** — glassmorphism design, 4-language i18n (EN/CN/TW/JP), mic recording + file upload
- 🚀 **GPU Management** — lazy loading, auto-offload after idle, manual release, model switching
- 📡 **REST API** — FastAPI with Swagger docs, OpenAPI schema
- 🔌 **MCP Integration** — fastmcp server with 4 tools for AI agent integration
- 🐳 **All-in-One Docker** — 3 models embedded, zero runtime download
- 📊 **Two Models** — Qwen3-ASR-1.7B (highest accuracy) and Qwen3-ASR-0.6B (fast & efficient)

---

## 🚀 Quick Start

### Docker One-Liner

```bash
docker run -d --gpus '"device=2"' --name qwen3-asr \
  -p 8250:8200 -p 8251:8201 \
  --restart unless-stopped \
  neosun/qwen3-asr:latest
```

Open **http://localhost:8250** for UI, **http://localhost:8250/docs** for API docs.

### Docker Compose

```bash
git clone https://github.com/neosun100/Qwen3-ASR.git
cd Qwen3-ASR
bash start.sh  # auto-selects freest GPU
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Web UI |
| `/health` | GET | Health check (version, GPU, model status) |
| `/api/status` | GET | Detailed status (GPU, models, supported languages) |
| `/api/transcribe` | POST | Speech recognition (multipart/form-data) |
| `/api/transcribe/stream` | WebSocket | Streaming transcription |
| `/api/languages` | GET | Supported languages list |
| `/api/gpu-offload` | POST | Release GPU memory |
| `/docs` | GET | Swagger API documentation |

### Transcribe Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `file` | file | required | Audio file (WAV/MP3/FLAC/M4A/OGG) |
| `language` | string | `auto` | Language name or `auto` |
| `model` | string | `Qwen3-ASR-1.7B` | `Qwen3-ASR-1.7B` or `Qwen3-ASR-0.6B` |
| `return_timestamps` | bool | `false` | Return word/char timestamps |
| `dtype` | string | `bfloat16` | `bfloat16` or `float16` |

### Example

```bash
curl -X POST http://localhost:8250/api/transcribe \
  -F 'file=@audio.wav' \
  -F 'language=auto' \
  -F 'model=Qwen3-ASR-1.7B' \
  -F 'return_timestamps=true'
```

```json
{
  "text": "Hello world",
  "language": "English",
  "timestamps": [
    {"text": "Hello", "start": 0.0, "end": 0.5},
    {"text": "world", "start": 0.5, "end": 1.0}
  ],
  "duration_seconds": 1.0,
  "process_time_seconds": 0.15,
  "rtf": 0.15
}
```

---

## 🔌 MCP Integration

MCP server runs on port **8251**. Config for Claude Desktop / Cursor / Kiro:

```json
{
  "mcpServers": {
    "qwen3-asr": {
      "command": "python",
      "args": ["app/mcp_server.py"],
      "env": {
        "MODEL_PATH_QWEN3_ASR_1_7B": "/models/Qwen3-ASR-1.7B"
      }
    }
  }
}
```

**Available Tools:** `transcribe`, `get_status`, `get_languages`, `gpu_offload`

---

## 🏗️ Tech Stack

| Component | Technology |
|---|---|
| ASR Engine | Qwen3-ASR (0.6B / 1.7B) |
| Forced Aligner | Qwen3-ForcedAligner-0.6B |
| Backend | FastAPI + Uvicorn |
| Frontend | Pure HTML/CSS/JS (no framework) |
| MCP Server | fastmcp |
| Container | NVIDIA CUDA 12.4 + Ubuntu 22.04 |
| GPU Mgmt | Auto-offload, lazy loading |

---

## 📁 Project Structure

```
app/
├── server.py              # FastAPI backend
├── gpu_manager.py         # GPU resource management
├── mcp_server.py          # MCP server (fastmcp)
└── templates/
    └── index.html         # Dark theme UI
tests/
├── test_api.py            # 22 API tests
└── test_mcp.py            # 8 MCP tests
Dockerfile                 # All-in-One image
docker-compose.yml         # GPU + health check
start.sh                   # One-click launcher
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `GPU_ID` | `2` | GPU device ID |
| `PORT` | `8200` | API server port |
| `MCP_PORT` | `8201` | MCP server port |
| `GPU_IDLE_TIMEOUT` | `600` | Auto-offload timeout (seconds) |

Copy `.env.example` to `.env` and edit as needed.

---

## 🌐 Online Demo

**https://qwen3-asr.aws.xin**

---

## 📄 License

Apache-2.0. Based on [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) by Alibaba Qwen Team.

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/Qwen3-ASR&type=Date)](https://star-history.com/#neosun100/Qwen3-ASR&Date)
