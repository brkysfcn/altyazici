# -*- coding: utf-8 -*-
"""Modelleri onceden indirir (Kurulum.bat cagirir)."""
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cevir_core import MODEL_DIR, _nllb_hazirla, _spm_yolu, gpu_var_mi, gpu_bellek_mb


def main():
    from faster_whisper import WhisperModel
    gpu = gpu_var_mi()
    if gpu and gpu_bellek_mb() >= 3500:
        ad, cihaz, tur = "large-v3", "cuda", "int8_float16"
    else:
        ad, cihaz, tur = "medium", "cpu", "int8"
    print(f"Whisper modeli indiriliyor: {ad} (buyuk dosya, sabirli olun)...")
    WhisperModel(ad, device=cihaz, compute_type=tur, download_root=str(MODEL_DIR / "whisper"))
    print("Ceviri modeli (NLLB) indiriliyor...")
    _spm_yolu(_nllb_hazirla())
    print("Modeller hazir.")


if __name__ == "__main__":
    main()
