# FAZ 2 — SPRINTLER

> Kaynak sırası: `ANAYASA.md`, `AGENTS.md`, `DESIGN_MANIFESTO.md`.
> Her sprint tek konu, tek çıktı ve **canlı doğrulama** ile kapanır.

## Kapsam

Faz 2, ürünleşme kanıtı üretir: yerel wheel doğrulaması, gerçek MCP
istemcisi, gerçek Canva export akışı ve küçük bir zamanlayıcı. Yeni entegrasyon
açmak, görsel panel yazmak veya geniş refactor yapmak yoktur.

## LOC bütçesi

| Sprint | Kod | Doküman | Yapılandırma | Toplam |
|---|---:|---:|---:|---:|
| 1 — Yerel wheel + MCP canlı kanıt | 180 | 40 | 0 | 220 |
| 2 — Canva canlı export | 240 | 40 | 0 | 280 |
| 3 — Zamanlayıcı + canlı koşum | 210 | 40 | 0 | 250 |
| 4 — Model API canlı çağrı + teslim | 110 | 50 | 0 | 160 |
| **Plan toplamı** | **740** | **170** | **0** | **910** |
| **Kategori bütçesi kalır** | 0 | 131 | 44 | — |

Toplam tavanın kalan payı **375 LOC**'dir; bunun **200 LOC**'u yalnız toplam
tavanından gelir. Kategori bütçeleri ayrı olarak bağlayıcıdır.

Tavan dağılımı: 5.000 kod / 3.500 doküman / 300 yapılandırma ve destek.
Sprint toplamları tavanı değil, tavanın altındaki hedef bütçeyi gösterir.
Yapılandırma satırı 44 LOC kalıncaya kadar kullanılmıştır; yeni config
dosyası açılmaz.

## Sprint kuralları

1. Sprint açılmadan önce tahmini LOC bu dosyaya yazılır.
2. Sprint kapanışında offline testler **exit 0** olmalıdır.
3. Sprint kapanışında canlı test komutu ve gerçek çıktısı kayda girer.
4. Canlı test yapılamazsa sprint kapanamaz; engel `STATE_BOARD.md`'e yazılır.
5. SEND/DELETE canlı testi yalnızca insan onayıyla koşar.
6. Sprint bitince `STATE_BOARD.md`'e commit hash'li tek satır damga atılır.

## Sprint 1 — Yerel wheel + gerçek MCP istemcisi

**Hedef:** policygate wheel'ini yerelde derle, GitHub Release'e ekle, chromex-mcp'yi gerçek MCP SDK ile doğrula.

**İşler**
- Yerel: `python -m build ./policy-gate` ile wheel üret.
- Yayın: `v1.1.0` için taslak GitHub Release'e wheel'i ekle; PyPI kullanılmaz.
- Kod: `scripts/mcp_smoke.py` ile stdio üzerinden 21 tool listele.
- Doküman: kullanıcıya MCP client yapılandırma örneği README'ye ekle.

**Canlı test**

```powershell
cd windows-browser-automation
python -m pip install build
python -m build ../policy-gate
python -m pip install --force-reinstall ../policy-gate/dist/policy_gate-1.1.0-py3-none-any.whl
python -c 'import policygate; assert policygate.__version__ == "1.1.0"'
python -m pip install -e ".[mcp]"
python scripts/mcp_smoke.py
python scripts/local_release.py --tag v1.1.0
```

**Kabul**
- `policy-gate/dist/` içinde 1.1.0 wheel bulunur.
- GitHub Release `v1.1.0` wheel dosyasını içerir.
- Yerel wheel kurulumu ve import başarılı.
- `mcp_smoke.py` exit 0 döner ve 21 tool listeler.
- Offline testler 36+62+7 = 105 geçer.

## Sprint 2 — Canva gerçek export

**Hedef:** Canva worker'ını tek HTTP çekirdeğinde birleştir ve gerçek dosya üret.

**İşler**
- `policygate.http`'ye `request_bytes` ekle; retry, redaksiyon ve audit korunsun.
- `canva_worker._download` doğrudan `requests` kullanmayı bırak.
- İndirme hataları ve kısmi dosya temizliği için offline testler ekle.
- `local_release.py --execute` için MODIFY onay kapısı ekle.
- `scripts/production_check.py` ile sürüm, policy, audit ve registry doğrula.
- Canlı akış için tasarım kimliği insan tarafından sağlanır.

**Canlı test**

```powershell
$env:CANVA_DESIGN_ID = "CANVA_DESIGN_KIMLIGI"
python -m orchestrator.cli canva-export $env:CANVA_DESIGN_ID --format pdf
Get-Item data\canva\*.pdf | Where-Object Length -gt 0
python -m orchestrator.cli audit-dogrula
```

**Kabul**
- En az bir PDF dosyası 0 bayttan büyük olur.
- Dosya adı tasarım kimliğini taşır.
- Audit zinciri sağlamdır.
- Secret çıktıda görünmez.
- `production_check.py` exit 0 döner.

## Sprint 3 — Zamanlayıcı ve canlı koşum

**Hedef:** READ/DRAFT işleri için küçük, dosya tabanlı zamanlayıcı.

**İşler**
- `workers/scheduler.py` ekle: JSON iş tanımı, tek seferlik koşum.
- `zamanla` CLI komutu ekle; varsayılan politika READ/DRAFT ile sınırlı.
- SEND/DELETE zamanlanamaz; preflight ve audit korunur.
- Offline testler: reddedilen seviye, kırık JSON, zaman aşımı, kayıt.

**Canlı test**

```powershell
Set-Content data\sprint3-job.json '{"komut":"github-arastir","args":["chromex"],"seviye":"READ"}'
python -m orchestrator.cli zamanla --dosya data\sprint3-job.json
python -m orchestrator.cli son-kayitlar --limit 3
```

**Kabul**
- Zamanlanmış READ komutu gerçek CLI çağrısıyla exit 0 döner.
- Sonuç SQLite deposunda görünür.
- SEND/DELETE job reddedilir ve red audit'e yazılır.
- Offline testler 123+ seviyesine çıkar; sayaç senkronu güncellenir.

## Sprint 4 — Model API canlı çağrı ve teslim

**Hedef:** `glm-5.3` varsayılan modeliyle gerçek API çağrısı ve teslim paketi.

**İşler**
- `model_manager.py`'ye `sor` komutu ekle; yalnız kayıtlı model kullanır.
- Kimlik doğrulamayı yerel Paseo CLI üstlenir; `PASEO_API_KEY` varsayımı geçersizdir.
- Offline test: kayıt dışı model, hata yanıtı, secret redaksiyonu.
- Teslim: sprint kanıtlarını `raporlar/2026-10-29-faz2/` altına yaz.

**Canlı test**

```powershell
python claude-code-automation/model_manager.py default
python claude-code-automation/model_manager.py sor "Araç kullanma. Tek cümle: Chromex Sprint 4 hazır mı?"
```

**Kabul**
- Yanıt `glm-5.3`'ten gelir ve terminale yazılır.
- Kimlik doğrulama Paseo CLI ile canlı olarak kanıtlandı.
- Canlı test komutları ve exit kodları kalıcı rapora yazılır.
- Çalışma ağacı temiz, CI yeşil, remote senkron.

## Faz 2 dışı

Aşağıdakiler tavan aşımı veya kapsam şişmesi nedeniyle Faz 3'e bırakılır:

- Web panel
- Yeni servis entegrasyonları
- Genel DOM scraping çerçevesi
- Desktop worker genişletmesi
- Çok kullanıcılı hesap yönetimi
