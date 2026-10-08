"""استخراج حقول طبية (اسم/جرعة/تشخيص…) — سقالة.

الخطة: نقل `omni-medical-suite/src/ocr/field_extractor.py` (NER extraction).
"""
from __future__ import annotations
import re

_DOSE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|وحدة|IU)\b", re.IGNORECASE)


def extract_doses(text: str) -> list:
    """يستخرج الجرعات (رقم + وحدة) — حارس الأرقام الطبي."""
    return [{"value": m.group(1), "unit": m.group(2)} for m in _DOSE_RE.finditer(text or "")]
