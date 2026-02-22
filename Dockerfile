FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

# Add deadsnakes PPA for Python 3.12 on Ubuntu 22.04
RUN apt-get update && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3.12-venv \
    git git-lfs wget ffmpeg libsndfile1 sox ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.12 /usr/bin/python \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3

RUN git lfs install

WORKDIR /app

# Install base deps first (cache layer)
RUN pip3 install --no-cache-dir -U pip setuptools wheel

# Install qwen-asr + fastapi deps
# Remove system blinker first (conflicts with pip packages), then ensure pip still works
RUN dpkg --force-depends -r python3-blinker 2>/dev/null || true
COPY pyproject.toml README.md MANIFEST.in /src/
COPY qwen_asr/ /src/qwen_asr/
RUN pip3 install --no-cache-dir /src \
    && pip3 install --no-cache-dir fastapi uvicorn python-multipart fastmcp librosa

# Install flash-attn — CRITICAL: use prebuilt wheel or ninja-accelerated build
# PyTorch 2.10 + CUDA 12 + Python 3.12 + ABI=TRUE detected
# Latest prebuilt only goes to torch2.9, so we try:
# 1. Try torch2.9 wheel (often compatible with 2.10)
# 2. If that fails, ninja-accelerated source build (3-5 min vs 80 min without ninja)
# 3. If all fails, skip (PyTorch 2.2+ has built-in flash attention via SDPA)
RUN pip3 install --no-cache-dir ninja packaging psutil && \
    pip3 install --no-cache-dir \
    "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.9cxx11abiTRUE-cp312-cp312-linux_x86_64.whl" \
    2>/dev/null || \
    (echo "⚠️ Prebuilt wheel failed, trying ninja-accelerated source build..." && \
     MAX_JOBS=8 pip3 install --no-cache-dir flash-attn --no-build-isolation) || \
    echo "⚠️ flash-attn skipped — using PyTorch native SDPA (still works)"

# Download models (embedded in image — zero runtime download)
RUN python3 -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Qwen/Qwen3-ASR-1.7B', local_dir='/models/Qwen3-ASR-1.7B'); \
    snapshot_download('Qwen/Qwen3-ASR-0.6B', local_dir='/models/Qwen3-ASR-0.6B'); \
    snapshot_download('Qwen/Qwen3-ForcedAligner-0.6B', local_dir='/models/Qwen3-ForcedAligner-0.6B')"

# Copy app code
COPY app/ /app/

# Environment
ENV MODEL_PATH_QWEN3_ASR_1_7B=/models/Qwen3-ASR-1.7B
ENV MODEL_PATH_QWEN3_ASR_0_6B=/models/Qwen3-ASR-0.6B
ENV ALIGNER_PATH=/models/Qwen3-ForcedAligner-0.6B
ENV PORT=8200
ENV MCP_PORT=8201
ENV GPU_IDLE_TIMEOUT=600

EXPOSE 8200 8201

CMD ["sh", "-c", "python3 mcp_server.py & python3 -m uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
