# -*- coding: utf-8 -*-
"""Gunluk (log) ve sorun raporu.

- loglar\\altyazici.log : donen dosya (1 MB x 4), her calistirmada sistem bilgisi basligi
- rapor_olustur()      : loglar + sistem bilgisi + ayarlar -> Masaustune zip (video icermez)
Yalnizca standart kutuphane kullanir; baska modullerden once guvenle import edilebilir.
"""
import ctypes
import io
import logging
import logging.handlers
import os
import platform
import shutil
import subprocess
import sys
import threading
import traceback
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "loglar"
LOG_FILE = LOG_DIR / "altyazici.log"
AD = "altyazici"
_kuruldu = False
_baslik_yazildi = False


def log():
    return logging.getLogger(AD)


class _Akim:
    """pythonw'de stdout/stderr None olur; yazmaya calisan kutuphaneler
    ("'NoneType' object has no attribute 'write'") coker. Bunun yerine gunluge yazar."""
    encoding = "utf-8"
    errors = "replace"

    def __init__(self, seviye):
        self.seviye = seviye
        self._tampon = ""

    def write(self, veri):
        if not isinstance(veri, str):
            veri = str(veri)
        self._tampon += veri.replace("\r", "\n")
        *satirlar, self._tampon = self._tampon.split("\n")
        for satir in satirlar:
            satir = satir.strip()
            if satir and "%|" not in satir:  # ilerleme cubugu satirlari atlanir
                log().log(self.seviye, "[cikti] %s", satir)
        return len(veri)

    def flush(self):
        pass

    def isatty(self):
        return False

    def writable(self):
        return True

    def fileno(self):
        raise io.UnsupportedOperation("fileno")


def _akimlari_duzelt():
    if sys.stdout is None:
        sys.stdout = _Akim(logging.INFO)
    if sys.stderr is None:
        sys.stderr = _Akim(logging.WARNING)
    # Calisma sirasinda HF ilerleme cubuklari gereksiz; kurulum (modelleri_indir) bunu cagirmaz.
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")


def kur():
    """Dosyaya yazan gunlugu bir kez kurar; yakalanmayan hatalari da kaydeder."""
    global _kuruldu
    _akimlari_duzelt()
    if _kuruldu:
        return
    _kuruldu = True
    try:
        LOG_DIR.mkdir(exist_ok=True)
        h = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s",
                                         "%Y-%m-%d %H:%M:%S"))
        for ad in (AD, "faster_whisper", "huggingface_hub", "ctranslate2"):
            lg = logging.getLogger(ad)
            lg.setLevel(logging.INFO)
            lg.addHandler(h)
        logging.getLogger(AD).propagate = False
    except Exception:
        return  # gunluk acilamasa program yine de calissin

    def _yakalanmayan(tip, deger, tb):
        log().critical("Yakalanmayan hata:\n%s", "".join(traceback.format_exception(tip, deger, tb)))
        sys.__excepthook__(tip, deger, tb)

    def _thread_hata(args):
        log().critical("Thread hatasi (%s):\n%s", getattr(args.thread, "name", "?"),
                       "".join(traceback.format_exception(args.exc_type, args.exc_value,
                                                          args.exc_traceback)))

    sys.excepthook = _yakalanmayan
    threading.excepthook = _thread_hata


# ---------------------------------------------------------------- yt-dlp koprusu
class YtdlpGunluk:
    """yt-dlp'nin kendi mesajlarini (uyari/hata/ayrinti) gunluge yazar, ekrana basmaz."""
    def debug(self, m):
        # "[debug]" satirlari site/ayristirici sorunlarini teshis etmek icin degerlidir
        if m.startswith("[debug]"):
            log().info("[yt-dlp] %s", m)

    def info(self, m):
        log().info("[yt-dlp] %s", m)

    def warning(self, m):
        log().warning("[yt-dlp] %s", m)

    def error(self, m):
        log().error("[yt-dlp] %s", m)


# ---------------------------------------------------------------- sistem bilgisi
def _surum(paket):
    try:
        from importlib.metadata import version
        return version(paket)
    except Exception:
        return "yuklu degil"


def _komut(args, zaman=8):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=zaman,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return (r.stdout or r.stderr).strip()
    except Exception as ex:
        return f"alinamadi ({type(ex).__name__})"


def _ram_gb():
    try:
        class MS(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong),
                        ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                        ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong),
                        ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                        ("ae", ctypes.c_ulonglong)]
        ms = MS()
        ms.l = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
        return f"{ms.tp / 2**30:.1f} GB toplam, {ms.ap / 2**30:.1f} GB bos"
    except Exception:
        return "alinamadi"


def _boyut_mb(yol):
    try:
        t = sum(f.stat().st_size for f in Path(yol).rglob("*") if f.is_file())
        return f"{t / 2**20:.0f} MB"
    except Exception:
        return "?"


def sistem_bilgisi():
    k = []
    ekle = k.append
    try:
        surum = (ROOT / "surum.txt").read_text(encoding="utf-8").strip()
    except Exception:
        surum = "?"
    ekle(f"Altyazici surumu : {surum}")
    ekle(f"Tarih/saat       : {datetime.now():%Y-%m-%d %H:%M:%S}")
    ekle(f"Windows          : {platform.platform()}")
    ekle(f"Python           : {sys.version.split()[0]} ({sys.executable})")
    ekle(f"Islemci          : {platform.processor() or platform.machine()}")
    ekle(f"RAM              : {_ram_gb()}")
    try:
        d = shutil.disk_usage(ROOT)
        ekle(f"Disk (program)   : {d.free / 2**30:.1f} GB bos / {d.total / 2**30:.0f} GB")
    except Exception:
        pass
    gpu = _komut(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                  "--format=csv,noheader"])
    ekle(f"NVIDIA ekran karti: {gpu}")
    try:
        import ctranslate2
        ekle(f"CUDA cihaz sayisi: {ctranslate2.get_cuda_device_count()}")
    except Exception as ex:
        ekle(f"CUDA cihaz sayisi: alinamadi ({type(ex).__name__})")
    ff = ROOT / "araclar" / "ffmpeg.exe"
    ekle("FFmpeg           : " + (_komut([str(ff), "-version"]).splitlines()[0] if ff.exists()
                                  else "YOK (araclar\\ffmpeg.exe bulunamadi)"))
    ekle("Kutuphaneler     : " + ", ".join(
        f"{p} {_surum(p)}" for p in ("yt-dlp", "faster-whisper", "ctranslate2",
                                      "sentencepiece", "huggingface-hub", "deep-translator", "av")))
    ekle(f"uv               : {_komut(['uv', '--version'])}")
    ekle(f"uv'yi biz kurduk mu: {'evet' if (ROOT / 'uv_kuruldu.txt').exists() else 'hayir/bilinmiyor'}")
    ekle(f"Program klasoru  : {ROOT}")
    for ad in ("modeller", ".venv", "araclar"):
        p = ROOT / ad
        ekle(f"  {ad:<10}: " + (_boyut_mb(p) if p.exists() else "YOK"))
    for ad in sorted(p.name for p in (ROOT / "modeller").glob("*")) if (ROOT / "modeller").exists() else []:
        ekle(f"    modeller/{ad}: {_boyut_mb(ROOT / 'modeller' / ad)}")
    ekle(f"Ortam            : UV_PYTHON={os.environ.get('UV_PYTHON')}, "
         f"UV_PYTHON_PREFERENCE={os.environ.get('UV_PYTHON_PREFERENCE')}")
    try:
        ekle("Ayarlar          : " + (ROOT / "ayarlar.json").read_text(encoding="utf-8").replace("\n", " "))
    except Exception:
        ekle("Ayarlar          : (yok)")
    return "\n".join(k)


def oturum_basligi():
    """Her program acilisinda (surec basina bir kez) gunluge sistem bilgisini yazar."""
    global _baslik_yazildi
    if _baslik_yazildi:
        return
    _baslik_yazildi = True
    try:
        log().info("=" * 70)
        log().info("PROGRAM ACILDI\n%s", sistem_bilgisi())
        log().info("=" * 70)
    except Exception:
        pass


# ---------------------------------------------------------------- rapor
def _gizle(metin):
    """Kullanici adini rapordan cikarir: C:\\Users\\ad -> %USERPROFILE%"""
    for yol in {os.environ.get("USERPROFILE", ""), str(Path.home())}:
        if yol:
            metin = metin.replace(yol, "%USERPROFILE%").replace(yol.replace("\\", "/"), "%USERPROFILE%")
    return metin


def rapor_olustur():
    """Masaustune Altyazici-rapor-<tarih>.zip yazar ve yolunu dondurur."""
    masaustu = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    if not masaustu.exists():
        masaustu = ROOT
    zip_yolu = masaustu / f"Altyazici-rapor-{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(zip_yolu, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("sistem_bilgisi.txt", _gizle(sistem_bilgisi()))
        if LOG_DIR.exists():
            for f in sorted(LOG_DIR.glob("*")):
                if f.is_file():
                    try:
                        z.writestr(f"loglar/{f.name}", _gizle(
                            f.read_text(encoding="utf-8", errors="replace")))
                    except Exception as ex:
                        z.writestr(f"loglar/{f.name}.okunamadi.txt", str(ex))
        z.writestr("NOT.txt", "Bu rapor video dosyasi icermez; indirdiginiz video linklerini ve "
                              "basliklarini icerebilir. Kullanici adiniz gizlenmistir.\n")
    log().info("Sorun raporu olusturuldu: %s", zip_yolu)
    return zip_yolu


def klasoru_goster(yol):
    """Dosya Gezgini'nde dosyayi secili acar."""
    try:
        subprocess.Popen(["explorer", "/select,", str(yol)])
    except Exception:
        pass
