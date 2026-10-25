# DERSLER — chromex

Negatif bilgi defteri: denendi, patladı, kural çıktı. Yeni tuzak EN ALTA eklenir (append-only, silmek yok). Her ders: tarih + tek cümle kural + kısa kanıt. Aynı tuzağa iki kez düşme (REHBER §8).

## Dersler
- 2026-10-12 · İskelet kuruldu — henüz ders yok; ilk tuzak buraya yazılacak.
- 2026-10-14 · Windows'ta stdin=NUL/DEVNULL iken `isatty()` True dönebilir — etkileşimsizlik kontrolü isatty'e güvenemez; `input()` EOFError'u çökme yerine red say (fail-closed). Kanıt: raporlar/insan-testi/cli-qa-2026-10-14.md P1-1.
- 2026-10-14 · Onay ekranı detay için okuma gerektiriyorsa `preflight()` + `require()` ikilisi: kesin redler (policy-deny, etkileşimsiz SEND/DELETE) ağdan önce, nihai onay detaylarla — çift onay ve çift audit yok. Kanıt: linkedin.create_post / gmail.send_draft.
- 2026-10-14 · CLI hata sunumu: genel `except` tek satır mesaj + exit 1, traceback yalnızca CHROMEX_DEBUG ile; `main()` girişinde stdout/stderr `reconfigure(errors="replace")` cp1252 sigortasıdır. Kanıt: P1-2/P1-3.
- 2026-10-14 · Sayaç senkronu kuralı ilk gece drift süpürmesinde 10 bulgu yakalattı; test ekleyen commit sayaçları aynı anda güeller (34+41=75).
- 2026-10-14 · PowerShell 5.1 `Set-Content -Encoding UTF8` dosyaya BOM yazar — JSON okuyucular `utf-8-sig` ile okumalı (policy.py). Kanıt: cli-qa P2-10.
- 2026-10-14 · Uzun sessiz bekleyiş kullanıcıya çökme gibi görünür — retry/backoff mesajları varsayılan görünür seviyede (warning) olmalı, `_log.info` kaybolur. Kanıt: cli-qa P2-9.
- 2026-10-14 · Onay reddi ile argüman hatası aynı exit kodunu paylaşmamalı — reddedilen işlem exit 3, usage hatası exit 2 (betikler ayırt edebilsin). Kanıt: cli-qa P2-6.
- 2026-10-15 · PowerShell'de `python -c "... $(...)"` cift-tirnakli dizge interpolasyon tuzagi — `$`, `()` ve `"` PS tarafindan python'a ulasmadan yenir. Kural: python her zaman tek-tirnakli here-string + `[IO.File]::WriteAllText` ile temp dosyaya, oradan calistirilir. Kanit: Faz 1 quickstart duzeltmesi ilk denemede PS parser hatasi.
- 2026-10-19 · Ortam degisince python PATH'e dusmeyebilir ve requests eksik olabilir; testleri sabit runtime yolu ve gecici PYTHONPATH/stub ile calistir, arac hatalarini rapor et. Kanit: 4/18 arac cagrisi basarisiz; policygate 35/35, wba 42/42, exit 0.
- 2026-10-25 · PowerShell'den `codex.exe --codex-run-as-apply-patch`'e here-string ile Türkçe/çift tırnak içeren patch geçince kod sayfası bozulur ve parser "son satır" hatası verir; UTF-8 patch içeriğini Python `subprocess` ile aktar. Kanıt: aynı patch doğrudan PS'te 4 kez düştü, Python köprüsüyle ilk denemede geçti.
