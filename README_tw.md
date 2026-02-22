[English](README.md) | [简体中文](README_zh.md) | [繁體中文](README_tw.md) | [日本語](README_jp.md)

# 🎙️ Qwen3-ASR Docker 一鍵部署

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/qwen3-asr)](https://hub.docker.com/r/neosun/qwen3-asr)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/Qwen3-ASR)](https://github.com/neosun100/Qwen3-ASR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

阿里通義千問 **Qwen3-ASR** 生產級 All-in-One Docker 部署方案 — 支援**52種語言/方言**識別、時間戳對齊、串流轉錄、暗色主題UI、REST API 和 MCP 整合。

![介面截圖](assets/screenshot.png)

---

## ✨ 功能特色

- 🌐 **52種語言和方言** — 30種語言 + 22種中文方言，自動語言偵測
- ⏱️ **強制對齊時間戳** — 基於 Qwen3-ForcedAligner-0.6B 的字/詞級時間戳
- 🔄 **串流轉錄** — WebSocket 即時回傳識別結果
- 🎨 **暗色主題 UI** — 毛玻璃設計，4語言國際化（中/英/繁/日），麥克風錄音 + 檔案上傳
- 🚀 **GPU 智慧管理** — 懶載入、閒置自動卸載、手動釋放、模型切換
- 📡 **REST API** — FastAPI + Swagger 文件
- 🔌 **MCP 整合** — fastmcp 服務，4個工具，支援 AI Agent 呼叫
- 🐳 **All-in-One Docker** — 3個模型內嵌，執行時零下載
- 📊 **雙模型** — Qwen3-ASR-1.7B（最高精度）和 Qwen3-ASR-0.6B（快速高效）

---

## 🚀 快速開始

### Docker 一行指令

```bash
docker run -d --gpus '"device=2"' --name qwen3-asr \
  -p 8250:8200 -p 8251:8201 \
  --restart unless-stopped \
  neosun/qwen3-asr:latest
```

開啟 **http://localhost:8250** 進入介面，**http://localhost:8250/docs** 查看API文件。

### Docker Compose

```bash
git clone https://github.com/neosun100/Qwen3-ASR.git
cd Qwen3-ASR
bash start.sh  # 自動選擇最空閒的GPU
```

---

## 📡 API 介面

| 端點 | 方法 | 說明 |
|---|---|---|
| `/` | GET | Web 介面 |
| `/health` | GET | 健康檢查（版本、GPU、模型狀態） |
| `/api/status` | GET | 詳細狀態（GPU、模型、支援語言列表） |
| `/api/transcribe` | POST | 語音識別（multipart/form-data） |
| `/api/transcribe/stream` | WebSocket | 串流識別 |
| `/api/languages` | GET | 支援語言列表 |
| `/api/gpu-offload` | POST | 釋放GPU記憶體 |
| `/docs` | GET | Swagger API 文件 |

### 識別參數

| 參數 | 類型 | 預設值 | 說明 |
|---|---|---|---|
| `file` | file | 必填 | 音訊檔案（WAV/MP3/FLAC/M4A/OGG） |
| `language` | string | `auto` | 語言名稱或 `auto` 自動偵測 |
| `model` | string | `Qwen3-ASR-1.7B` | `Qwen3-ASR-1.7B` 或 `Qwen3-ASR-0.6B` |
| `return_timestamps` | bool | `false` | 回傳字/詞級時間戳 |
| `dtype` | string | `bfloat16` | `bfloat16` 或 `float16` |

### 範例

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

## 🔌 MCP 整合

MCP 服務執行於 **8251** 連接埠。Claude Desktop / Cursor / Kiro 設定：

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

## 🏗️ 技術棧

| 元件 | 技術 |
|---|---|
| ASR 引擎 | Qwen3-ASR (0.6B / 1.7B) |
| 強制對齊器 | Qwen3-ForcedAligner-0.6B |
| 後端 | FastAPI + Uvicorn |
| 前端 | 純 HTML/CSS/JS（無框架） |
| MCP 服務 | fastmcp |
| 容器 | NVIDIA CUDA 12.4 + Ubuntu 22.04 |
| GPU 管理 | 自動卸載、懶載入 |

---

## 📁 專案結構

```
app/
├── server.py              # FastAPI 後端
├── gpu_manager.py         # GPU 資源管理
├── mcp_server.py          # MCP 服務 (fastmcp)
└── templates/
    └── index.html         # 暗色主題 UI
tests/
├── test_api.py            # 22 個 API 測試
└── test_mcp.py            # 8 個 MCP 測試
Dockerfile                 # All-in-One 映像
docker-compose.yml         # GPU + 健康檢查
start.sh                   # 一鍵啟動腳本
```

---

## ⚙️ 設定說明

| 變數 | 預設值 | 說明 |
|---|---|---|
| `GPU_ID` | `2` | GPU 裝置 ID |
| `PORT` | `8200` | API 服務連接埠 |
| `MCP_PORT` | `8201` | MCP 服務連接埠 |
| `GPU_IDLE_TIMEOUT` | `600` | 自動卸載逾時（秒） |

複製 `.env.example` 為 `.env` 並按需修改。

---

## 🌐 線上演示

**https://qwen3-asr.aws.xin**

---

## 📄 授權

Apache-2.0。基於阿里通義千問團隊的 [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)。

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/Qwen3-ASR&type=Date)](https://star-history.com/#neosun100/Qwen3-ASR&Date)
