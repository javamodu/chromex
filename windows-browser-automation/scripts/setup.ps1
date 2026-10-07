# Tek seferlik kurulum (Windows, PowerShell).
# Gerekenler: Node.js 20+, Python 3.11+, winget (gh icin) onceden kurulu olmali.

Write-Host "== Node tabanli araclar =="
npm install -g @playwright/cli@latest
playwright-cli install --skills          # coding agent'lar icin skill dosyalari
npm install -g supabase vercel

Write-Host "== GitHub CLI =="
winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
# Kurulumdan sonra bir kez: gh auth login

Write-Host "== Python bagimliliklari =="
python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt

Write-Host ""
Write-Host "Kurulum bitti. Sonraki adimlar:"
Write-Host "  1) ..\.env.example dosyasini ..\.env olarak kopyalayip doldurun."
Write-Host "  2) gh auth login  (GitHub icin)"
Write-Host "  3) Gmail icin credentials.json'i proje kokune koyun (README)."
Write-Host "  4) .\start-chrome-automation.ps1 ile otomasyon Chrome'unu acin."
