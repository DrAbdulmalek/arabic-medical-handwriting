"""معالجة RTL — **تفويض حرفي إلى ocr-core** + سياسة اتجاه على الحافة.

لا يوجد أي منطق إصلاح RTL في هذا المشروع. النسخة المحلية السابقة (المنقولة
من omni-medical-suite) حُذفت عمداً لتفادي نسخة ثالثة متفحتة من نفس الكود.
مصدر الحقيقة الوحيد للإصلاح: ``ocr_core.rtl_utils`` (‏ArabicRTLFixer).

التوافق مع ocr-core الفعلي (تحقق 2026-10-11):
  - دالة الإصلاح الحقيقية: ``fix_text(text, *, force=False)``
    (البدائل fix/fix_rtl تُجرَّب احتياطاً للتوافق مع حقن الاختبارات).
  - ``detect_direction`` غير موجودة في ocr-core إطلاقاً — تُشتق هنا
    كسياسة اتجاه نقية (نطاقات يونيكود العربية) بدون اعتماد على شكل
    الفيكسر: rtl / mixed / ltr.
  - حل كسول (lazy) عند كل نداء حتى تعمل الحقن الوهمية في الاختبارات
    بغضّ النظر عن ترتيب الاستيراد.
"""
from __future__ import annotations

_FIX_METHODS = ("fix_text", "fix", "fix_rtl")  # الحقيقي أولًا ثم بدائل توافق


def _get_fixer():
    from ocr_core.rtl_utils import ArabicRTLFixer

    return ArabicRTLFixer()


def _is_arabic_char(ch: str) -> bool:
    return (
        "\u0600" <= ch <= "\u06FF"
        or "\u0750" <= ch <= "\u077F"
        or "\u08A0" <= ch <= "\u08FF"
        or "\uFB50" <= ch <= "\uFDFF"
        or "\uFE70" <= ch <= "\uFEFF"
    )


def fix_rtl(text: str) -> str:
    """يصحح ترتيب الحروف/الكلمات العربية المعكوسة. تفويض حرفي."""
    fixer = _get_fixer()
    for name in _FIX_METHODS:
        fix = getattr(fixer, name, None)
        if fix is not None:
            return fix(text)
    raise AttributeError(
        "ocr_core.rtl_utils.ArabicRTLFixer بلا fix_text/fix/fix_rtl — "
        "حدّث _FIX_METHODS هنا ليطابق ocr-core"
    )


def detect_direction(text: str) -> str:
    """'rtl' أو 'ltr' أو 'mixed' — سياسة اتجاه نطاقات يونيكود (حافة المشروع)."""
    has_arabic = any(_is_arabic_char(ch) for ch in text)
    has_latin = any(ch.isascii() and ch.isalpha() for ch in text)
    if has_arabic and has_latin:
        return "mixed"
    return "rtl" if has_arabic else "ltr"
