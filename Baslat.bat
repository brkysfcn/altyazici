@echo off
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
rem Sistemde baska Python olsa bile yalnizca uv nin kendi Python 3.12 si kullanilir.
set "UV_PYTHON=3.12"
set "UV_PYTHON_PREFERENCE=only-managed"
where uv >nul 2>nul
if errorlevel 1 goto kurulum
if not exist ".venv" goto kurulum
if not exist "araclar\ffmpeg.exe" goto kurulum
echo yt-dlp guncelleniyor (internet yoksa atlanir)...
if not exist "loglar" mkdir "loglar"
uv pip install --quiet --upgrade yt-dlp >> "loglar\baslat.log" 2>&1
start "" uv run --no-sync pythonw app\gui.py
exit /b 0
:kurulum
echo Kurulum yapilmamis gorunuyor. Kurulum baslatiliyor...
call Kurulum.bat
