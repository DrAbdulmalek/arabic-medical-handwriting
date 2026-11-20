"""عقد OCRResult المحلي — الواجهة الحالية لكل محركات هذا المستودع.

ملاحظة S2-T3 (قرار المالك 2026-10-08): العقد القانوني الموحد للمحفظة هو
OCRResult في ocr-core (7 حقول). هذا الشكل المحلي يبقى واجهة التشغيل هنا،
والتحويل نحو القانوني عبر ocr/canonical.py::to_canonical مع اختبار
تكافؤ مجمد (tests/test_contract_parity.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class WordBox:
    """كلمة واحدة مع موضعها."""
    text: str
    bbox: tuple[int, int, int, int]     # x1, y1, x2, y2
    confidence: float = 1.0


@dataclass
class OCRResult:
    """نتيجة OCR موحدة — كل محرك يعيد هذا الشكل."""
    # النص
    text: str = ""

    # الكلمات مع مواقعها (قد تكون فارغة)
    words: list[WordBox] = field(default_factory=list)

    # الثقة (0-1)
    confidence: float = 0.0

    # من أي محرك
    engine: str = "unknown"

    # أي لغة
    language: str = "ar"

    # زمن المعالجة بالمللي ثانية
    duration_ms: float = 0.0

    # النص الخام كما أعاده المحرك (قبل التنظيف)
    raw_text: str = ""

    # بيانات إضافية خاصة بالمحرك
    metadata: dict = field(default_factory=dict)

    # تحذيرات وأخطاء
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None

    # متى
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def to_dict(self) -> dict:
        d = asdict(self)
        # حوّل WordBox إلى dict (asdict يفعلها تلقائيًا)
        return d

    def summary(self) -> str:
        """ملخص بشري للعرض."""
        return (
            f"[{self.engine}] {self.word_count} كلمة | "
            f"ثقة: {self.confidence:.0%} | "
            f"{self.duration_ms:.0f}ms"
        )
