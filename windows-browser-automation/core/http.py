"""Geriye uyumluluk köprüsü — asıl modül v0.4'te policygate.http'e taşındı.

`requests` bağımlılığı policygate[http] extra'sı üzerinden gelir; wba'nın
requirements.txt zaten requests içerdiğinden davranış değişmez.
"""
from policygate.http import HttpError, request_json

__all__ = ["HttpError", "request_json"]