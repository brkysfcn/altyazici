"""Altyazici: video linkinden Turkce altyazi (Endonezce konusma). Tamamen yerel ve ucretsiz."""
import os
import re
import sys
import glob
import shutil
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gunluk  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ARAC = ROOT / "araclar"
MODEL_DIR = ROOT / "modeller"
CIKTI = ROOT / "Ciktilar"
VARSAYILAN_DIL = "id"  # "auto" = otomatik algila
NLLB_KOD = {"id": "ind_Latn", "hi": "hin_Deva", "en": "eng_Latn", "ms": "zsm_Latn",
            "ar": "arb_Arab", "ur": "urd_Arab", "es": "spa_Latn", "fr": "fra_Latn",
            "de": "deu_Latn", "ru": "rus_Cyrl", "pt": "por_Latn", "tl": "tgl_Latn",
            "jw": "jav_Latn", "su": "sun_Latn", "bn": "ben_Beng", "ta": "tam_Taml"}
NLLB_REPO = "OpenNMT/nllb-200-3.3B-ct2-int8"  # en kaliteli yerel model (~3.3 GB)
NLLB_YEDEK_REPO = "JustFrederik/nllb-200-distilled-1.3B-ct2-int8"  # bellek yetmezse
NLLB_SPM_REPO = "JustFrederik/nllb-200-distilled-1.3B-ct2-int8"
os.environ["PATH"] = str(ARAC) + os.pathsep + os.environ.get("PATH", "")
os.environ.setdefault("HF_HOME", str(MODEL_DIR / "hf"))


def _cuda_dll_ekle():
    """pip ile gelen cublas/cudnn DLL'lerini Windows'ta bulunur hale getirir."""
    if sys.platform != "win32":
        return
    for sp in sys.path:
        for d in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


_cuda_dll_ekle()


def gpu_var_mi():
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def gpu_bellek_mb():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return int(out.strip().splitlines()[0])
    except Exception:
        return 0


def guvenli_ad(s, n=60):
    s = re.sub(r"^[\d.,]+[KMB]? views\s*[·|]\s*([\d.,]+[KMB]? reactions\s*[·|]?\s*)?", "", s)
    s = re.sub(r'[\\/:*?"<>|\r\n#]+', " ", s).strip()
    return (re.sub(r"\s+", " ", s)[:n].strip() or "video")


# ---------------------------------------------------------------- indirme
def indir(url, klasor, log=print, tarayici_cerezi=None):
    """Indirir. Tarayici cerezleri okunamazsa (ornegin Chrome aciksa) cerezsiz yeniden dener:
    herkese acik videolar cerez gerektirmez, cerez secenegi indirmeyi bozmamali."""
    import yt_dlp
    try:
        return _indir_dene(url, klasor, log, tarayici_cerezi)
    except yt_dlp.utils.DownloadError as ex:
        if tarayici_cerezi and "cookie" in str(ex).lower():
            gunluk.log().warning("Cerezler okunamadi (%s); cerezsiz yeniden deneniyor.", tarayici_cerezi)
            log(f"  {tarayici_cerezi} cerezleri okunamadi (tarayici acik olabilir); cerezsiz deneniyor...")
            return _indir_dene(url, klasor, log, None)
        raise


def _indir_dene(url, klasor, log, tarayici_cerezi):
    import yt_dlp
    klasor.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(klasor / "video.%(ext)s"),
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
        "merge_output_format": "mp4",
        "quiet": True, "noplaylist": True, "noprogress": True,
        "verbose": True, "logger": gunluk.YtdlpGunluk(),  # ekrana degil, gunluge yazar
        "extract_flat": "in_playlist",  # listeyi acmadan yalnizca liste mi diye bakar
        "ffmpeg_location": str(ARAC),
        "progress_hooks": [lambda d: d["status"] == "downloading" and log(
            f"  indiriliyor {d.get('_percent_str', '').strip()}", end="\r")],
    }
    if tarayici_cerezi:
        opts["cookiesfrombrowser"] = (tarayici_cerezi,)
    with yt_dlp.YoutubeDL(opts) as ydl:
        # noplaylist: "watch?v=..&list=.." linkinde yalnizca o video indirilir.
        # Saf oynatma listesi / kanal linkleri ise acikca reddedilir.
        info = ydl.extract_info(url, download=False)
        if info.get("_type") in ("playlist", "multi_video") or "entries" in info:
            raise RuntimeError("Oynatma listesi ve kanal linkleri desteklenmiyor. "
                               "Lutfen tek bir videonun linkini girin.")
        ydl.process_ie_result(info, download=True)
    mp4 = klasor / "video.mp4"
    if not mp4.exists():
        bulunan = [p for p in klasor.glob("video.*") if p.suffix in (".mp4", ".mkv", ".webm")]
        if not bulunan:
            raise RuntimeError("Video indirilemedi.")
        mp4 = bulunan[0]
    return mp4, (info.get("title") or info.get("id") or "video")


# ---------------------------------------------------------------- ses
def ses_cikar(video, wav):
    subprocess.run(
        [str(ARAC / "ffmpeg.exe"), "-y", "-i", str(video), "-vn", "-ac", "1",
         "-ar", "16000", str(wav)],
        check=True, capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


# ---------------------------------------------------------------- Whisper
def metne_dok(wav, log=print, dil=VARSAYILAN_DIL):
    from faster_whisper import WhisperModel
    gpu = gpu_var_mi()
    if gpu:
        mb = gpu_bellek_mb()
        # 4 GB kartta large-v3 icin int8_float16 yeterli
        model_ad, tur = ("large-v3", "int8_float16") if mb >= 3500 else ("medium", "int8_float16")
        cihaz = "cuda"
    else:
        model_ad, tur, cihaz = "medium", "int8", "cpu"
    log(f"  Whisper: {model_ad} ({cihaz}, {tur})")
    model = WhisperModel(model_ad, device=cihaz, compute_type=tur,
                         download_root=str(MODEL_DIR / "whisper"))
    segs, bilgi = model.transcribe(
        str(wav), language=None if dil == "auto" else dil, task="transcribe", beam_size=5,
        vad_filter=True, vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False)
    sonuc = []
    for s in segs:
        t = s.text.strip()
        if t:
            sonuc.append((s.start, s.end, t))
    del model
    log(f"  Algilanan dil: {bilgi.language}")
    return sonuc, bilgi.language


# ---------------------------------------------------------------- NLLB
def _nllb_hazirla(repo=None):
    from huggingface_hub import snapshot_download
    return snapshot_download(repo or NLLB_REPO, cache_dir=str(MODEL_DIR / "nllb"))


def _spm_yolu(model_yolu):
    """3.3B deposunda sentencepiece dosyasi yok; tum NLLB-200 modelleri ayni sozlugu kullanir."""
    yerel = next(Path(model_yolu).glob("*.model"), None)
    if yerel:
        return str(yerel)
    from huggingface_hub import hf_hub_download
    return hf_hub_download(NLLB_SPM_REPO, "sentencepiece.bpe.model",
                           cache_dir=str(MODEL_DIR / "nllb"))


def _cumlelere_bol(metin):
    """NLLB cumle duzeyinde egitildi: cok cumleli girdide ikinci cumleyi atabiliyor."""
    parcalar = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", metin) if p.strip()]
    return parcalar or [metin]


def _nllb_yukle(log):
    import ctranslate2
    gpu = gpu_var_mi()
    for repo in (NLLB_REPO, NLLB_YEDEK_REPO):
        try:
            yol = _nllb_hazirla(repo)
            tr = ctranslate2.Translator(yol, device="cuda" if gpu else "cpu",
                                        compute_type="int8_float16" if gpu else "int8")
            return tr, yol
        except Exception as ex:
            gunluk.log().exception("NLLB modeli yuklenemedi: %s", repo)
            log(f"  {repo} yuklenemedi ({type(ex).__name__}: {ex}); daha kucuk model deneniyor...")
    raise RuntimeError("NLLB modeli yuklenemedi.")


def turkceye_cevir(segmentler, kaynak_dil, log=print):
    import sentencepiece as spm
    tr, yol = _nllb_yukle(log)
    sp = spm.SentencePieceProcessor(model_file=_spm_yolu(yol))
    kod = NLLB_KOD.get(kaynak_dil, "eng_Latn")
    # her segment -> cumleler; hepsini tek listede cevirip geri birlestir
    parcalar, sahip = [], []
    for k, (_, _, t) in enumerate(segmentler):
        for c in _cumlelere_bol(t):
            parcalar.append(c)
            sahip.append(k)
    kaynak = [[kod] + sp.encode(c, out_type=str) + ["</s>"] for c in parcalar]
    cevrilen = []
    for i in range(0, len(kaynak), 16):
        parti = kaynak[i:i + 16]
        res = tr.translate_batch(parti, target_prefix=[["tur_Latn"]] * len(parti),
                                 beam_size=4, max_decoding_length=256,
                                 repetition_penalty=1.2, no_repeat_ngram_size=4)
        cevrilen += [sp.decode(r.hypotheses[0][1:]).strip() for r in res]
        log(f"  Ceviri {min(i + 16, len(kaynak))}/{len(kaynak)}", end="\r")
    # yariya dusen ceviri (NLLB'nin icerik atmasi): kaynagi ikiye bolup tekrar cevir
    def _cevir(metinler):
        src = [[kod] + sp.encode(m, out_type=str) + ["</s>"] for m in metinler]
        res = tr.translate_batch(src, target_prefix=[["tur_Latn"]] * len(src), beam_size=4,
                                 max_decoding_length=256, repetition_penalty=1.2,
                                 no_repeat_ngram_size=4)
        return [sp.decode(r.hypotheses[0][1:]).strip() for r in res]
    for i, (kaynak_m, c) in enumerate(zip(parcalar, cevrilen)):
        kel = kaynak_m.split()
        if len(kaynak_m) > 40 and len(c) < 0.5 * len(kaynak_m) and len(kel) >= 6:
            yari = len(kel) // 2
            a, b = _cevir([" ".join(kel[:yari]), " ".join(kel[yari:])])
            cevrilen[i] = (a + " " + b).strip()
    cikti = [""] * len(segmentler)
    for k, c in zip(sahip, cevrilen):
        cikti[k] = (cikti[k] + " " + c).strip()
    del tr
    return cikti


# ---------------------------------------------------------------- SRT
def _zaman(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _satirla(t, uz=42):
    kel, satirlar, cur = t.split(), [], ""
    for k in kel:
        if len(cur) + len(k) + 1 > uz and cur:
            satirlar.append(cur)
            cur = k
        else:
            cur = (cur + " " + k).strip()
    if cur:
        satirlar.append(cur)
    return "\n".join(satirlar)


def srt_yaz(yol, segmentler, metinler):
    with open(yol, "w", encoding="utf-8") as f:
        for i, ((b, e, _), m) in enumerate(zip(segmentler, metinler), 1):
            f.write(f"{i}\n{_zaman(b)} --> {_zaman(e)}\n{_satirla(m)}\n\n")


# ---------------------------------------------------------------- cumle birlestirme
GOOGLE_KOD = {"jw": "jv", "tl": "tl"}


def cumleleri_birlestir(segs, max_bosluk=1.0, max_karakter=100):
    """Kisa parcalari cumle bazinda gruplar: baglam korunur, ceviri iyilesir."""
    gruplar, cur = [], []
    for b, e, t in segs:
        if cur:
            onceki_son = cur[-1][2].rstrip()[-1:]
            uzunluk = sum(len(x[2]) + 1 for x in cur)
            if (onceki_son in ".?!…" or b - cur[-1][1] > max_bosluk
                    or uzunluk + len(t) > max_karakter):
                gruplar.append(cur)
                cur = []
        cur.append((b, e, t))
    if cur:
        gruplar.append(cur)
    return [(g[0][0], g[-1][1], " ".join(x[2] for x in g)) for g in gruplar]


def cevir_google(metinler, kaynak_dil, log=print):
    from deep_translator import GoogleTranslator
    kod = GOOGLE_KOD.get(kaynak_dil, kaynak_dil if kaynak_dil != "auto" else "auto")
    ceviri = GoogleTranslator(source=kod, target="tr")
    sonuc = []
    for i, m in enumerate(metinler, 1):
        t = ceviri.translate(m) if m.strip() else ""
        if t is None:
            raise RuntimeError("Google bos yanit dondurdu.")
        sonuc.append(t.strip())
        log(f"  Google ceviri {i}/{len(metinler)}", end="\r")
    return sonuc


def cevir_metinler(grup_segs, kaynak_dil, motor="google", log=print):
    if motor == "google":
        try:
            return cevir_google([t for _, _, t in grup_segs], kaynak_dil, log)
        except Exception as ex:
            log(f"  Google kullanilamadi ({type(ex).__name__}); yerel NLLB'ye geciliyor...")
    return turkceye_cevir(grup_segs, kaynak_dil, log)


def bol_ve_yaz(yol, gruplar, metinler, uz=42, satir=2):
    """Her cevrilmis cumleyi okunakli (en fazla 2 satir) altyazilara bolup sureyi paylastirir."""
    cuelar = []
    for (b, e, _), m in zip(gruplar, metinler):
        kel, parcalar, cur = m.split(), [], []
        for k in kel:
            if cur and len(" ".join(cur + [k])) > uz * satir:
                parcalar.append(" ".join(cur))
                cur = [k]
            else:
                cur.append(k)
        if cur:
            parcalar.append(" ".join(cur))
        if not parcalar:
            continue
        toplam = sum(len(p) for p in parcalar)
        t = b
        for p in parcalar:
            d = (e - b) * len(p) / toplam
            cuelar.append((t, t + d, p))
            t += d
    with open(yol, "w", encoding="utf-8") as f:
        for i, (b, e, m) in enumerate(cuelar, 1):
            f.write(f"{i}\n{_zaman(b)} --> {_zaman(e)}\n{_satirla(m)}\n\n")


# ---------------------------------------------------------------- ana akis
def isle(url, log=print, tarayici_cerezi=None, dil=VARSAYILAN_DIL, motor="nllb"):
    """Tum is akisi; her adimi ve hatayi loglar/altyazici.log dosyasina da yazar."""
    gunluk.kur()
    gunluk.oturum_basligi()
    lg = gunluk.log()

    def kayitli(m="", end="\n", **_):
        if end != "\r":  # ilerleme yuzdesi satirlari gunluge yazilmaz
            lg.info(str(m).strip())
        log(m, end=end)

    lg.info("ISLEM BASLADI url=%s dil=%s motor=%s cerez=%s", url, dil, motor,
            tarayici_cerezi or "yok")
    t0 = time.perf_counter()
    try:
        sonuc = _isle(url, kayitli, tarayici_cerezi, dil, motor)
    except BaseException:
        lg.exception("ISLEM BASARISIZ (%.1f sn)", time.perf_counter() - t0)
        raise
    lg.info("ISLEM TAMAMLANDI (%.1f sn) -> %s", time.perf_counter() - t0, sonuc)
    return sonuc


def _isle(url, log, tarayici_cerezi, dil, motor):
    from datetime import date
    gecici = CIKTI / "_gecici"
    if gecici.exists():
        shutil.rmtree(gecici)
    log("1/4 Video indiriliyor...")
    mp4, baslik = indir(url, gecici, log, tarayici_cerezi)
    hedef = CIKTI / f"{date.today()}_{guvenli_ad(baslik)}"
    n = 2
    while hedef.exists():
        hedef = CIKTI / f"{date.today()}_{guvenli_ad(baslik)}_{n}"
        n += 1
    shutil.move(str(gecici), str(hedef))
    mp4 = hedef / mp4.name
    video = hedef / "video.mp4"
    if mp4 != video:
        mp4.rename(video)

    log("2/4 Ses ayriliyor...")
    wav = hedef / "_ses.wav"
    ses_cikar(video, wav)

    log("3/4 Konusma metne donusturuluyor...")
    segs, algilanan = metne_dok(wav, log, dil)
    wav.unlink(missing_ok=True)
    if not segs:
        raise RuntimeError("Videoda konusma bulunamadi.")
    log(f"  {len(segs)} konusma parcasi bulundu (dil: {algilanan})")
    srt_yaz(hedef / "video.orijinal.srt", segs, [t for _, _, t in segs])

    log("4/4 Turkceye cevriliyor...")
    gruplar = cumleleri_birlestir(segs)
    tr = cevir_metinler(gruplar, algilanan, motor, log)
    bol_ve_yaz(hedef / "video.tr.srt", gruplar, tr)
    log(f"Tamam: {hedef}")
    return hedef


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python cevir_core.py <video-linki>")
        sys.exit(1)
    isle(sys.argv[1])
