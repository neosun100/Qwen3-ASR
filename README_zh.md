[English](README.md) | [简体中文](README_zh.md) | [繁體中文](README_tw.md) | [日本語](README_jp.md)

# 🎙️ Qwen3-ASR Docker 一键部署

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/qwen3-asr)](https://hub.docker.com/r/neosun/qwen3-asr)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/Qwen3-ASR)](https://github.com/neosun100/Qwen3-ASR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

阿里通义千问 **Qwen3-ASR** 生产级 All-in-One Docker 部署方案 — 支持**52种语言/方言**识别、时间戳对齐、流式转录、暗色主题UI、REST API 和 MCP 集成。

![界面截图](assets/screenshot.png)

---

## ✨ 功能特性

- 🌐 **52种语言和方言** — 30种语言 + 22种中文方言，自动语言检测
- ⏱️ **强制对齐时间戳** — 基于 Qwen3-ForcedAligner-0.6B 的字/词级时间戳
- 🔄 **流式转录** — WebSocket 实时返回识别结果
- 🎨 **暗色主题 UI** — 毛玻璃设计，4语言国际化（中/英/繁/日），麦克风录音 + 文件上传
- 🚀 **GPU 智能管理** — 懒加载、空闲自动卸载、手动释放、模型切换
- 📡 **REST API** — FastAPI + Swagger 文档
- 🔌 **MCP 集成** — fastmcp 服务，4个工具，支持 AI Agent 调用
- 🐳 **All-in-One Docker** — 3个模型内嵌，运行时零下载
- 📊 **双模型** — Qwen3-ASR-1.7B（最高精度）和 Qwen3-ASR-0.6B（快速高效）

---

## 🚀 快速开始

### Docker 一行命令

```bash
docker run -d --gpus '"device=2"' --name qwen3-asr \
  -p 8250:8200 -p 8251:8201 \
  --restart unless-stopped \
  neosun/qwen3-asr:latest
```

访问 **http://localhost:8250** 打开界面，**http://localhost:8250/docs** 查看API文档。

### Docker Compose

```bash
git clone https://github.com/neosun100/Qwen3-ASR.git
cd Qwen3-ASR
bash start.sh  # 自动选择最空闲的GPU
```

---

## 📡 API 接口

| 端点 | 方法 | 说明 |
|---|---|---|
| `/` | GET | Web 界面 |
| `/health` | GET | 健康检查（版本、GPU、模型状态） |
| `/api/status` | GET | 详细状态（GPU、模型、支持语言列表） |
| `/api/transcribe` | POST | 语音识别（multipart/form-data） |
| `/api/transcribe/stream` | WebSocket | 流式识别 |
| `/api/languages` | GET | 支持语言列表 |
| `/api/gpu-offload` | POST | 释放GPU显存 |
| `/docs` | GET | Swagger API 文档 |

### 识别参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `file` | file | 必填 | 音频文件（WAV/MP3/FLAC/M4A/OGG） |
| `language` | string | `auto` | 语言名称或 `auto` 自动检测 |
| `model` | string | `Qwen3-ASR-1.7B` | `Qwen3-ASR-1.7B` 或 `Qwen3-ASR-0.6B` |
| `return_timestamps` | bool | `false` | 返回字/词级时间戳 |
| `dtype` | string | `bfloat16` | `bfloat16` 或 `float16` |

### 示例

```bash
curl -X POST http://localhost:8250/api/transcribe \
  -F 'file=@audio.wav' \
  -F 'language=auto' \
  -F 'model=Qwen3-ASR-1.7B' \
  -F 'return_timestamps=true'
```

```json
{
  "text": "你好世界",
  "language": "Chinese",
  "timestamps": [
    {"text": "你", "start": 0.0, "end": 0.3},
    {"text": "好", "start": 0.3, "end": 0.5},
    {"text": "世", "start": 0.5, "end": 0.8},
    {"text": "界", "start": 0.8, "end": 1.0}
  ],
  "duration_seconds": 1.0,
  "process_time_seconds": 0.15,
  "rtf": 0.15
}
```

---

## 🔌 MCP 集成

MCP 服务运行在 **8251** 端口。Claude Desktop / Cursor / Kiro 配置：

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

**可用工具：** `transcribe`、`get_status`、`get_languages`、`gpu_offload`

---

## 🏗️ 技术栈

| 组件 | 技术 |
|---|---|
| ASR 引擎 | Qwen3-ASR (0.6B / 1.7B) |
| 强制对齐器 | Qwen3-ForcedAligner-0.6B |
| 后端 | FastAPI + Uvicorn |
| 前端 | 纯 HTML/CSS/JS（无框架） |
| MCP 服务 | fastmcp |
| 容器 | NVIDIA CUDA 12.4 + Ubuntu 22.04 |
| GPU 管理 | 自动卸载、懒加载 |

---

## 📁 项目结构

```
app/
├── server.py              # FastAPI 后端
├── gpu_manager.py         # GPU 资源管理
├── mcp_server.py          # MCP 服务 (fastmcp)
└── templates/
    └── index.html         # 暗色主题 UI
tests/
├── test_api.py            # 22 个 API 测试
└── test_mcp.py            # 8 个 MCP 测试
Dockerfile                 # All-in-One 镜像
docker-compose.yml         # GPU + 健康检查
start.sh                   # 一键启动脚本
```

---

## ⚙️ 配置说明

| 变量 | 默认值 | 说明 |
|---|---|---|
| `GPU_ID` | `2` | GPU 设备 ID |
| `PORT` | `8200` | API 服务端口 |
| `MCP_PORT` | `8201` | MCP 服务端口 |
| `GPU_IDLE_TIMEOUT` | `600` | 自动卸载超时（秒） |

复制 `.env.example` 为 `.env` 并按需修改。

---

## 🌐 在线演示

**https://qwen3-asr.aws.xin**

---

## 📄 许可证

Apache-2.0。基于阿里通义千问团队的 [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)。

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/Qwen3-ASR&type=Date)](https://star-history.com/#neosun100/Qwen3-ASR&Date)
