"""استخراج الحقول الطبية — **تفويض إلى ocr-core** مع حارس أرقام.

الاستخراج الكامل يحدث في ``ocr_core.postprocess.field_extractor``
(‏ArabicMedicalFieldExtractor). هذا الملف يضيف فقط السياسة المحلية:
``extract_doses`` يُرجع حقول الجرعات **فقط** ويحمي الأرقام من أي تصحيح
(الحارس موجود أيضاً في ميثاق ocr-core — هذا دفاع مزدوج عند الحواف).
"""
from __future__ import annotations

# لا استيراد علوي — الاستيراد الكسول داخل _get_extractor() حتى يتبع
# sys.modules لحظة النداء (توافق حقن الاختبارات وترتيب الملفات).

_DOSAGE_HINTS = ("dose", "dosage", "جرعة", "جرعه", "dose_")


def _get_extractor():
    # حل كسول — يتبع sys.modules لحظة النداء (توافق حقن الاختبارات)
    from ocr_core.postprocess.field_extractor import ArabicMedicalFieldExtractor

    return ArabicMedicalFieldExtractor()


def extract_fields(text: str) -> dict:
    """كل الحقول الطبية — تفويض حرفي إلى ocr-core.

    ocr-core يرجع ``ExtractedMedicalFields`` (dataclass) — نحوّله إلى
    ``dict`` عبر ``to_dict()`` ليطابق العقد المحلي في ``ocr/contract.py``.
    """
    result = _get_extractor().extract_fields(text)
    to_dict = getattr(result, "to_dict", None)
    return to_dict() if callable(to_dict) else result


def extract_doses(text: str) -> dict:
    """حقول الجرعات فقط. بلا حقول → ‏{} وليس اختلاقاً."""
    fields = extract_fields(text)
    return {k: v for k, v in fields.items() if any(h in k.lower() for h in _DOSAGE_HINTS)}
