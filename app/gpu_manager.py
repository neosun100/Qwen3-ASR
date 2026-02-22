"""GPU resource manager with auto-offload for Qwen3-ASR models."""
import os, gc, time, asyncio, subprocess
from typing import Optional, Dict, Any

IDLE_TIMEOUT = int(os.environ.get("GPU_IDLE_TIMEOUT", "600"))

class GPUManager:
    def __init__(self):
        self.asr_model = None
        self.current_model_name: Optional[str] = None
        self.lock = asyncio.Lock()
        self.last_used: float = 0
        self._auto_task = None

    async def get_model(self, model_name: str, dtype: str = "bfloat16"):
        async with self.lock:
            if self.asr_model and self.current_model_name == model_name:
                self.last_used = time.time()
                return self.asr_model
            # unload old
            if self.asr_model:
                await self._offload_unlocked()
            # lazy load
            import torch
            from qwen_asr import Qwen3ASRModel
            dt = torch.bfloat16 if dtype == "bfloat16" else torch.float16
            aligner_path = os.environ.get("ALIGNER_PATH", "Qwen/Qwen3-ForcedAligner-0.6B")
            model_path = os.environ.get(f"MODEL_PATH_{model_name.replace('-','_').replace('.','_').upper()}",
                                        f"Qwen/{model_name}")
            self.asr_model = Qwen3ASRModel.from_pretrained(
                model_path, dtype=dt, device_map="cuda:0",
                max_inference_batch_size=32, max_new_tokens=512,
                forced_aligner=aligner_path,
                forced_aligner_kwargs=dict(dtype=dt, device_map="cuda:0"),
            )
            self.current_model_name = model_name
            self.last_used = time.time()
            return self.asr_model

    async def offload(self):
        async with self.lock:
            return await self._offload_unlocked()

    async def _offload_unlocked(self):
        if self.asr_model:
            del self.asr_model
            self.asr_model = None
            self.current_model_name = None
            gc.collect()
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass
        return True

    def get_status(self) -> Dict[str, Any]:
        status = {
            "model_loaded": self.current_model_name,
            "idle_seconds": int(time.time() - self.last_used) if self.last_used else 0,
            "idle_timeout": IDLE_TIMEOUT,
        }
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu",
                 "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                for line in r.stdout.strip().split("\n"):
                    p = [x.strip() for x in line.split(",")]
                    if len(p) >= 6:
                        status["gpu"] = {
                            "id": int(p[0]), "name": p[1],
                            "memory_used_mb": int(p[2]), "memory_total_mb": int(p[3]),
                            "utilization_percent": int(p[4]), "temperature_c": int(p[5]),
                        }
                        break
        except Exception:
            pass
        return status

    async def auto_offload_loop(self):
        while True:
            await asyncio.sleep(60)
            if self.asr_model and self.last_used and (time.time() - self.last_used) > IDLE_TIMEOUT:
                await self.offload()

gpu_manager = GPUManager()
