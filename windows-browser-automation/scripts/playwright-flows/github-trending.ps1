# Playwright CLI ile tekrarlanabilir tarayici akisi ORNEGI (0 satir kod).
# Kurulum: npm i -g @playwright/cli@latest ; playwright-cli install --skills
#
# Mantik: her adimdan sonra snapshot alinir; snapshot'taki eNN ref'leriyle
# tiklama/yazma yapilir (Inspect -> Act -> Re-inspect dongusu).
# Oturum/profil secenekleri icin: playwright-cli --help
#   (isimli oturumlar ve --persistent kalici profil desteklenir)

playwright-cli open https://github.com/trending --headed
playwright-cli snapshot
playwright-cli find "Star"
# Ornek etkilesim (ref'i kendi snapshot ciktinizdan alin):
#   playwright-cli click e15
playwright-cli screenshot
playwright-cli close

# NOT: Oturum acilmis OTOMASYON Chrome'una baglanmak icin MCP tarafinda
# chrome-devtools-mcp (--browser-url=http://127.0.0.1:9222) veya
# Playwright MCP --extension kullanin; bu CLI akisi kendi tarayicisini acar.
