# -*- coding: utf-8 -*-
"""Gelistirici araci: GitHub Release icin dist/FB-Ceviri.zip uretir.

Kullanim:  uv run python paketle.py 0.3.0     (surum.txt de guncellenir)
           uv run python paketle.py           (mevcut surum.txt ile paketler)
Pakete girmeyenler: Ciktilar, modeller, araclar, .venv, ayarlar.json, dist
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOSYALAR = ["Baslat.bat", "Kurulum.bat", "Guncelle.bat", "KULLANIM.txt",
            "pyproject.toml", "uv.lock", "surum.txt", "guncelleme.txt"]


def main():
    if len(sys.argv) > 1:
        (ROOT / "surum.txt").write_text(sys.argv[1].strip() + "\n", encoding="utf-8")
    surum = (ROOT / "surum.txt").read_text(encoding="utf-8").strip()
    depo = (ROOT / "guncelleme.txt").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", depo):
        print(f"UYARI: guncelleme.txt icinde gecerli bir 'sahip/depo' yok ({depo!r}); "
              "Guncelle.bat calismaz.")
    cikti = ROOT / "dist"
    cikti.mkdir(exist_ok=True)
    zip_yolu = cikti / "FB-Ceviri.zip"
    with zipfile.ZipFile(zip_yolu, "w", zipfile.ZIP_DEFLATED) as z:
        for ad in DOSYALAR:
            z.write(ROOT / ad, ad)
        for p in sorted((ROOT / "app").glob("*.py")):
            z.write(p, f"app/{p.name}")
    print(f"Hazir: {zip_yolu}  (surum {surum}, {zip_yolu.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
