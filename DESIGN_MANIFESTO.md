# TASARIM MANİFESTOSU — Chromex

## Felsefe

Chromex, **az kodla çok iş** yapan bir otomasyon çekirdeğidir. Hedef:
- Küçük tutmak
- Keskin tutmak
- Kanıtlı tutmak
- Güvenliği pazarlık etmeden korumak

## İlkeler

1. **Dikey keskinlik:** Her parça uçtan uca çalışmalı.
2. **Kanıt:** “Yaptım” değil, “exit 0 + test yeşil + commit hash” geçerli.
3. **Fail-closed:** Şüphe varsa reddet.
4. **Tek kaynak:** Aynı bilgi iki yerde yaşamaz.
5. **Offline test:** Ağ ve servis bağımlılığı testleri sahte ile çözülür.
6. **Küçük yüzey:** Kullanıcıya az ama net komut sunulur.
7. **Güvenlik önce:** Kolaylık için güvenlik feda edilmez.

## LOC disiplini

LOC bir başarı ölçütü değildir. Depo, **9.000 toplam LOC** tavanını aşamaz.
Yeni iş açılmadan önce:

1. Gerekli tahmini LOC yazılır.
2. Tavan altı kalıp kalmadığı kontrol edilir.
3. Aşım varsa iş bölünür veya Faz 3’e ertelenir.

## Kalite ölçütleri

- Tüm testler yeşil.
- `py_compile` temiz.
- `git diff --check` temiz.
- Audit zinciri sağlam.
- Çalışma ağacı temiz.
- CI yeşil.

## Anti-hedefler

- Şişmiş UI
- Gereksiz soyutlama
- Kopya güvenlik kodu
- Canlı servis testi olmayan yeşil iddiası
- Açık uçlu “yakında” kartları
