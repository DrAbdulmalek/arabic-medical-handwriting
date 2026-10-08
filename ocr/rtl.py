"""معالجة RTL/BiDi — سقالة.

الخطة: نقل `omni-medical-suite/src/ocr/rtl_utils.py` (معالجة عربية نادرة،
لا تُكتب من الصفر). حتى النقل، هذه الوحدة توفر واجهة مستقرة.
"""
from __future__ import annotations


def reshape_arabic(text: str) -> str:
    """يعيد تشكيل العربية للعرض (سقالة — النقل من omni)."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text  # تراجع آمن: بلا reshaping


def detect_direction(text: str) -> str:
    """rtl | ltr | mixed — يعتمد على نسبة الحروف العربية."""
    ar = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    la = sum(1 for c in text if c.isascii() and c.isalpha())
    if ar and la:
        return "mixed"
    return "rtl" if ar >= la else "ltr"
