# -*- coding: utf-8 -*-
"""Video linki (Facebook, YouTube vb.) -> Turkce altyazi: Tkinter arayuzu."""
import os
import re
import sys
import queue
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import gunluk  # noqa: E402

MOTORLAR = [("Yerel NLLB (internetsiz, ücretsiz)", "nllb"), ("Google (internet gerekir, sınırlı)", "google")]
DILLER = [("Endonezce", "id"), ("Otomatik algıla", "auto"), ("Hintçe", "hi"),
          ("İngilizce", "en"), ("Malayca", "ms")]
TARAYICILAR = ["chrome", "edge", "firefox"]
AYAR_DOSYASI = APP_DIR.parent / "ayarlar.json"  # guncellemede korunur


def _ayar_oku():
    try:
        import json
        return json.loads(AYAR_DOSYASI.read_text(encoding="utf-8"))
    except Exception:
        return {}


class Uygulama(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Altyazıcı - Video Türkçe Altyazı")
        self.geometry("760x560")
        self.minsize(620, 440)
        self.kuyruk = queue.Queue()
        self.calisiyor = False
        self.cikti = None
        self._satir_guncelle = False  # son satir \r ile yazildiysa
        self._arayuz()
        self.after(100, self._kuyruk_isle)

    def _arayuz(self):
        p = ttk.Frame(self, padding=10)
        p.pack(fill="both", expand=True)

        ttk.Label(p, text="Video linki (Facebook, YouTube, Instagram, TikTok, X ...):").pack(anchor="w")
        satir = ttk.Frame(p)
        satir.pack(fill="x", pady=(2, 8))
        self.url = tk.StringVar()
        self.giris = ttk.Entry(satir, textvariable=self.url)
        self.giris.pack(side="left", fill="x", expand=True)
        ttk.Button(satir, text="Yapıştır", command=self._yapistir).pack(side="left", padx=(6, 0))
        self.giris.bind("<Return>", lambda e: self._baslat())
        self.giris.focus_set()

        sec = ttk.Frame(p)
        sec.pack(fill="x", pady=(0, 8))
        ttk.Label(sec, text="Konuşma dili:").pack(side="left")
        self.dil = tk.StringVar(value=DILLER[0][0])
        ttk.Combobox(sec, textvariable=self.dil, state="readonly", width=16,
                     values=[d[0] for d in DILLER]).pack(side="left", padx=(6, 18))
        self.cerez = tk.BooleanVar(value=False)
        ttk.Checkbutton(sec, text="Tarayıcı çerezlerini kullan", variable=self.cerez,
                        command=self._cerez_durum).pack(side="left")
        self.motor = tk.StringVar(value=MOTORLAR[0][0])
        ttk.Combobox(sec, textvariable=self.motor, state="readonly", width=34,
                     values=[m[0] for m in MOTORLAR]).pack(side="left", padx=(0, 18))
        self.tarayici = tk.StringVar(value=TARAYICILAR[0])
        self.tarayici_kutu = ttk.Combobox(sec, textvariable=self.tarayici, state="disabled",
                                          width=9, values=TARAYICILAR)
        self.tarayici_kutu.pack(side="left", padx=6)
        self._ayar_yukle()

        self.dugme = ttk.Button(p, text="Çevir", command=self._baslat)
        self.dugme.pack(fill="x", pady=(0, 8), ipady=4)

        self.adim_etiket = ttk.Label(p, text="Hazır.")
        self.adim_etiket.pack(anchor="w")
        self.ilerleme = ttk.Progressbar(p, maximum=4, mode="determinate")
        self.ilerleme.pack(fill="x", pady=(2, 8))

        kutu = ttk.Frame(p)
        kutu.pack(fill="both", expand=True)
        self.log = tk.Text(kutu, height=12, wrap="word", state="disabled",
                           font=("Consolas", 9))
        kay = ttk.Scrollbar(kutu, command=self.log.yview)
        self.log.configure(yscrollcommand=kay.set)
        kay.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.tag_configure("hata", foreground="#b00020")

        self.hata = ttk.Label(p, text="", foreground="#b00020", wraplength=720, justify="left")
        self.hata.pack(fill="x", pady=(6, 0))

        alt = ttk.Frame(p)
        alt.pack(fill="x", pady=(6, 0))
        self.ac = ttk.Button(alt, text="Klasörü Aç", command=self._klasor_ac, state="disabled")
        self.ac.pack(side="right")
        ttk.Button(alt, text="Sorun Raporu Oluştur", command=self._rapor).pack(side="left")
        ttk.Button(alt, text="Günlüğü Aç", command=self._gunluk_ac).pack(side="left", padx=(6, 0))

    # ---- yardimcilar
    def _gunluk_ac(self):
        try:
            if gunluk.LOG_FILE.exists():
                os.startfile(str(gunluk.LOG_FILE))
            else:
                messagebox.showinfo("Günlük", "Henüz günlük dosyası yok.")
        except Exception as e:
            messagebox.showerror("Günlük", f"Günlük açılamadı: {e}")

    def _rapor(self):
        try:
            yol = gunluk.rapor_olustur()
        except Exception as e:
            gunluk.log().exception("Rapor olusturulamadi")
            messagebox.showerror("Sorun raporu", f"Rapor oluşturulamadı: {e}")
            return
        gunluk.klasoru_goster(yol)
        messagebox.showinfo(
            "Sorun raporu hazır",
            f"Rapor masaüstüne kaydedildi:\n{yol.name}\n\n"
            "Bu dosyayı geliştiriciye gönderin.\n\n"
            "Rapor video dosyası içermez; indirdiğiniz video linklerini ve başlıklarını "
            "içerebilir. Kullanıcı adınız gizlenmiştir.")

    def _yapistir(self):
        try:
            self.url.set(self.clipboard_get().strip())
        except tk.TclError:
            pass

    def _cerez_durum(self):
        self.tarayici_kutu.configure(state="readonly" if self.cerez.get() else "disabled")

    def _klasor_ac(self):
        if self.cikti and Path(self.cikti).exists():
            os.startfile(str(self.cikti))

    def _yaz(self, metin, end="\n"):
        self.log.configure(state="normal")
        if self._satir_guncelle:
            self.log.delete("end-1c linestart", "end-1c")
        self.log.insert("end", metin)
        self._satir_guncelle = (end == "\r")
        if end != "\r":
            self.log.insert("end", "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        m = re.search(r"\b([1-4])/4\b", metin)
        if m:
            n = int(m.group(1))
            self.ilerleme["value"] = n - 1
            self.adim_etiket.configure(text=metin.strip())

    # ---- ayarlar
    def _ayar_yukle(self):
        a = _ayar_oku()
        if a.get("dil") in [d[0] for d in DILLER]:
            self.dil.set(a["dil"])
        if a.get("motor") in [m[0] for m in MOTORLAR]:
            self.motor.set(a["motor"])
        if a.get("tarayici") in TARAYICILAR:
            self.tarayici.set(a["tarayici"])
        self.cerez.set(bool(a.get("cerez", False)))
        self._cerez_durum()

    def _ayar_kaydet(self):
        try:
            import json
            AYAR_DOSYASI.write_text(json.dumps({
                "dil": self.dil.get(), "motor": self.motor.get(),
                "tarayici": self.tarayici.get(), "cerez": bool(self.cerez.get()),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ---- is akisi
    def _baslat(self):
        if self.calisiyor:
            return
        url = self.url.get().strip()
        if not re.match(r"^https?://", url):
            messagebox.showwarning("Link gerekli", "Lütfen tek bir videonun linkini girin (http ile başlamalı). Oynatma listesi desteklenmez.")
            return
        kod = dict(DILLER).get(self.dil.get(), "id")
        motor = dict(MOTORLAR).get(self.motor.get(), "google")
        cerez = self.tarayici.get() if self.cerez.get() else None
        self.calisiyor = True
        self.cikti = None
        self.dugme.configure(state="disabled", text="Çalışıyor...")
        self.ac.configure(state="disabled")
        self.hata.configure(text="")
        self.ilerleme["value"] = 0
        self.adim_etiket.configure(text="Başlıyor...")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._satir_guncelle = False
        self._ayar_kaydet()
        gunluk.log().info("Arayuz: Cevir'e basildi (dil=%s, motor=%s)", kod, motor)
        threading.Thread(target=self._calis, args=(url, cerez, kod, motor), daemon=True).start()

    def _calis(self, url, cerez, kod, motor):
        def log(msg="", end="\n", **_):
            self.kuyruk.put(("log", str(msg), end))
        try:
            import cevir_core
            sonuc = cevir_core.isle(url, log=log, tarayici_cerezi=cerez, dil=kod, motor=motor)
            self.kuyruk.put(("bitti", str(sonuc)))
        except BaseException as e:
            self.kuyruk.put(("hata", f"{e}", traceback.format_exc()))

    def _kuyruk_isle(self):
        try:
            while True:
                o = self.kuyruk.get_nowait()
                if o[0] == "log":
                    self._yaz(o[1], o[2])
                elif o[0] == "bitti":
                    self._bitti(o[1])
                elif o[0] == "hata":
                    self._hata(o[1], o[2])
        except queue.Empty:
            pass
        self.after(100, self._kuyruk_isle)

    def _son(self):
        self.calisiyor = False
        self.dugme.configure(state="normal", text="Çevir")

    def _bitti(self, yol):
        self._son()
        self.cikti = yol
        self.ilerleme["value"] = 4
        self.adim_etiket.configure(text="Tamamlandı.")
        self.ac.configure(state="normal")
        self._klasor_ac()

    def _hata(self, mesaj, ayrinti):
        self._son()
        self.adim_etiket.configure(text="Hata oluştu.")
        self.hata.configure(text=f"Hata: {mesaj or 'Bilinmeyen hata'}\n"
                                 "Giriş gerektiren videolarda 'Tarayıcı çerezlerini kullan' seçeneğini açın (tarayıcıyı kapatmanız gerekebilir); gerekmeyen videolarda kapalı bırakın.\n"
                                 "Sorun sürerse 'Sorun Raporu Oluştur' düğmesiyle rapor hazırlayıp gönderin.")
        self.log.configure(state="normal")
        self.log.insert("end", "\n" + ayrinti, "hata")
        self.log.see("end")
        self.log.configure(state="disabled")

    def destroy(self):
        if self.calisiyor and not messagebox.askyesno("Çıkış", "İşlem sürüyor. Yine de çıkılsın mı?"):
            return
        super().destroy()
        if self.calisiyor:
            os._exit(0)


if __name__ == "__main__":
    gunluk.kur()
    gunluk.oturum_basligi()
    Uygulama().mainloop()
