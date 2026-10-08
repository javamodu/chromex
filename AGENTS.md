# AGENTS.md — Chromex

Bu depo iki bağımsız araç seti içerir:

- `claude-code-automation/` — ralph.sh ajan döngü kiti (bash + Python audit köprüsü)
- `windows-browser-automation/` — API-öncelikli Python otomasyon paketi (aktif geliştirme burada)

## Komutlar

| İş | Komut |
|---|---|
| Testler | `cd windows-browser-automation; python -m unittest discover -s tests` |
| policy-gate testleri | `cd policy-gate; $env:PYTHONPATH="src"; python -m unittest discover -s tests` |
| CLI | `python -m orchestrator.cli <komut>` (paket kuruluysa `otomasyon <komut>`) |
| Kurulum | `python -m pip install -e windows-browser-automation` |

## Kurallar

- **Dil:** Kod, yorum, docstring, commit mesajları ve dokümanlar Türkçe.
- **Satır sonu:** LF (`.gitattributes` ile sabitli; CRLF yazma).
- **Onay kapısı:** Dış etki yaratan her işlem `core/approval.require()` üzerinden geçer.
  DELETE asla `auto` olamaz; SEND/DELETE etkileşimsiz oturumda her zaman reddedilir.
- **Secret:** Değerler log'a/hataya yalnızca `core/secrets.redact` ile maskelenerek girer;
  hiçbir secret print edilmez, dosyaya düz yazılmaz.
- **Audit:** `core/audit.py` zincir formatını değiştirme — `claude-code-automation/audit_bridge.py`
  ile birebir parite testi var (`AuditBridgeParityTests`).
- **Test:** Yeni davranış = yeni offline test. Ağ/CLI/tarayıcı mock'lanır; `playwright`
  kurulu olmadan da testler geçmeli (lazy import kuralı).
- **Stil:** Yorumlar "neden"i açıklar; modül başı docstring düzenini koru; yeni CLI
  komutu `@command` dekoratörüyle eklenir (registry deseni).
