"""Full API test suite for Qwen3-ASR server."""
import os, sys, io, json, wave, struct, time
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Generate a short test WAV in memory
def make_test_wav(duration=1.0, sr=16000):
    n = int(sr * duration)
    samples = [int(16000 * np.sin(2 * np.pi * 440 * i / sr)) for i in range(n)]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(struct.pack(f"<{n}h", *samples))
    buf.seek(0)
    return buf

@pytest.fixture(scope="module")
def client():
    """Create test client — imports server without loading GPU models."""
    # Patch gpu_manager to avoid real model loading
    import gpu_manager as gm

    class FakeTimestamp:
        def __init__(self):
            self.text = "hello"
            self.start_time = 0.0
            self.end_time = 0.5

    class FakeResult:
        def __init__(self):
            self.text = "hello world"
            self.language = "English"
            self.time_stamps = [FakeTimestamp()]

    class FakeModel:
        def transcribe(self, audio, language=None, return_time_stamps=False):
            r = FakeResult()
            if not return_time_stamps:
                r.time_stamps = None
            return [r]
        def init_streaming_state(self, **kw):
            return None

    original_get = gm.GPUManager.get_model
    async def mock_get(self, model_name="Qwen3-ASR-1.7B", dtype="bfloat16"):
        self.current_model_name = model_name
        self.last_used = time.time()
        self.asr_model = FakeModel()
        return self.asr_model
    gm.GPUManager.get_model = mock_get

    from fastapi.testclient import TestClient
    import server
    c = TestClient(server.app)
    yield c
    gm.GPUManager.get_model = original_get


# --- Health & Status ---

def test_health_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "healthy"
    assert "version" in d
    assert "model_loaded" in d

def test_status(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    d = r.json()
    assert "supported_languages" in d
    assert "dialects" in d
    assert "available_models" in d
    assert len(d["supported_languages"]) == 30
    assert len(d["available_models"]) == 2

def test_languages(client):
    r = client.get("/api/languages")
    assert r.status_code == 200
    d = r.json()
    assert "languages" in d
    assert "Chinese" in d["languages"]
    assert "English" in d["languages"]
    assert len(d["languages"]) == 30
    assert "dialects" in d


# --- Transcribe ---

def test_transcribe_basic(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe", files={"file": ("test.wav", wav, "audio/wav")})
    assert r.status_code == 200
    d = r.json()
    assert "text" in d
    assert "language" in d
    assert d["text"] == "hello world"
    assert d["language"] == "English"
    assert "process_time_seconds" in d
    assert "rtf" in d

def test_transcribe_with_language(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"language": "English"})
    assert r.status_code == 200
    assert r.json()["language"] == "English"

def test_transcribe_chinese(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"language": "Chinese"})
    assert r.status_code == 200

def test_transcribe_japanese(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"language": "Japanese"})
    assert r.status_code == 200

def test_transcribe_with_timestamps(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"return_timestamps": "true"})
    assert r.status_code == 200
    d = r.json()
    assert "timestamps" in d
    assert len(d["timestamps"]) > 0
    ts = d["timestamps"][0]
    assert "text" in ts
    assert "start" in ts
    assert "end" in ts

def test_transcribe_model_06b(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"model": "Qwen3-ASR-0.6B"})
    assert r.status_code == 200

def test_transcribe_model_17b(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"model": "Qwen3-ASR-1.7B"})
    assert r.status_code == 200

def test_transcribe_auto_language(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"language": "auto"})
    assert r.status_code == 200

def test_transcribe_response_headers(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe", files={"file": ("test.wav", wav, "audio/wav")})
    assert r.status_code == 200
    assert "x-time-load" in r.headers
    assert "x-time-process" in r.headers
    assert "x-time-total" in r.headers

def test_transcribe_dtype_float16(client):
    wav = make_test_wav()
    r = client.post("/api/transcribe",
        files={"file": ("test.wav", wav, "audio/wav")},
        data={"dtype": "float16"})
    assert r.status_code == 200


# --- Error handling ---

def test_transcribe_no_file(client):
    r = client.post("/api/transcribe")
    assert r.status_code == 422  # FastAPI validation error

def test_transcribe_invalid_format(client):
    r = client.post("/api/transcribe",
        files={"file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")})
    # Should still attempt (model handles errors)
    assert r.status_code in (200, 500)


# --- GPU offload ---

def test_gpu_offload(client):
    r = client.post("/api/gpu-offload")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "offloaded"

def test_gpu_offload_then_transcribe(client):
    """After offload, transcribe should auto-reload model."""
    client.post("/api/gpu-offload")
    wav = make_test_wav()
    r = client.post("/api/transcribe", files={"file": ("test.wav", wav, "audio/wav")})
    assert r.status_code == 200
    assert r.json()["text"] == "hello world"


# --- Swagger docs ---

def test_docs_accessible(client):
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()

def test_openapi_json(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    d = r.json()
    assert "paths" in d
    assert "/api/transcribe" in d["paths"]


# --- UI ---

def test_ui_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Qwen3-ASR" in r.text
    assert "data-i18n" in r.text  # i18n support


# --- CORS ---

def test_cors_headers(client):
    r = client.options("/api/transcribe", headers={
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 200
    assert "access-control-allow-origin" in r.headers


# --- Concurrent requests ---

def test_concurrent_requests(client):
    """Multiple requests should not deadlock."""
    import concurrent.futures
    def do_req():
        wav = make_test_wav()
        return client.post("/api/transcribe", files={"file": ("test.wav", wav, "audio/wav")}).status_code
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(lambda _: do_req(), range(3)))
    assert all(r == 200 for r in results)
