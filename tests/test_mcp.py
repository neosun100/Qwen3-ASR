"""MCP server tests for Qwen3-ASR."""
import os, sys, time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

@pytest.fixture(scope="module", autouse=True)
def patch_gpu():
    """Patch gpu_manager to avoid real model loading."""
    import gpu_manager as gm

    class FakeTimestamp:
        text = "hello"
        start_time = 0.0
        end_time = 0.5

    class FakeResult:
        text = "hello world"
        language = "English"
        time_stamps = [FakeTimestamp()]

    class FakeModel:
        def transcribe(self, audio, language=None, return_time_stamps=False):
            r = FakeResult()
            if not return_time_stamps:
                r.time_stamps = None
            return [r]

    original = gm.GPUManager.get_model
    async def mock_get(self, model_name="Qwen3-ASR-1.7B", dtype="bfloat16"):
        self.current_model_name = model_name
        self.last_used = time.time()
        self.asr_model = FakeModel()
        return self.asr_model
    gm.GPUManager.get_model = mock_get
    yield
    gm.GPUManager.get_model = original


def test_mcp_module_imports():
    import mcp_server
    assert hasattr(mcp_server, 'mcp')
    assert hasattr(mcp_server, '_transcribe')
    assert hasattr(mcp_server, '_get_status')
    assert hasattr(mcp_server, '_get_languages')
    assert hasattr(mcp_server, '_gpu_offload')

def test_get_languages():
    from mcp_server import _get_languages
    langs = _get_languages()
    assert isinstance(langs, list)
    assert "Chinese" in langs
    assert "English" in langs
    assert len(langs) == 30

def test_get_status():
    from mcp_server import _get_status
    s = _get_status()
    assert isinstance(s, dict)
    assert "model_loaded" in s
    assert "idle_timeout" in s

def test_gpu_offload():
    from mcp_server import _gpu_offload
    r = _gpu_offload()
    assert r["status"] == "offloaded"

def test_transcribe_file_not_found():
    from mcp_server import _transcribe
    r = _transcribe("/nonexistent/audio.wav")
    assert r["status"] == "error"
    assert "not found" in r["error"].lower()

def _make_wav(path, n=16000):
    import wave, struct
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack(f"<{n}h", *([0]*n)))

def test_transcribe_with_file(tmp_path):
    wav_path = str(tmp_path / "test.wav")
    _make_wav(wav_path)
    from mcp_server import _transcribe
    r = _transcribe(wav_path)
    assert r["status"] == "success"
    assert r["text"] == "hello world"
    assert r["language"] == "English"

def test_transcribe_with_timestamps(tmp_path):
    wav_path = str(tmp_path / "test.wav")
    _make_wav(wav_path)
    from mcp_server import _transcribe
    r = _transcribe(wav_path, return_timestamps=True)
    assert r["status"] == "success"
    assert "timestamps" in r

def test_transcribe_model_switch(tmp_path):
    wav_path = str(tmp_path / "test.wav")
    _make_wav(wav_path)
    from mcp_server import _transcribe
    r = _transcribe(wav_path, model="Qwen3-ASR-0.6B")
    assert r["status"] == "success"
