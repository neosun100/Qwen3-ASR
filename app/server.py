"""FastAPI server for Qwen3-ASR — UI + REST API."""
import os, sys, time, uuid, asyncio, json
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import numpy as np

from gpu_manager import gpu_manager

SUPPORTED_LANGUAGES = [
    "Chinese","English","Cantonese","Arabic","German","French","Spanish","Portuguese",
    "Indonesian","Italian","Korean","Russian","Thai","Vietnamese","Japanese","Turkish",
    "Hindi","Malay","Dutch","Swedish","Danish","Finnish","Polish","Czech","Filipino",
    "Persian","Greek","Romanian","Hungarian","Macedonian",
]
DIALECTS = [
    "Anhui","Dongbei","Fujian","Gansu","Guizhou","Hebei","Henan","Hubei","Hunan",
    "Jiangxi","Ningxia","Shandong","Shaanxi","Shanxi","Sichuan","Tianjin","Yunnan",
    "Zhejiang","Cantonese (Hong Kong)","Cantonese (Guangdong)","Wu","Minnan",
]
MODELS = ["Qwen3-ASR-1.7B", "Qwen3-ASR-0.6B"]

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(gpu_manager.auto_offload_loop())
    yield
    task.cancel()

app = FastAPI(title="Qwen3-ASR", description="Production ASR service with 52-language support", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/", response_class=HTMLResponse)
async def index():
    p = Path(__file__).parent / "templates" / "index.html"
    return p.read_text(encoding="utf-8") if p.exists() else "<h1>Qwen3-ASR</h1><p><a href='/docs'>API Docs</a></p>"


@app.get("/health")
async def health():
    s = gpu_manager.get_status()
    return {"status": "healthy", "version": "1.0.0", "model_loaded": s["model_loaded"], **s}


@app.get("/api/status")
async def api_status():
    s = gpu_manager.get_status()
    return {**s, "supported_languages": SUPPORTED_LANGUAGES, "dialects": DIALECTS, "available_models": MODELS}


@app.get("/api/languages")
async def api_languages():
    return {"languages": SUPPORTED_LANGUAGES, "dialects": DIALECTS}


@app.post("/api/transcribe")
async def api_transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    model: str = Form("Qwen3-ASR-1.7B"),
    return_timestamps: bool = Form(False),
    dtype: str = Form("bfloat16"),
):
    t0 = time.time()
    tmp = f"/tmp/qwen_asr_{uuid.uuid4()}{Path(file.filename or 'a.wav').suffix}"
    try:
        content = await file.read()
        if len(content) > 200 * 1024 * 1024:
            return JSONResponse({"error": "File too large (max 200MB)"}, status_code=413)
        with open(tmp, "wb") as f:
            f.write(content)

        t_load_start = time.time()
        asr = await gpu_manager.get_model(model, dtype)
        t_load = time.time() - t_load_start

        lang_arg = language if language and language.lower() != "auto" else None
        t_proc_start = time.time()
        results = asr.transcribe(
            audio=tmp,
            language=lang_arg,
            return_time_stamps=return_timestamps,
        )
        t_proc = time.time() - t_proc_start
        r = results[0]

        # compute audio duration
        try:
            import librosa
            dur = librosa.get_duration(filename=tmp)
        except Exception:
            dur = 0.0

        t_total = time.time() - t0
        resp = {
            "text": r.text,
            "language": r.language,
            "duration_seconds": round(dur, 2),
            "process_time_seconds": round(t_proc, 3),
            "rtf": round(t_proc / dur, 4) if dur > 0 else 0,
        }
        if return_timestamps and r.time_stamps:
            resp["timestamps"] = [{"text": it.text, "start": it.start_time, "end": it.end_time} for it in r.time_stamps]

        headers = {
            "X-Time-Load": f"{t_load:.3f}",
            "X-Time-Process": f"{t_proc:.3f}",
            "X-Time-Total": f"{t_total:.3f}",
        }
        return JSONResponse(resp, headers=headers)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


@app.websocket("/api/transcribe/stream")
async def ws_stream(ws: WebSocket):
    await ws.accept()
    try:
        # receive config
        cfg = await ws.receive_json()
        model_name = cfg.get("model", "Qwen3-ASR-1.7B")
        dtype = cfg.get("dtype", "bfloat16")
        language = cfg.get("language")

        asr = await gpu_manager.get_model(model_name, dtype)
        if not hasattr(asr, 'init_streaming_state'):
            await ws.send_json({"error": "Streaming not supported with transformers backend"})
            await ws.close()
            return

        lang_arg = language if language and language.lower() != "auto" else None
        state = asr.init_streaming_state(language=lang_arg)

        await ws.send_json({"type": "ready"})

        while True:
            data = await ws.receive_bytes()
            if not data:
                break
            pcm = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            state = asr.streaming_transcribe(pcm, state)
            await ws.send_json({"type": "partial", "text": state.text if hasattr(state, 'text') else ""})

        state = asr.finish_streaming_transcribe(state)
        await ws.send_json({"type": "final", "text": state.text if hasattr(state, 'text') else "", "language": state.language if hasattr(state, 'language') else ""})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass


@app.post("/api/gpu-offload")
async def gpu_offload():
    await gpu_manager.offload()
    return {"status": "offloaded", **gpu_manager.get_status()}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8200"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=1)
