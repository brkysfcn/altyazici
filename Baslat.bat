@echo off
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 goto kurulum
if not exist ".venv" goto kurulum
if not exist "araclar\ffmpeg.exe" goto kurulum
echo yt-dlp guncelleniyor (internet yoksa atlanir)...
uv pip install --quiet --upgrade yt-dlp >nul 2>nul
start "" uv run --no-sync pythonw app\gui.py
exit /b 0
:kurulum
echo Kurulum yapilmamis gorunuyor. Kurulum baslatiliyor...
call Kurulum.bat
