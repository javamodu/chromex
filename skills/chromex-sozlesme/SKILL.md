---
name: chromex-sozlesme
description: Chromex deposunda (policy-gate, windows-browser-automation, claude-code-automation) kod veya doküman değiştirirken uyulacak repo sözleşmesi — policygate tek-kaynak kuralı, onay kapısı, test sayacı senkronu, LF/cp1252 disiplinleri. Chromex dışı projelerde kullanma.
---

# Chromex Repo Sözleşmesi

Bu skill, Chromex deposunda değişiklik yapan ajanın uyması gereken
kuralları öğretir. Kaynak: kök `AGENTS.md` — çelişki olursa AGENTS.md
ve kullanıcı talimatı kazanır.

## Harita

- `claude-code-automation/` — ralph.sh ajan döngü kiti (bash + Python
  audit köprüsü).
- `windows-browser-automation/` — API-öncelikli Python otomasyon paketi;
  aktif geliştirme burada. CLI: `python -m orchestrator.cli <komut>`
  (paket kuruluysa `otomasyon <komut>`).
- `policy-gate/` — güvenlik çekirdeği (PyPI: `policy-gate`, import:
  `policygate`). approval / audit / policy / secrets / log / http
  yalnızca `policy-gate/src/policygate/` altında yaşar; wba tarafında
  kopya tutulmaz.

## Komutlar

- Testler: `cd windows-browser-automation; python -m unittest discover -s tests`
  ve `cd policy-gate; python -m unittest discover -s tests`
- Kurulum: `python -m pip install -e policy-gate` ardından
  `python -m pip install -e windows-browser-automation`

## Kurallar

- **Dil:** Kod, yorum, docstring, commit mesajı ve dokümanlar Türkçe.
- **Satır sonu:** LF; CRLF yazma (`.gitattributes` sabitler).
- **Onay kapısı:** Dış etki yaratan her işlem `policygate.require()`
  üzerinden geçer. DELETE asla `auto` olamaz; SEND/DELETE etkileşimsiz
  oturumda her zaman reddedilir.
- **Secret:** Değerler log'a/hataya yalnızca `policygate.secrets.redact`
  ile maskelenerek girer; secret print edilmez, dosyaya düz yazılmaz.
- **Audit:** `policygate/audit.py` zincir formatını değiştirme —
  `claude-code-automation/audit_bridge.py` ile birebir parite testi var
  (`AuditBridgeParityTests`).
- **Test:** Yeni davranış = yeni offline test. Ağ/CLI/tarayıcı
  mock'lanır; `playwright` kurulu olmadan da testler geçmeli
  (lazy import kuralı).
- **CLI:** Yeni komut `@command` dekoratörüyle eklenir (registry deseni);
  ayrı dispatch tablosu tutulmaz.
- **Konsol çıktısı:** Kullanıcıya yazan her metin cp1252-güvenli olmalı
  (`policygate.approval._console_safe` deseni; Windows CI runner'ları
  cp1252'dir).
- **Bağımlılık:** policygate çekirdeği stdlib-only kalır; yeni
  bağımlılık ancak `[project.optional-dependencies]` extra'sı olur
  (ör. `policy-gate[http]`).
- **Sayaç senkronu:** Test ekleyen/silen, sayaçları aynı commit'te
  günceller: `.github/workflows/test.yml`, kök `README.md`,
  `windows-browser-automation/README.md`. Geçerli sayaçlar: 30 + 35 = 65.
- **Sürüm:** semver; tag `vX.Y.Z`; release GitHub'dan açılır →
  `publish-policygate.yml` PyPI'a iner (trusted publisher).
- **Gizli veri:** `.env`, `audit/`, `data/` hiçbir zaman commit'lenmez.

## Doğrulama

Değişiklikten sonra iki test suite'ini de çalıştır (CI lokal taklidi);
sayaçlar CI ve README'lerle eşleşmeli.
