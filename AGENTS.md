# AGENTS.md — Chromex

Bu depo üç bileşen içerir:

- `policy-gate/` — güvenlik çekirdeği paketi
- `claude-code-automation/` — ralph.sh ajan döngü kiti (bash + Python audit köprüsü)
- `windows-browser-automation/` — API-öncelikli Python otomasyon paketi (aktif geliştirme burada)

## SSOT haritası

- `ANAYASA.md` — değişmez kurallar ve LOC tavanı
- `AGENTS.md` — ajan çalışma kuralları
- `DESIGN_MANIFESTO.md` — tasarım felsefesi
- `GLOSSARY.md` — terim sözlüğü
- `plans/FAZ2-SPRINTLER.md` — Faz 2 sprint planı
- `README.md` — kullanıcı yüzeyi
- `STATE_BOARD.md` — durum takibi

Çelişki olursa `ANAYASA.md` kazanır.

## LOC tavanı

- Toplam: **9.000 LOC**
- Kod: **5.000 LOC**
- Doküman: **3.500 LOC**
- Yapılandırma + destek: **300 LOC**

Yeni iş açılmadan önce kalan bütçe kontrol edilir; tavan aşılamaz.
Güncel bütçe ve sprint dağılımı: `ANAYASA.md` ve `plans/FAZ2-SPRINTLER.md`.

## Komutlar

| İş | Komut |
|---|---|
| Testler | `cd windows-browser-automation; python -m unittest discover -s tests` |
| policy-gate testleri | `cd policy-gate; python -m unittest discover -s tests` (editable kurulumdan sonra PYTHONPATH gerekmez) |
| CI lokal taklit | iki suite'i de çalıştır; sayaçlar CI/README ile eşleşmeli |
| CLI | `python -m orchestrator.cli <komut>` (paket kuruluysa `otomasyon <komut>`) |
| Kurulum | `python -m pip install -e policy-gate` ardından `python -m pip install -e windows-browser-automation` |
| Model yönetimi | `python claude-code-automation/model_manager.py default` |

## Kurallar

- **Dil:** Kod, yorum, docstring, commit mesajları ve dokümanlar Türkçe.
- **Satır sonu:** LF (`.gitattributes` ile sabitli; CRLF yazma).
- **Onay kapısı:** Dış etki yaratan her işlem `policygate.require()` üzerinden geçer.
  DELETE asla `auto` olamaz; SEND/DELETE etkileşimsiz oturumda her zaman reddedilir.
- **Tek kaynak:** Güvenlik çekirdeği (approval/audit/policy/secrets/log/http) yalnızca
  `policy-gate/src/policygate/` altında yaşar; wba tarafında kopya tutulmaz.
- **Secret:** Değerler log'a/hataya yalnızca `policygate.secrets.redact` ile maskelenerek girer;
  hiçbir secret print edilmez, dosyaya düz yazılmaz.
- **Audit:** `policygate/audit.py` zincir formatını değiştirme — `claude-code-automation/audit_bridge.py`
  ile birebir parite testi var (`AuditBridgeParityTests`).
- **Test:** Yeni davranış = yeni offline test. Ağ/CLI/tarayıcı mock'lanır; `playwright`
  kurulu olmadan da testler geçmeli (lazy import kuralı).
- **Stil:** Yorumlar "neden"i açıklar; modül başı docstring düzenini koru; yeni CLI
  komutu `@command` dekoratörüyle eklenir (registry deseni).
- **Konsol çıktısı:** Kullanıcıya yazan her metin cp1252-güvenli olmalı
  (`policygate.approval._console_safe` deseni — Windows CI runner'ları cp1252'dir;
  bu ders CI'da gerçek hatayla öğrenildi).
- **Bağımlılık:** policygate çekirdeği stdlib-only kalır; yeni bağımlılık ancak
  `[project.optional-dependencies]` extra'sı olarak eklenir (ör. `policy-gate[http]`).
- **Sayaç senkronu:** Test ekleyen/silen, test sayaçlarını aynı commit'te günceller
  (`.github/workflows/test.yml`, kök README, wba README).
- **Sürüm/Release:** semver; tag `vX.Y.Z`; GitHub Release + wheel kullanılır.
  PyPI ertelenmiştir; dağıtım kararı değişirse yeni karar kaydı açılır.
- **Gizli veri:** `.env`, `audit/`, `data/` hiçbir zaman commit'lenmez
  (`.gitignore`'a değil, bu kurala güven).
