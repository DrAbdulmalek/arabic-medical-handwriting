"""التطبيع العربي — **تفويض إلى ocr-core** (‏non-destructive للعرض).

التطبيع هنا مخصص للمطابقة/البحث فقط، ولا يمس النص الأصلي المعروض.
مصدر الحقيقة: ``ocr_core.postprocess.normalization``.

التوافق مع ocr-core الفعلي (تحقق 2026-10-11): الدوال الحقيقية
``arabic_normalize`` (خفيف — للمطابقة) و``arabic_strong_normalize``
(مع القاموس الطبي). لا وجود لـ normalize_for_search/normalize هناك.
الحل كسول عند كل نداء — يتبع ما هو مسجّل في sys.modules لحظة النداء
(يدعم حقن ocr_core الوهمي في الاختبارات بغضّ النظر عن ترتيب الاستيراد).
"""
from __future__ import annotations

import importlib

# مسارات محتملة حسب تطور ocr-core — جرّبها بالترتيب (الحقيقي أولًا)
_CANDIDATES = [
    ("ocr_core.postprocess.normalization", "arabic_normalize"),
    ("ocr_core.postprocess.normalization", "arabic_strong_normalize"),
    ("ocr_core.postprocess.normalization", "normalize_for_search"),
    ("ocr_core.postprocess.normalization", "normalize"),
]


def _resolve():
    for module_name, func_name in _CANDIDATES:
        try:
            return getattr(importlib.import_module(module_name), func_name)
        except (ImportError, AttributeError):
            continue
    raise ImportError(
        "تعذر إيجاد دالة التطبيع في ocr-core. افحص ocr_core/postprocess/normalization.py "
        "وحدّث قائمة _CANDIDATES في ocr/normalize.py"
    )


def normalize_for_search(text: str) -> str:
    """تطبيع آمن للمطابقة — تفويض حرفي إلى ocr-core. لا يدمر الأصل."""
    return _resolve()(text)
