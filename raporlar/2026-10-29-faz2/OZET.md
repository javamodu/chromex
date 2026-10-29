# Sprint 4 Kanıt Özeti

- Tarih: 2026-10-30
- Kod kanıtı: `de66f6a` — Sprint 4: Paseo model soru komutu
- Model: `glm-5.3` / sağlayıcı `claude-glm`
- Arayüz: yerel Paseo CLI, plan modu, JSON çıktı şeması

## Doğrulama

| Komut | Sonuç |
|---|---|
| `paseo provider models claude-glm --json` | exit 0; `glm-5.3` doğrulandı |
| `cd policy-gate; python -m unittest discover -s tests` | exit 0; 41 test |
| `cd windows-browser-automation; python -m unittest discover -s tests` | exit 0; 75 test |
| `cd claude-code-automation; python -m unittest discover -s tests` | exit 0; 10 test |
| `python scripts/mcp_smoke.py` | exit 0; 21 tool |
| `python scripts/production_check.py` | exit 0 |
| `python model_manager.py sor "Araç kullanma. Tek cümle: Chromex Sprint 4 hazır mı?"` | exit 0; yanıt alındı |

Canlı koşudan örnek yanıt: model, o anki çalışma ağacının kirli olduğunu doğru şekilde
bildirdi. Kod commit’inden önce yapıldığı için “hazır değil” cevabı geçerli kanıttır.

## Güvenlik

- `PASEO_API_KEY` kullanılmaz; kimlik doğrulamayı yerel Paseo CLI üstlenir.
- Hata çıktısındaki anahtar kalıpları maskelenir; offline test kırmızısız doğrular.
- Kayıt dışı model reddedilir; çağrı plan modunda ve 210 saniye timeout ile yapılır.
- Kod LOC: **4.991 / 5.000**; tavan aşılmadı.
