# ANAYASA — Chromex

## Amaç

Bu depo, **küçük, keskin, kanıtlı ve güvenlik önce** çalışan bir otomasyon
çekirdeği üretir. Hedef, her şeyi yazmak değil; en kritik acıyı en az kodla
çözmektir.

## Kapsam

- `policy-gate/` — güvenlik çekirdeği
- `windows-browser-automation/` — servis ve tarayıcı otomasyonu
- `claude-code-automation/` — ajan döngüsü ve model yönetimi
- `plans/`, `docs/`, `raporlar/` — kalıcı bilgi katmanları

## LOC tavanı

Bu depo için **sert tavan** aşağıdadır:

| Tür | Tavan | Mevcut | Kalan |
|---|---:|---:|---:|
| Toplam | 9.000 | 7.815 | 1.185 |
| Kod | 5.000 | 4.210 | 790 |
| Doküman | 3.500 | 3.317 | 183 |
| Yapılandırma + destek | 300 | 288 | 12 |

Mevcut ölçüm 2026-10-29'de `git ls-files --cached --others
--exclude-standard` ile yapıldı. Sayıma kod, doküman, yapılandırma ve
destek metinleri girer; derleme/çalışma artıkları ve gizli veri girmez.

Bu tavanlar aşılırsa:

1. Yeni iş açılamaz.
2. Mevcut iş bölünür veya iptal edilir.
3. Faz 2’den Faz 3’e geçiş ancak tavan yeniden değerlendirilerek yapılır.

## Değişmez kurallar

1. **Güvenlik önce:** Dış etki yaratan her işlem onay kapısından geçer.
2. **Fail-closed:** Etkileşimsiz ortamda SEND/DELETE reddedilir.
3. **Audit:** Her karar hash zincirine yazılır.
4. **Tek kaynak:** Güvenlik çekirdeği yalnızca `policygate` içinde yaşar.
5. **Offline test:** Yeni davranış, offline test olmadan merge edilemez.
6. **Türkçe:** Kod, doküman, yorum ve commit mesajları Türkçedir.
7. **LF:** Satır sonu LF’dir; CRLF yazılmaz.
8. **Sıfır bağımlılık:** policygate çekirdeği stdlib-only kalır.

## SSOT hiyerarşisi

1. `ANAYASA.md`
2. `AGENTS.md`
3. `DESIGN_MANIFESTO.md`
4. `GLOSSARY.md`
5. `plans/FAZ2-SPRINTLER.md`
6. `README.md`
7. `STATE_BOARD.md`
8. Kod ve testler

Çelişki olursa üst sıradaki dosya kazanır.

## Değişiklik süreci

- Küçük değişiklik: tek commit, tek dosya kümesi.
- Mimari değişiklik: `plans/handoff/` altında yeni karar kaydı.
- LOC tavanı değişikliği: yalnızca insan onayıyla.
- Doküman değişikliği: aynı commit’te test/CI senkronu.

## İhlal politikası

- Tavan aşılırsa iş durdurulur.
- Test kırmızıysa yeni feature açılmaz.
- Audit zinciri bozuksa canlıya çıkılmaz.
- Secret sızıntısı varsa acil düzeltilir.
