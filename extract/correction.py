"""تصحيح أخطاء OCR العربية — سقالة (يفوّض إلى ocr-core).

الخطة: استخدام `ocr_core.postprocess.corrections_ar.ArabicMedicalCorrections`
(311+ زوجًا) بدل إعادة البناء.
"""
from __future__ import annotations


def correct_arabic(text: str) -> tuple:
    """يعيد (النص المصحح، عدد التصحيحات). يفوّض إلى ocr-core إن توفّر."""
    try:
        from ocr_core.postprocess.corrections_ar import ArabicMedicalCorrections
        return ArabicMedicalCorrections().apply(text)
    except Exception:
        return text, 0
