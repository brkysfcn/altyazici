@echo off
cd /d "%~dp0"
set "DIR=%~dp0"
if "%DIR:~-1%"=="\" set "DIR=%DIR:~0,-1%"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
rem Sistemde baska Python olsa bile yalnizca uv nin kendi Python 3.12 si kullanilir.
set "UV_PYTHON=3.12"
set "UV_PYTHON_PREFERENCE=only-managed"
echo ============================================
echo   Video Ceviri - KALDIRMA (Uninstall)
echo ============================================
echo.
echo Program klasoru: %DIR%
echo.
echo Bu islem asagidakileri sirayla soracaktir; her adimda onay istenir:
echo   1) Kurulu bilesenler: .venv, modeller (~7 GB), araclar, ayarlar
echo   2) Ciktilar klasoru (VIDEO VE ALTYAZILARINIZ) - ayri sorulur
echo   3) uv ve Python 3.12 (yalnizca Kurulum.bat kurduysa)
echo   4) Program klasorunun kendisi
echo.
choice /c EH /n /m "Devam edilsin mi? (E/H): "
if errorlevel 2 (
  echo Iptal edildi. Hicbir sey silinmedi.
  pause
  exit /b 0
)

rem ---------- 1) Kurulu bilesenler
echo.
echo [1/4] Kurulu bilesenler:
for %%D in (.venv modeller araclar dist) do if exist "%%D" (
  for /f %%S in ('powershell -NoProfile -Command "[math]::Round((Get-ChildItem -LiteralPath '%DIR%\%%D' -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)"') do echo     %%D  - %%S MB
)
if exist "ayarlar.json" echo     ayarlar.json
choice /c EH /n /m "Bunlar silinsin mi? (E/H): "
if errorlevel 2 (
  echo     Atlandi.
) else (
  for %%D in (.venv modeller araclar dist) do if exist "%%D" rmdir /s /q "%%D"
  if exist "ayarlar.json" del /q "ayarlar.json"
  if exist "app\__pycache__" rmdir /s /q "app\__pycache__"
  echo     Silindi.
)

rem ---------- 2) Ciktilar
echo.
echo [2/4] Ciktilar klasoru (videolariniz ve .srt altyazilariniz):
if exist "Ciktilar" (
  for /f %%S in ('powershell -NoProfile -Command "[math]::Round((Get-ChildItem -LiteralPath '%DIR%\Ciktilar' -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)"') do echo     Ciktilar  - %%S MB
  echo     DIKKAT: Silinirse geri alinamaz ^(Geri Donusum Kutusuna gitmez^).
  choice /c EH /n /m "Ciktilar da silinsin mi? Varsayilan onerimiz H (E/H): "
  if errorlevel 2 (
    echo     Ciktilar korundu: %DIR%\Ciktilar
    set "KORU=1"
  ) else (
    rmdir /s /q "Ciktilar"
    echo     Silindi.
  )
) else (
  echo     Ciktilar klasoru yok.
)

rem ---------- 3) uv ve Python
echo.
echo [3/4] uv ve Python 3.12:
if exist "uv_kuruldu.txt" (
  echo     Bunlari Kurulum.bat kurdu. Baska programlariniz uv veya Python 3.12
  echo     kullaniyorsa onlar da calismaz hale gelebilir.
  choice /c EH /n /m "uv, Python 3.12 ve uv onbellegi kaldirilsin mi? (E/H): "
  if errorlevel 2 (
    echo     Atlandi.
  ) else (
    where uv >nul 2>nul
    if not errorlevel 1 (
      uv python uninstall 3.12 >nul 2>nul
      uv cache clean >nul 2>nul
    )
    del /q "%USERPROFILE%\.local\bin\uv.exe" "%USERPROFILE%\.local\bin\uvx.exe" "%USERPROFILE%\.local\bin\uvw.exe" >nul 2>nul
    del /q "uv_kuruldu.txt" >nul 2>nul
    echo     Kaldirildi. ^(Kullanici PATH'indeki .local\bin girdisine dokunulmadi; zararsizdir.^)
  )
) else (
  echo     uv bu bilgisayarda Kurulum.bat'tan once vardi veya baska yolla kuruldu;
  echo     bu nedenle uv ve Python'a dokunulmuyor.
)

rem ---------- 4) Program klasoru
echo.
echo [4/4] Program klasoru:
if defined KORU (
  echo     Ciktilar korundugu icin klasorun kendisi silinmeyecek.
  echo     Kalan kod dosyalari kucuktur; isterseniz klasoru elle silebilirsiniz.
) else (
  choice /c EH /n /m "Program klasorunun kendisi (kod dosyalari) de silinsin mi? (E/H): "
  if not errorlevel 2 (
    echo     Klasor siliniyor: %DIR%
    cd /d "%TEMP%"
    (goto) 2>nul & rmdir /s /q "%DIR%" & exit /b 0
  )
)
echo.
echo Kaldirma tamamlandi.
pause
exit /b 0
