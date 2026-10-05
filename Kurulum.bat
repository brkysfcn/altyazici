@echo off
setlocal
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
rem Sistemde baska Python olsa bile yalnizca uv nin kendi Python 3.12 si kullanilir.
set "UV_PYTHON=3.12"
set "UV_PYTHON_PREFERENCE=only-managed"
echo === Altyazici - Kurulum ===

where uv >nul 2>nul
if errorlevel 1 (
  echo [1/4] uv kuruluyor...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%PATH%"
rem Sistemde baska Python olsa bile yalnizca uv nin kendi Python 3.12 si kullanilir.
set "UV_PYTHON=3.12"
set "UV_PYTHON_PREFERENCE=only-managed"
  where uv >nul 2>nul
  if errorlevel 1 (
    echo HATA: uv kurulamadi. Internet baglantinizi kontrol edip tekrar deneyin.
    pause
    exit /b 1
  )
  echo Bu uv kurulumu Kurulum.bat tarafindan yapildi.> "%~dp0uv_kuruldu.txt"
) else (
  echo [1/4] uv zaten kurulu.
)

echo [2/4] Bagimliliklar kuruluyor - Python 3.12 dahil...
uv sync --frozen
if errorlevel 1 (
  echo HATA: Bagimliliklar kurulamadi. Internet baglantinizi kontrol edin.
  pause
  exit /b 1
)

if exist "araclar\ffmpeg.exe" if exist "araclar\ffprobe.exe" (
  echo [3/4] FFmpeg zaten mevcut.
  goto modeller
)
echo [3/4] FFmpeg indiriliyor...
if not exist araclar mkdir araclar
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $z=Join-Path $env:TEMP 'ffmpeg-btbn.zip'; $d=Join-Path $env:TEMP 'ffmpeg-btbn'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile $z; if(Test-Path $d){Remove-Item $d -Recurse -Force}; Expand-Archive $z -DestinationPath $d -Force; Get-ChildItem $d -Recurse -Include ffmpeg.exe,ffprobe.exe | Copy-Item -Destination 'araclar' -Force; Remove-Item $z -Force; Remove-Item $d -Recurse -Force"
if errorlevel 1 (
  echo HATA: FFmpeg indirilemedi. ffmpeg.exe ve ffprobe.exe dosyalarini elle araclar klasorune koyabilirsiniz.
  pause
  exit /b 1
)
if not exist "araclar\ffmpeg.exe" (
  echo HATA: ffmpeg.exe bulunamadi.
  pause
  exit /b 1
)

:modeller
echo [4/4] Yapay zeka modelleri indiriliyor - toplam yaklasik 7 GB, uzun surebilir...
uv run python app\modelleri_indir.py
if errorlevel 1 (
  echo HATA: Modeller indirilemedi. Baglantinizi ve disk alanini kontrol edip Kurulum.bat dosyasini tekrar calistirin.
  pause
  exit /b 1
)

echo.
echo Kurulum tamamlandi. Baslat.bat ile programi acabilirsiniz.
pause
