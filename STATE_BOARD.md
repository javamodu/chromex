# STATE_BOARD — chromex

## Aktif iş
Yok (Sprint 2 tamamlandı; tek insan işi PyPI trusted publisher kaydı).

## Son damgalar
- 2026-10-25 · Sprint 2: `mcp_server/` adaptörü kuruldu — 20 CLI komutu MCP tool'ı, `MCPApprovalChannel` fail-closed onay köprüsü, `chromex-mcp` giriş noktası, `[mcp]` optional extra; testler 35+53=88 yeşil
- 2026-10-12 · İskelet kuruldu (katman-kur.ps1): L1+L5 dosyaları + plans/handoff + kararlar + raporlar dizinleri
- 2026-10-14 · Gece vardiyası: 2 subagent (CLI insan-testi + drift/plugin) → QA raporu %100 kapandı: 5/5 P1 (EOF fail-closed, tek-satır hata, cp1252, preflight kapısı, google import guardu) + 6/6 işlevsel P2 (BOM toleransı, retry görünürlüğü, exit 3, boş-sonuç mesajı, ok karakterleri, arg help'leri); testler 35+42=77 yeşil; plugin iskeleti kuruldu (.claude-plugin + skills/chromex-sozlesme)

## Bekleyen onaylar
- PyPI trusted publisher kaydı (insan işi): policy-gate / javamodu / chromex / publish-policygate.yml / env `pypi`; sonra `gh run rerun --failed`.
