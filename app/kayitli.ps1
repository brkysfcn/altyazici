# Bir .bat dosyasini calistirir: ciktisi hem ekranda gorunur hem de gunluk dosyasina yazilir.
# Kullanim: powershell -File kayitli.ps1 -Bat "<bat yolu>" -Log "<log yolu>"
param(
    [Parameter(Mandatory = $true)][string]$Bat,
    [Parameter(Mandatory = $true)][string]$Log
)
$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Log) | Out-Null
$env:ALTYAZICI_TEE = "1"
$baslik = "===== {0}  {1} =====" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), (Split-Path -Leaf $Bat)
Add-Content -Path $Log -Value $baslik -Encoding UTF8
# stderr'i cmd'nin kendisi stdout'a yonlendirir (PowerShell 5.1 NativeCommandError gurultusunu onler)
cmd.exe /c "`"$Bat`" 2>&1" | ForEach-Object {
    $_
    # ilerleme cubugu satirlarinda (\r) yalnizca son durumu gunluge yaz; kullanici adini gizle
    $satir = ($_ -split "`r")[-1] -replace [regex]::Escape($env:USERPROFILE), "%USERPROFILE%"
    Add-Content -Path $Log -Value $satir -Encoding UTF8
}
Add-Content -Path $Log -Value ("===== bitti, cikis kodu: {0} =====" -f $LASTEXITCODE) -Encoding UTF8
exit $LASTEXITCODE
