@echo off
setlocal
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo === Video Ceviri - Guncelle ===
where uv >nul 2>nul
if errorlevel 1 (
  echo HATA: uv bulunamadi. Once Kurulum.bat dosyasini calistirin.
  pause
  exit /b 1
)

echo [1/3] En son surum GitHub'dan kontrol ediliyor...
uv run --no-sync python app\guncelle.py
if errorlevel 1 (
  echo Kod guncellenemedi. Kutuphane guncellemesine devam ediliyor.
)

echo [2/3] Kutuphaneler uv.lock surumlerine esitleniyor...
uv sync --frozen
if errorlevel 1 (
  echo HATA: Kutuphaneler esitlenemedi. Internet baglantinizi kontrol edin.
  pause
  exit /b 1
)

echo [3/3] yt-dlp en son surume guncelleniyor...
uv pip install --upgrade yt-dlp
if errorlevel 1 (
  echo HATA: yt-dlp guncellenemedi. Internet baglantinizi kontrol edin.
  pause
  exit /b 1
)

echo.
echo Guncel yt-dlp surumu:
uv run --no-sync yt-dlp --version
echo.
echo Tamam. Baslat.bat ile programi acabilirsiniz.
pause
rem Calisan bat dosyasi kendi uzerine yazilamaz: yeni surum en sonda yerine konur.
if exist "Guncelle.bat.yeni" (goto) 2>nul & move /y "Guncelle.bat.yeni" "Guncelle.bat" >nul & exit /b 0
exit /b 0
