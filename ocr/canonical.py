"""جسر العقد القانوني (S2-T3 shim) — إعادة تصدير/تحويل نحو عقد ocr-core.

قرار المالك 2026-10-08 (خطة الجاهزية للإنتاج §1.1): العقد القانوني الموحد
هو **OCRResult في ocr-core** (7 حقول) — الفائز بعدد المستهلكين الحقيقيين
الآن، **لا** تصميم ثالث مدمج. المستودع الخاسر (هذا المستودع) يحصل على
shim إعادة تصدير: تحويل أمين من الشكل المحلي (11 حقلًا) إلى الشكل
القانوني، دون حذف أي حقل (الفائض يذهب إلى ``meta``).

الاتجاه المستقبلي: إعادة تصدير مباشرة (``from ocr_core.engines.base
import OCRResult``) بعد اكتمال ترحيل المحركات — هذا الجسر يثبّت الخريطة
القانونية الآن ويجعل أي انزلاق يُكتشف بالاختبار (test_contract_parity).
"""
from __future__ import annotations

from typing import Any

from .contract import OCRResult

try:  # pragma: no cover - يعتمد على بيئة التثبيت
    from ocr_core.engines.base import OCRResult as CanonicalOCRResult

    HAS_OCR_CORE = True
except ImportError:  # ocr-core غير مثبت — التدهور آمن وموثق
    CanonicalOCRResult = None
    HAS_OCR_CORE = False

# مجموعة الحقول القانونية المجمدة (ocr-core/src/ocr_core/engines/base.py:15)
CANONICAL_FIELDS = ("text", "engine", "confidence", "processing_time", "error", "pages", "meta")


def to_canonical(result: OCRResult) -> Any:
    """حوّل نتيجة AMH المحلية إلى الشكل القانوني.

    الخريطة (شاملة — كل حقل محلي يهبط في مكان موثق):
      text→text · engine→engine · confidence→confidence · error→error
      duration_ms→processing_time (تحويل وحدة ms→ثوانٍ؛ وحدة
      processing_time القانونية = ثوانٍ)
      words→meta["words"] · language→meta["language"] ·
      raw_text→meta["raw_text"] · warnings→meta["warnings"] ·
      created_at→meta["created_at"]
      metadata (dict محلي) يُدمج في meta، ومفاتيح AMH الصريحة تنتصر عند التعارض.
      pages لا يملكه AMH → القيمة القانونية الافتراضية 1.

    يعيد ``CanonicalOCRResult`` إن كان ocr-core مثبتًا، وإلا dictًا
    بمفاتيح الحقول القانونية نفسها (تدهور آمن للاختبار والمعاينة).
    """
    meta: dict[str, Any] = dict(result.metadata or {})
    meta.update({
        "words": result.words,
        "language": result.language,
        "raw_text": result.raw_text,
        "warnings": list(result.warnings),
        "created_at": result.created_at,
    })
    values = {
        "text": result.text,
        "engine": result.engine,
        "confidence": result.confidence,
        # وحدة processing_time القانونية: ثوانٍ — AMH يوثق duration_ms بالمللي ثانية
        "processing_time": result.duration_ms / 1000.0,
        "error": result.error,
        "pages": 1,
        "meta": meta,
    }
    if HAS_OCR_CORE:
        return CanonicalOCRResult(**values)
    return values
