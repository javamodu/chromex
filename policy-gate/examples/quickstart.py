"""policygate hizli baslangic — 60 saniyede onay kapisi.

Calistirma: python examples/quickstart.py
(Hicbir sey gondermez; SEND adimi etkilesimsiz ortamda reddedilir.)
"""

from policygate import ActionRequest, ApprovalDenied, audit, preflight, require

# 1) READ seviyesi: politikada varsayilan "auto" — sessizce gecer
require(ActionRequest(
    worker="ornek", action="ornek.oku", level="READ",
    summary="Sadece okuma — onay istenmez",
))

# 2) SEND seviyesi: once preflight (ag oncesi kesin redler), sonra require
istek = ActionRequest(
    worker="ornek", action="ornek.gonder", level="SEND",
    summary="ornek.com'a gonderim YAPILACAK",
    details={"boyut": "1.2 KB"},
)
try:
    preflight(istek)      # policy-deny / etkilesimsiz red burada patlar
    require(istek)        # etkilesimli oturumda birebir 'EVET' ister
except ApprovalDenied as exc:
    print(f"Reddedildi (beklenen): {exc}")

# 3) Audit zinciri bütünlügü
ok, mesaj = audit.verify_chain()
print(("SAGLAM" if ok else "BOZUK"), "-", mesaj)
