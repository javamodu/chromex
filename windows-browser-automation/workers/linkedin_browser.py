"""LinkedIn tarayıcı okuyucusu — AÇIK OTURUMDAN salt-okunur veri çekme.

Resmi API'nin vermediği şeyler (akış, kişi/iş arama) için: oturum açık
otomasyon Chrome'una (scripts\\start-chrome-automation.ps1, CDP
127.0.0.1:9222) Playwright ile bağlanır ve YALNIZCA okur. Beğenme, bağlantı
isteme, mesaj atma gibi hiçbir etkileşim YOKTUR; login sayfalarına dokunmaz
(giriş yoksa hata verir, kullanıcının elle girmesini ister).

RİSKLER (bilinçli karar):
- LinkedIn kullanım koşulları otomatik erişimi kısıtlar; salt-okunur da olsa
  hesap kısıtı riski vardır. Düşük hacimde, seyrek ve yavaş kullanın.
- LinkedIn DOM'u sık değişir; seçiciler kırılgandır. Okuma bozulursa bu
  dosyadaki seçicilere bakın. API'nin kapsadığı işlerde her zaman API
  tercih edilir (bkz. linkedin_worker.py).

Gereken: pip install playwright (tarayıcı indirmeye gerek yok; mevcut
Chrome'a CDP ile bağlanır). Önce start-chrome-automation.ps1 ile otomasyon
profilini açıp LinkedIn'e elle giriş yapın.
"""
from __future__ import annotations

import json
from urllib.parse import quote

from core import audit, store

WORKER = "linkedin"
CDP_URL = "http://127.0.0.1:9222"
_MAX_SCROLLS = 15


def _browser():
    """Açık Chrome'a CDP ile bağlanır (playwright lazy import: test/CI'de
    bu modül playwright kurulu olmadan da yüklenebilir)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "playwright kurulu değil: pip install playwright "
            "(tarayıcı indirmek gerekmez; CDP ile mevcut Chrome'a bağlanılır)."
        ) from exc
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
    except Exception:
        pw.stop()
        raise RuntimeError(
            f"CDP'ye bağlanılamadı ({CDP_URL}) — önce "
            "scripts\\start-chrome-automation.ps1 ile otomasyon Chrome'unu açın."
        )
    if not browser.contexts:
        pw.stop()
        raise RuntimeError("CDP bağlantısında oturum context'i bulunamadı.")
    return pw, browser


def _new_tab(browser):
    """Kullanıcının açık sekmesine dokunmaz; aynı oturum context'inde (cookie
    paylaşımlı) YENİ sekme açar. İş bitince sekme kapatılır."""
    return browser.contexts[0].new_page()


def _require_logged_in(page) -> None:
    if "login" in page.url or "authwall" in page.url:
        raise RuntimeError(
            "LinkedIn oturumu yok — otomasyon Chrome'unda LinkedIn'e elle "
            "giriş yapın (otomasyon login sayfalarına dokunmaz)."
        )


def _close(pw, browser, page) -> None:
    try:
        page.close()
    except Exception:
        pass
    browser.close()  # CDP bağlantısını keser; Chrome'u KAPATMAZ.
    pw.stop()


def feed(limit: int = 20) -> list[dict]:
    """Akıştan son gönderileri okur (salt-okunur)."""
    audit.log_event("linkedin_feed_read", WORKER, "READ", "auto",
                    {"limit": limit, "yol": "cdp"})
    pw, browser = _browser()
    page = _new_tab(browser)
    items: list[dict] = []
    seen: set[str] = set()
    try:
        page.goto("https://www.linkedin.com/feed/",
                  wait_until="domcontentloaded")
        page.wait_for_selector("main", timeout=15000)
        _require_logged_in(page)
        for _ in range(_MAX_SCROLLS):
            for post in page.query_selector_all("div.feed-shared-update-v2"):
                urn = post.get_attribute("data-urn") or ""
                if urn in seen:
                    continue
                seen.add(urn)
                text_el = post.query_selector(
                    ".update-components-text, "
                    ".feed-shared-inline-show-more-text")
                actor_el = post.query_selector(
                    ".update-components-actor__title")
                text = (text_el.inner_text() if text_el
                        else post.inner_text() or "").strip()
                if not text:
                    continue
                item = {
                    "urn": urn,
                    "yazar": (actor_el.inner_text().strip()
                              if actor_el else ""),
                    "metin": text[:1000],
                }
                items.append(item)
                store.save(WORKER, "feed_post", urn,
                           f"{item['yazar']}: {text[:80]}",
                           json.dumps(item, ensure_ascii=False))
                if len(items) >= limit:
                    break
            if len(items) >= limit:
                break
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(1500)
        return items[:limit]
    finally:
        _close(pw, browser, page)


_SEARCH_KINDS = {"people", "posts", "jobs", "companies"}


def search(query: str, limit: int = 10, kind: str = "people") -> list[dict]:
    """Kişi/gönderi/iş araması sonuçlarını okur (salt-okunur)."""
    kind = kind.lower()
    if kind not in _SEARCH_KINDS:
        raise ValueError(f"kind şunlardan biri olmalı: {sorted(_SEARCH_KINDS)}")
    audit.log_event("linkedin_search_read", WORKER, "READ", "auto",
                    {"query": query, "limit": limit, "kind": kind})
    pw, browser = _browser()
    page = _new_tab(browser)
    items: list[dict] = []
    try:
        page.goto(
            f"https://www.linkedin.com/search/results/{kind}/"
            f"?keywords={quote(query)}",
            wait_until="domcontentloaded")
        page.wait_for_selector("main", timeout=15000)
        _require_logged_in(page)
        page.wait_for_timeout(2000)
        for card in page.query_selector_all(
                "li.reusable-search__result-container, "
                "div.entity-result"):
            name_el = card.query_selector(
                ".entity-result__title-text span[aria-hidden='true']")
            sub_el = card.query_selector(".entity-result__primary-subtitle")
            link_el = card.query_selector("a.app-aware-link[href]")
            name = name_el.inner_text().strip() if name_el else ""
            text = (card.inner_text() or "").strip()
            if not name and not text:
                continue
            item = {
                "ad": name,
                "alt_bilgi": sub_el.inner_text().strip() if sub_el else "",
                "link": (link_el.get_attribute("href") or "").split("?")[0]
                        if link_el else "",
                "metin": text[:500],
            }
            items.append(item)
            store.save(WORKER, f"search_{kind}", item["link"] or None,
                       item["ad"] or item["metin"][:80],
                       json.dumps(item, ensure_ascii=False))
            if len(items) >= limit:
                break
        return items
    finally:
        _close(pw, browser, page)
