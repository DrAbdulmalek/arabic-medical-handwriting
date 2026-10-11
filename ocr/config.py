"""إعداد المحرك — قائمة المحركات وحد الثقة.

سياسة الثقة: ‏confidence == 0.0 تعني *مجهولة* ولا تُختلق أبداً
(موروثة من ocr-core وهي نفسها تُفرض في ocr/engine.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EngineConfig:
    engines: list[str] = field(default_factory=lambda: ["tesseract", "easyocr", "paddle"])
    confidence_threshold: float = 0.0  # 0.0 = لا حد — الثقة المجهولة مسموحة لكن موسومة
