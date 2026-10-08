"""تطبيع النص العربي — سقالة.

الخطة: نقل `omni-medical-suite/src/ocr/normalization.py` (40+ mapping،
تشكيل، خلط عربي/إنجليزي). حتى النقل، واجهة مستقرة.

ملاحظة: هذا "تطبيع للبحث/المطابقة" — لا يغيّر النص القانوني المحفوظ
(canonical preserved) وفق سياسة ocr-core.
"""
from __future__ import annotations
import re

_DIACRITICS = re.compile(r"[\u064B-\u0652\u0670]")


def normalize_for_search(text: str) -> str:
    """تطبيع غير مدمر للمطابقة (تشكيل + أليفات + مسافات)."""
    t = _DIACRITICS.sub("", text or "")
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ى", "ي").replace("ة", "ه")
    t = re.sub(r"\s+", " ", t)
    return t.strip()
