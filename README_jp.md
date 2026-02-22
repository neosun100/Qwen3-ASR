[English](README.md) | [简体中文](README_zh.md) | [繁體中文](README_tw.md) | [日本語](README_jp.md)

# 🎙️ Qwen3-ASR Docker デプロイ

[![Docker Pulls](https://img.shields.io/docker/pulls/neosun/qwen3-asr)](https://hub.docker.com/r/neosun/qwen3-asr)
[![GitHub Stars](https://img.shields.io/github/stars/neosun100/Qwen3-ASR)](https://github.com/neosun100/Qwen3-ASR)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Alibaba Qwen3-ASR のプロダクションレベル All-in-One Docker デプロイメント — **52言語・方言**対応、タイムスタンプ、ストリーミング、ダークテーマUI、REST API、MCP統合。

![UIスクリーンショット](assets/screenshot.png)

---

## ✨ 機能

- 🌐 **52言語・方言** — 30言語 + 22中国語方言、自動言語検出
- ⏱️ **強制アライメントタイムスタンプ** — Qwen3-ForcedAligner-0.6B による文字/単語レベル
- 🔄 **ストリーミング文字起こし** — WebSocket によるリアルタイム結果
- 🎨 **ダークテーマ UI** — グラスモーフィズムデザイン、4言語 i18n（英/中/繁/日）、マイク録音 + ファイルアップロード
- 🚀 **GPU管理** — 遅延ロード、アイドル時自動アンロード、手動解放、モデル切替
- 📡 **REST API** — FastAPI + Swagger ドキュメント
- 🔌 **MCP統合** — fastmcp サーバー、4ツール、AIエージェント連携
- 🐳 **All-in-One Docker** — 3モデル内蔵、ランタイムダウンロード不要
- 📊 **2モデル** — Qwen3-ASR-1.7B（最高精度）と Qwen3-ASR-0.6B（高速・効率的）

---

## 🚀 クイックスタート

### Docker ワンライナー

```bash
docker run -d --gpus '"device=2"' --name qwen3-asr \
  -p 8250:8200 -p 8251:8201 \
  --restart unless-stopped \
  neosun/qwen3-asr:latest
```

**http://localhost:8250** でUI、**http://localhost:8250/docs** でAPIドキュメントを開きます。

### Docker Compose

```bash
git clone https://github.com/neosun100/Qwen3-ASR.git
cd Qwen3-ASR
bash start.sh  # 最も空いているGPUを自動選択
```

---

## 📡 APIリファレンス

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/` | GET | Web UI |
| `/health` | GET | ヘルスチェック（バージョン、GPU、モデル状態） |
| `/api/status` | GET | 詳細ステータス（GPU、モデル、対応言語一覧） |
| `/api/transcribe` | POST | 音声認識（multipart/form-data） |
| `/api/transcribe/stream` | WebSocket | ストリーミング認識 |
| `/api/languages` | GET | 対応言語一覧 |
| `/api/gpu-offload` | POST | GPUメモリ解放 |
| `/docs` | GET | Swagger APIドキュメント |

### 認識パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `file` | file | 必須 | 音声ファイル（WAV/MP3/FLAC/M4A/OGG） |
| `language` | string | `auto` | 言語名または `auto` |
| `model` | string | `Qwen3-ASR-1.7B` | `Qwen3-ASR-1.7B` または `Qwen3-ASR-0.6B` |
| `return_timestamps` | bool | `false` | 文字/単語レベルタイムスタンプを返す |
| `dtype` | string | `bfloat16` | `bfloat16` または `float16` |

### 使用例

```bash
curl -X POST http://localhost:8250/api/transcribe \
  -F 'file=@audio.wav' \
  -F 'language=auto' \
  -F 'model=Qwen3-ASR-1.7B' \
  -F 'return_timestamps=true'
```

```json
{
  "text": "こんにちは世界",
  "language": "Japanese",
  "timestamps": [
    {"text": "こんにちは", "start": 0.0, "end": 0.6},
    {"text": "世界", "start": 0.6, "end": 1.0}
  ],
  "duration_seconds": 1.0,
  "process_time_seconds": 0.15,
  "rtf": 0.15
}
```

---

## 🔌 MCP統合

MCPサーバーはポート **8251** で動作。Claude Desktop / Cursor / Kiro 設定：

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

**利用可能なツール：** `transcribe`、`get_status`、`get_languages`、`gpu_offload`

---

## 🏗️ 技術スタック

| コンポーネント | 技術 |
|---|---|
| ASRエンジン | Qwen3-ASR (0.6B / 1.7B) |
| 強制アライナー | Qwen3-ForcedAligner-0.6B |
| バックエンド | FastAPI + Uvicorn |
| フロントエンド | 純粋 HTML/CSS/JS（フレームワーク不使用） |
| MCPサーバー | fastmcp |
| コンテナ | NVIDIA CUDA 12.4 + Ubuntu 22.04 |
| GPU管理 | 自動アンロード、遅延ロード |

---

## 📁 プロジェクト構成

```
app/
├── server.py              # FastAPI バックエンド
├── gpu_manager.py         # GPUリソース管理
├── mcp_server.py          # MCPサーバー (fastmcp)
└── templates/
    └── index.html         # ダークテーマ UI
tests/
├── test_api.py            # 22 APIテスト
└── test_mcp.py            # 8 MCPテスト
Dockerfile                 # All-in-One イメージ
docker-compose.yml         # GPU + ヘルスチェック
start.sh                   # ワンクリック起動
```

---

## ⚙️ 設定

| 変数 | デフォルト | 説明 |
|---|---|---|
| `GPU_ID` | `2` | GPUデバイスID |
| `PORT` | `8200` | APIサーバーポート |
| `MCP_PORT` | `8201` | MCPサーバーポート |
| `GPU_IDLE_TIMEOUT` | `600` | 自動アンロードタイムアウト（秒） |

`.env.example` を `.env` にコピーして編集してください。

---

## 🌐 オンラインデモ

**https://qwen3-asr.aws.xin**

---

## 📄 ライセンス

Apache-2.0。Alibaba Qwen チームの [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) に基づいています。

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/Qwen3-ASR&type=Date)](https://star-history.com/#neosun100/Qwen3-ASR&Date)
