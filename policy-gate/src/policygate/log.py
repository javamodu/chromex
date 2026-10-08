"""Tek noktadan loglama — stderr'e, seviye OTOMASYON_LOG ile ayarlanır
(DEBUG/INFO/WARNING; varsayılan WARNING, yani sessiz).

Not: Kullanıcıya dönük çıktılar (onay banner'ı, CLI sonuçları) print'te
kalır — bu modül yalnızca operasyonel teşhis içindir (retry, bekleme...).
"""
from __future__ import annotations

import logging
import os


def get(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(os.environ.get("OTOMASYON_LOG", "WARNING").upper())
    return logger
