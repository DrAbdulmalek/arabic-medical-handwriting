"""محرك OCR موحّد — سقالة (multi-engine: TrOCR + Tesseract + EasyOCR).

الخطة (محادثة 1m3ih8eveq98lv7aqc — msg251):
  - لفّ المحركات خلف واجهة واحدة تُعيد OCRResult (من contract.py).
  - إصلاح Mistral: لا تُختلق ثقة (0.0 = مجهولة).
  - الترتيب: TrOCR (خط يدوي) ← EasyOCR ← Tesseract (احتياطي).

حتى التنفيذ الكامل، يمكن الاعتماد على `ocr-core` المركزي مباشرة:
    pip install "marathon-ocr-core[paddle]"
    from ocr_core.engines.tesseract import TesseractEngine

هذه الوحدة تبقى import-safe (لا تحمّل نماذج عند الاستيراد).
"""
from __future__ import annotations
import logging
import time
from typing import Optional

from .contract import OCRResult
from .config import EngineConfig, DEFAULT

logger = logging.getLogger(__name__)


class HandwritingEngine:
    """محرك موحّد — يلفّ المحركات المتاحة ويُعيد OCRResult."""

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or DEFAULT
        self._backends: dict = {}

    def available(self) -> list:
        """قائمة المحركات المتاحة فعليًا في هذه البيئة."""
        avail = []
        try:
            import pytesseract, shutil
            if shutil.which("tesseract"):
                avail.append("tesseract")
        except Exception:
            pass
        try:
            import easyocr  # noqa
            avail.append("easyocr")
        except Exception:
            pass
        try:
            import transformers, torch  # noqa
            avail.append("trocr")
        except Exception:
            pass
        return avail

    def process_image(self, image_path: str) -> OCRResult:
        """OCR لصورة — يستخدم أول محرك متاح (سقالة: tesseract)."""
        start = time.perf_counter()
        engines = self.available()
        if not engines:
            return OCRResult(
                engine="none", error="لا محرك متاح — ثبّت tesseract/easyocr/trocr",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        # المسار الافتراضي الحالي: tesseract (الأخف). TrOCR يُضاف عند التنفيذ.
        try:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(image_path),
                                               lang=self.config.language)
            return OCRResult(
                text=text.strip(), raw_text=text, engine="tesseract",
                confidence=0.0,  # tesseract عبر image_to_string: مجهولة (0.0)
                language=self.config.language,
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as e:
            return OCRResult(
                engine="tesseract", error=f"{type(e).__name__}: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )
