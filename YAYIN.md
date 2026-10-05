# Yayın ve güncelleme kılavuzu (geliştirici)

Program GitHub'da herkese açık bir depoda, sürümler ise **Releases** sayfasında yayınlanır.
Kullanıcılar `Guncelle.bat` ile ya da zip dosyasını elle indirip üzerine kopyalayarak günceller.

## Bir kez yapılacak kurulum

1. https://github.com adresinde hesap açın (ücretsiz).
2. **New repository** > ad: `altyazici` > **Public** > README/gitignore eklemeyin > Create.
3. `guncelleme.txt` dosyasının içine `kullanici-adiniz/altyazici` yazın (başka bir şey yazmayın).
4. Bu klasörde (`E:\AIWORKS\altyazici`) şu komutlarla kodu yükleyin:
   ```
   git init
   git add .
   git commit -m "ilk surum"
   git branch -M main
   git remote add origin https://github.com/kullanici-adiniz/altyazici.git
   git push -u origin main
   ```
   `.gitignore` sayesinde modeller (7 GB), Ciktilar, araclar, `.venv` ve `ayarlar.json` yüklenmez.

## Her yeni sürümde

1. Kodu değiştirin ve test edin.
2. Paketleyin (sürüm numarasını yazın; `surum.txt` de güncellenir):
   ```
   uv run python paketle.py 0.3.0
   ```
   Çıktı: `dist\Altyazici.zip`
3. Değişiklikleri GitHub'a gönderin (`git add .`, `git commit`, `git push`).
4. GitHub'da depo sayfası > **Releases** > **Draft a new release** > Tag: `v0.3.0`
   > `dist\Altyazici.zip` dosyasını sürüme ekleyin > **Publish release**.

**Önemli:** zip dosyasının adı tam olarak `Altyazici.zip` olmalı. `Guncelle.bat`,
`.../releases/latest/download/Altyazici.zip` adresinden indirir.

## Kullanıcı tarafı

- **İlk kurulum:** Releases sayfasından `Altyazici.zip` indirilir, bir klasöre çıkarılır,
  `Kurulum.bat` çalıştırılır.
- **Otomatik güncelleme:** `Guncelle.bat` en son sürümü indirir, kodu ve `uv.lock` dosyasını
  günceller, kütüphaneleri eşitler, yt-dlp'yi yeniler.
- **Elle güncelleme:** yeni `Altyazici.zip` indirilir ve klasörün üzerine çıkarılır
  (zip yalnızca kod içerir; Ciktilar, modeller, araclar ve ayarlar ezilmez).
  Ardından `Guncelle.bat` çalıştırılırsa kütüphaneler de eşitlenir.

## Kaldırma

`Kaldir.bat` kurulu her şeyi onayla temizler (bileşenler, Çıktılar, uv/Python, klasör). `Kurulum.bat`, uv'yi kendisi kurduğunda `uv_kuruldu.txt` bırakır; `Kaldir.bat` yalnızca bu dosya varsa uv ve Python 3.12'yi kaldırmayı önerir.

## Güncellemede korunanlar

`Ciktilar\`, `modeller\`, `araclar\`, `.venv\`, `ayarlar.json`
