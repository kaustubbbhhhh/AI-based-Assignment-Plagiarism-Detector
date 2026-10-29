"""
Model Manager.
Central lifecycle manager for neural models (CRAFT, TrOCR, GOT-OCR 2.0).
Provides singleton caching, lazy loading, FP16 execution, and GPU memory monitoring.
"""

import os
import gc
import logging
import threading
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized:
            return

        from ..config.config_loader import load_config
        self.config = config or load_config()

        # Model caches
        self._craft_detector = None
        self._trocr_processor = None
        self._trocr_model = None
        self._got_tokenizer = None
        self._got_model = None
        self._qwen_processor = None
        self._qwen_model = None

        # Device determination
        self._device = self._resolve_device()
        self._use_fp16 = self._device == "cuda"

        self._initialized = True
        logger.info(f"[MODEL_MANAGER] Initialized with primary device: {self._device} (FP16: {self._use_fp16})")

    def _resolve_device(self) -> str:
        """Resolve CUDA vs CPU device."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                logger.info(f"[MODEL_MANAGER] GPU Detected: {gpu_name} ({vram_gb:.2f} GB VRAM)")
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    @property
    def device(self) -> str:
        return self._device

    def get_vram_usage(self) -> Dict[str, float]:
        """Return allocated and reserved GPU memory in MB."""
        try:
            import torch
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(0) / (1024 ** 2)
                reserved = torch.cuda.memory_reserved(0) / (1024 ** 2)
                return {"allocated_mb": round(allocated, 2), "reserved_mb": round(reserved, 2)}
        except Exception:
            pass
        return {"allocated_mb": 0.0, "reserved_mb": 0.0}

    def clear_vram(self):
        """Force garbage collection and clear PyTorch CUDA memory cache."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                vram = self.get_vram_usage()
                logger.info(f"[MODEL_MANAGER] Cleared VRAM cache. Current allocated: {vram['allocated_mb']} MB")
        except Exception:
            pass

    # ── TrOCR Loader ──────────────────────────────────────────────────────────
    def get_trocr(self) -> Tuple[Any, Any]:
        """Lazy-loads and returns (processor, model) for TrOCR."""
        if self._trocr_model is not None and self._trocr_processor is not None:
            return self._trocr_processor, self._trocr_model

        with self._lock:
            if self._trocr_model is not None:
                return self._trocr_processor, self._trocr_model

            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            trocr_cfg = self.config.get("models", {}).get("trocr", {})
            model_path = trocr_cfg.get("model_path", "backend/models/trocr_finetuned")
            fallback_name = trocr_cfg.get("fallback_model", "microsoft/trocr-base-handwritten")

            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            abs_custom_path = os.path.join(workspace_root, model_path)

            if model_path.startswith("microsoft/"):
                logger.info(f"[TrOCR] Loading official HuggingFace checkpoint '{model_path}' on {self._device}...")
                target_path = model_path
            elif os.path.exists(abs_custom_path) and os.path.exists(os.path.join(abs_custom_path, "config.json")):
                logger.info(f"[TrOCR] Loading fine-tuned model from {abs_custom_path} on {self._device}...")
                target_path = abs_custom_path
            else:
                logger.info(f"[TrOCR] Loading base model '{fallback_name}' on {self._device}...")
                target_path = fallback_name

            try:
                self._trocr_processor = TrOCRProcessor.from_pretrained(target_path, local_files_only=True)
                self._trocr_model = VisionEncoderDecoderModel.from_pretrained(target_path, local_files_only=True)
            except Exception:
                logger.info(f"[TrOCR] Fetching from Hugging Face hub: {target_path}")
                self._trocr_processor = TrOCRProcessor.from_pretrained(target_path)
                self._trocr_model = VisionEncoderDecoderModel.from_pretrained(target_path)

            if self._use_fp16 and self._device == "cuda":
                self._trocr_model = self._trocr_model.half()

            self._trocr_model.to(self._device)
            self._trocr_model.eval()

            vram = self.get_vram_usage()
            logger.info(f"[TrOCR] Loaded successfully. VRAM: {vram['allocated_mb']} MB")
            return self._trocr_processor, self._trocr_model

    # ── GOT-OCR 2.0 Loader ───────────────────────────────────────────────────
    def get_got_ocr(self) -> Tuple[Any, Any]:
        """Lazy-loads and returns (tokenizer, model) for GOT-OCR 2.0."""
        if self._got_model is not None and self._got_tokenizer is not None:
            return self._got_tokenizer, self._got_model

        with self._lock:
            if self._got_model is not None:
                return self._got_tokenizer, self._got_model

            import torch
            from transformers import AutoTokenizer, AutoModel

            got_cfg = self.config.get("models", {}).get("got", {})
            model_name = got_cfg.get("model_name", "stepfun-ai/GOT-OCR2_0")

            logger.info(f"[GOT-OCR] Lazy-loading GOT-OCR 2.0 ('{model_name}') on {self._device}...")

            try:
                # Compatibility patch for transformers 5.x DynamicCache
                try:
                    from transformers.cache_utils import DynamicCache
                    if not hasattr(DynamicCache, "seen_tokens"):
                        DynamicCache.seen_tokens = property(lambda s: s.get_seq_length())
                    if not hasattr(DynamicCache, "get_max_length"):
                        DynamicCache.get_max_length = lambda s: None
                except Exception:
                    pass

                self._got_tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
                torch_dtype = torch.float16 if (self._use_fp16 and self._device == "cuda") else torch.float32

                self._got_model = AutoModel.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    torch_dtype=torch_dtype,
                    device_map="auto" if self._device == "cuda" else None,
                    low_cpu_mem_usage=True
                )
                if self._device != "cuda" or not hasattr(self._got_model, "hf_device_map"):
                    self._got_model.to(self._device)

                # Patch generate to set use_cache=False preventing SDPA dimension mismatch in transformers 5
                orig_gen = self._got_model.generate
                def safe_generate(*args, **kwargs):
                    kwargs["use_cache"] = False
                    return orig_gen(*args, **kwargs)
                self._got_model.generate = safe_generate

                self._got_model.eval()
                vram = self.get_vram_usage()
                logger.info(f"[GOT-OCR] Model loaded successfully. VRAM: {vram['allocated_mb']} MB")
            except Exception as e:
                logger.warning(f"[GOT-OCR] Failed to load full GOT-OCR weights ({e}). Initializing fallback engine.")
                self._got_tokenizer = None
                self._got_model = None

            return self._got_tokenizer, self._got_model

    def is_got_available(self) -> bool:
        """Check if GOT-OCR weights can be loaded."""
        got_cfg = self.config.get("models", {}).get("got", {})
        return got_cfg.get("enabled", True)

    # ── Qwen2-VL Loader ──────────────────────────────────────────────────────
    def _resolve_hf_snapshot(self, repo_id: str) -> str:
        """Resolve locally cached snapshot directory to prevent online network requests."""
        parts = repo_id.replace("/", "--")
        cache_dir = os.path.expanduser(f"~/.cache/huggingface/hub/models--{parts}/snapshots")
        if os.path.isdir(cache_dir):
            snapshots = [
                os.path.join(cache_dir, d)
                for d in os.listdir(cache_dir)
                if os.path.isdir(os.path.join(cache_dir, d))
            ]
            if snapshots:
                return sorted(snapshots, key=os.path.getmtime, reverse=True)[0]
        return repo_id

    def get_qwen2_vl(self) -> Tuple[Any, Any]:
        """Lazy-loads and returns (processor, model) for Qwen2-VL (4-bit quantized)."""
        if self._qwen_model is not None and self._qwen_processor is not None:
            return self._qwen_processor, self._qwen_model

        with self._lock:
            if self._qwen_model is not None:
                return self._qwen_processor, self._qwen_model

            import torch
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

            qwen_cfg = self.config.get("models", {}).get("qwen2_vl", {})
            model_id = qwen_cfg.get("model_id", "Qwen/Qwen2-VL-2B-Instruct")
            load_in_4bit = qwen_cfg.get("load_in_4bit", True)

            target_path = self._resolve_hf_snapshot(model_id)
            is_local = os.path.isdir(target_path)
            logger.info(f"[Qwen2-VL] Lazy-loading {target_path} (4-bit: {load_in_4bit}, local: {is_local}) on {self._device}...")

            try:
                self._qwen_processor = AutoProcessor.from_pretrained(
                    target_path,
                    min_pixels=256 * 28 * 28,
                    max_pixels=1024 * 28 * 28,
                    local_files_only=is_local
                )

                if load_in_4bit and self._device == "cuda":
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True
                    )
                    self._qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
                        target_path,
                        quantization_config=bnb_config,
                        device_map="auto",
                        torch_dtype=torch.float16,
                        local_files_only=is_local
                    )
                else:
                    self._qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
                        target_path,
                        device_map="auto" if self._device == "cuda" else None,
                        torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
                        local_files_only=is_local
                    )
                    if self._device != "cuda":
                        self._qwen_model.to(self._device)

                self._qwen_model.eval()
                vram = self.get_vram_usage()
                logger.info(f"[Qwen2-VL] Model loaded successfully. VRAM: {vram['allocated_mb']} MB")
            except Exception as e:
                logger.error(f"[Qwen2-VL] Failed to load Qwen2-VL ({e})")
                self._qwen_processor = None
                self._qwen_model = None

            return self._qwen_processor, self._qwen_model

    def is_qwen_available(self) -> bool:
        """Check if Qwen2-VL is enabled in config."""
        qwen_cfg = self.config.get("models", {}).get("qwen2_vl", {})
        return qwen_cfg.get("enabled", True)

