# Otomasyon Chrome'unu AYRI profil + CDP portuyla baslatir.
#
# NEDEN AYRI PROFIL?
# - Chrome 136+ varsayilan profil dizininde --remote-debugging-port'u
#   KABUL ETMEZ; ayri --user-data-dir zorunludur (guvenlik icin de dogrusu).
# - Gunluk profilinizle cakisma (cookie/eklenti/es zamanli kullanim) onlenir.
#
# GUVENLIK:
# - Port yalnizca 127.0.0.1'de dinler; ASLA disari acmayin/yonlendirmeyin.
# - Port acikken ayni makinedeki HER uygulama tarayiciyi kontrol edebilir;
#   is bitince stop-chrome-automation.ps1 ile kapatin.
# - Ilk calistirmada hedef sitelere (GitHub, X, Gmail...) ELLE giris yapin;
#   otomasyon login sayfalarina hic dokunmamalidir.

param(
    [int]$Port = 9222,
    [string]$ProfileName = "profile-main"
)

$userDataDir = Join-Path $env:LOCALAPPDATA "ChromeAutomation\$ProfileName"
New-Item -ItemType Directory -Force -Path $userDataDir | Out-Null

$chrome = Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) {
    $chrome = Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"
}
if (-not (Test-Path $chrome)) {
    Write-Error "chrome.exe bulunamadi. Chrome kurulumunu kontrol edin."
    exit 1
}

# Start-Process ile arka planda baslat: "&" cagrisi Chrome kapanana dek
# script'i kilitler ve asagidaki bilgi mesajlari asla gorunmezdi.
Start-Process -FilePath $chrome -ArgumentList "--remote-debugging-port=$Port", "--user-data-dir=`"$userDataDir`""

Write-Host ""
Write-Host "Chrome baslatildi:"
Write-Host "  CDP endpoint : http://127.0.0.1:$Port"
Write-Host "  Profil       : $userDataDir"
Write-Host ""
Write-Host "Birden fazla profil icin farkli -Port ve -ProfileName ile tekrar calistirin:"
Write-Host "  .\start-chrome-automation.ps1 -Port 9223 -ProfileName profile-work"
