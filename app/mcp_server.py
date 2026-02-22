#!/usr/bin/env python3
"""Qwen3-ASR MCP Server — fastmcp based."""
import os, sys, time, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Optional
from fastmcp import FastMCP
from gpu_manager import gpu_manager

mcp = FastMCP("qwen3-asr")

SUPPORTED_LANGUAGES = [
    "Chinese","English","Cantonese","Arabic","German","French","Spanish","Portuguese",
    "Indonesian","Italian","Korean","Russian","Thai","Vietnamese","Japanese","Turkish",
    "Hindi","Malay","Dutch","Swedish","Danish","Finnish","Polish","Czech","Filipino",
    "Persian","Greek","Romanian","Hungarian","Macedonian",
]

def _get_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

# --- Core logic functions (testable) ---

def _transcribe(audio_path: str, language: str = "auto", model: str = "Qwen3-ASR-1.7B", return_timestamps: bool = False) -> dict:
    if not os.path.exists(audio_path):
        return {"status": "error", "error": f"File not found: {audio_path}"}
    try:
        loop = _get_loop()
        asr = loop.run_until_complete(gpu_manager.get_model(model))
        lang_arg = language if language.lower() != "auto" else None
        t0 = time.time()
        results = asr.transcribe(audio=audio_path, language=lang_arg, return_time_stamps=return_timestamps)
        t1 = time.time()
        r = results[0]
        resp = {"status": "success", "text": r.text, "language": r.language, "process_time": round(t1 - t0, 3)}
        if return_timestamps and r.time_stamps:
            resp["timestamps"] = [{"text": it.text, "start": it.start_time, "end": it.end_time} for it in r.time_stamps]
        return resp
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _get_status() -> dict:
    return gpu_manager.get_status()

def _get_languages() -> list:
    return SUPPORTED_LANGUAGES

def _gpu_offload() -> dict:
    loop = _get_loop()
    loop.run_until_complete(gpu_manager.offload())
    return {"status": "offloaded"}

# --- MCP tool wrappers ---

@mcp.tool()
def transcribe(audio_path: str, language: str = "auto", model: str = "Qwen3-ASR-1.7B", return_timestamps: bool = False) -> dict:
    """Transcribe audio file. Supports 52 languages/dialects."""
    return _transcribe(audio_path, language, model, return_timestamps)

@mcp.tool()
def get_status() -> dict:
    """Get service status including GPU info and loaded model."""
    return _get_status()

@mcp.tool()
def get_languages() -> list:
    """Get list of supported languages."""
    return _get_languages()

@mcp.tool()
def gpu_offload() -> dict:
    """Release GPU memory by unloading models."""
    return _gpu_offload()

if __name__ == "__main__":
    mcp.run()
