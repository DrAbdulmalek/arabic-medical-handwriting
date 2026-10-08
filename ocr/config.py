"""إعدادات + قائمة المحركات (سقالة).

الخطة (محادثة 1m3ih8eveq98lv7aqc — msg251): محرك موحّد يلفّ
TrOCR + Tesseract + EasyOCR مع إصلاح Mistral. يُنفذ في engine.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class EngineConfig:
    """قائمة المحركات وأولوياتها."""
    engines: list = field(default_factory=lambda: ["trocr", "tesseract", "easyocr"])
    language: str = "ar"
    # حد الثقة الأدنى — أدناه REVIEW_NEEDED (0.0 = مجهولة، لا تُختلق)
    confidence_floor: float = 0.6
    use_gpu: bool = False


DEFAULT = EngineConfig()
