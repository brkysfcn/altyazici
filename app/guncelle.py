# -*- coding: utf-8 -*-
"""GitHub'daki en son surumu indirip kodu gunceller.

Dokunulmayanlar: Ciktilar, modeller, araclar, .venv, loglar, ayarlar.json
Guncelle.bat calisirken kendi uzerine yazilamayacagi icin Guncelle.bat.yeni olarak birakilir.
"""
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KORUNAN = ("ciktilar/", "modeller/", "araclar/", ".venv/", "loglar/", "ayarlar.json")
ZIP_ADI = "Altyazici.zip"


def depo_adi():
    f = ROOT / "guncelleme.txt"
    ad = f.read_text(encoding="utf-8").strip() if f.exists() else ""
    if "BURAYA" in ad or not re.fullmatch(r"[\w.-]+/[\w.-]+", ad):
        raise SystemExit(
            "HATA: guncelleme.txt icinde GitHub deposu 'sahip/depo' biciminde yazili degil.\n"
            "Ornek: ahmet/altyazici")
    return ad


def yerel_surum():
    f = ROOT / "surum.txt"
    return f.read_text(encoding="utf-8").strip() if f.exists() else "0"


def indir(depo):
    url = f"https://github.com/{depo}/releases/latest/download/{ZIP_ADI}"
    print(f"Indiriliyor: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Altyazici-Guncelle"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except Exception as ex:
        raise SystemExit(f"HATA: Surum indirilemedi ({ex}).\n"
                         "Internet baglantinizi ve depo adini kontrol edin; "
                         "depoda en az bir surum (Release) yayinlanmis olmali.")


def guvenli_hedef(ad):
    hedef = (ROOT / ad).resolve()
    if ROOT not in hedef.parents and hedef != ROOT:
        raise SystemExit(f"HATA: Gecersiz dosya yolu paket icinde: {ad}")
    return hedef


def main():
    depo = depo_adi()
    veri = indir(depo)
    with zipfile.ZipFile(io.BytesIO(veri)) as z:
        yeni = z.read("surum.txt").decode("utf-8").strip() if "surum.txt" in z.namelist() else "?"
        eski = yerel_surum()
        print(f"Yuklu surum: {eski}   Yayindaki surum: {yeni}")
        if yeni == eski:
            print("Kod zaten guncel.")
            return
        sayi = 0
        for bilgi in z.infolist():
            ad = bilgi.filename.replace("\\", "/")
            if bilgi.is_dir() or ad.lower().startswith(KORUNAN):
                continue
            hedef = guvenli_hedef(ad)
            if ad == "Guncelle.bat":
                hedef = guvenli_hedef("Guncelle.bat.yeni")
            hedef.parent.mkdir(parents=True, exist_ok=True)
            hedef.write_bytes(z.read(bilgi))
            sayi += 1
    print(f"{sayi} dosya guncellendi ({eski} -> {yeni}).")


if __name__ == "__main__":
    main()
