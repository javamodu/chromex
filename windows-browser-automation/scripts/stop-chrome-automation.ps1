# Otomasyon profiline ait Chrome process'lerini kapatir (CDP portu da kapanir).
# Gunluk Chrome'unuza DOKUNMAZ: yalnizca ChromeAutomation\<profil> ile
# baslatilmis process'leri hedefler.

param(
    [string]$ProfileName = "profile-main"
)

$dir = Join-Path $env:LOCALAPPDATA "ChromeAutomation\$ProfileName"

$procs = Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
    Where-Object { $_.CommandLine -like "*$dir*" }

if (-not $procs) {
    Write-Host "Bu profile ait calisan Chrome bulunamadi: $dir"
    exit 0
}

$procs | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Otomasyon Chrome'u kapatildi; CDP portu artik dinlemiyor. ($ProfileName)"
