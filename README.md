# FB-Ceviri

Video linkindeki (Facebook, YouTube, Instagram, TikTok, X vb.) konuşmayı yazıya döküp **Türkçe altyazıya (.srt)** çeviren Windows programı. Tamamen ücretsiz ve internet gerektirmeden bilgisayarınızda çalışır (Whisper + NLLB). Varsayılan konuşma dili Endonezce; Hintçe, İngilizce, Malayca ve otomatik algılama da var.

## Kurulum
1. [Releases](../../releases/latest) sayfasından `FB-Ceviri.zip` dosyasını indirip bir klasöre çıkarın.
2. `Kurulum.bat` dosyasını bir kez çalıştırın (Python, kütüphaneler ve yaklaşık 7 GB model indirilir).
3. `Baslat.bat` ile programı açın, video linkini yapıştırıp **Çevir**'e basın.

Sonuç `Ciktilar\` klasörüne kaydedilir: `video.mp4`, `video.orijinal.srt`, `video.tr.srt`.

## Güncelleme
`Guncelle.bat` en son sürümü indirir; videolarınız, modelleriniz ve ayarlarınız silinmez. Ayrıntılar için `KULLANIM.txt`.

## Gereksinimler
Windows 10/11. NVIDIA ekran kartı varsa hızlı çalışır; yoksa işlemciyle çalışır ama yavaştır.

Yalnızca kişisel kullanım için; telif haklarına ve sitelerin kullanım şartlarına uyun.
