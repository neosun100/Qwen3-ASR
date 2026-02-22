#!/bin/bash
set -e

# Auto-select GPU with most free memory
GPU_ID=$(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | sort -t',' -k2 -rn | head -1 | cut -d',' -f1 | tr -d ' ')
export GPU_ID=${GPU_ID:-2}
echo "🚀 Using GPU $GPU_ID"

docker compose up -d --build
echo "✅ Qwen3-ASR running on http://0.0.0.0:8200 (GPU $GPU_ID)"
echo "   MCP server on port 8201"
echo "   API docs: http://0.0.0.0:8200/docs"
