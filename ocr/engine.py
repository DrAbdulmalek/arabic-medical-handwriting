"""محرك الخط اليدوي — **تفويض كامل إلى ocr-core**.

هذا الملف لا يملك أي منطق OCR. دوره فقط:
  1. بناء قائمة المحركات المطلوبة من ``EngineConfig`` (بناء كسول — لا يُبنى
     محرك إلا عند أول استخدام، والأعطال تُخزَّن ولا تُعاد).
  2. تكييف نتيجة ``ocr_core`` إلى العقد المحلي (``ocr/contract.py``) الذي
     يبقى واجهة المشروع العامة.
  3. فرض سياسة الثقة: ``confidence == 0.0`` تعني *مجهولة* — لا تُختلق أبداً،
     والأخطاء تُبلَّغ عبر ``OCRResult.error`` ولا تُرفع استثناءات.

المصدر الوحيد للحقيقة OCR هو ``ocr-core`` (‏v0.6.0). أي تعديل على منطق
المحركات/التصويت يحدث هناك، لا هنا.
"""
from __future__ import annotations

import importlib
import warnings
from typing import Any

from ocr.config import EngineConfig
from ocr.contract import OCRResult, WordBox

# محركات ocr-core المتاحة كـ extras هناك (paddle/easyocr/tesseract)
_ENGINE_FACTORIES: dict[str, tuple[str, str]] = {
    "tesseract": ("ocr_core.engines.tesseract", "TesseractEngine"),
    "paddle": ("ocr_core.engines.paddle", "PaddleEngine"),
    "easyocr": ("ocr_core.engines.easyocr", "EasyOCREngine"),
}


def _load_engine_class(name: str) -> type:
    module_name, class_name = _ENGINE_FACTORIES[name]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _adapt_words(raw_words: Any) -> list[WordBox]:
    """تكييف كلمات ocr_core إلى WordBox المحلي.

    يقبل كائنات أو dicts — يقرأ الحقول الشائعة فقط ويتجاهل الباقي.
    إن اختلفت أسماء الحقول في ocr-core عدّل هنا وحدها.
    """
    boxes: list[WordBox] = []
    for w in raw_words or []:
        get = w.get if isinstance(w, dict) else lambda k, d=None: getattr(w, k, d)
        text = get("text", "")
        if not text:
            continue
        boxes.append(
            WordBox(
                text=text,
                bbox=get("bbox", get("box")),
                confidence=get("confidence", 0.0),  # 0.0 = مجهولة — لا اختلاق
            )
        )
    return boxes


def _adapt_result(core_result: Any, engine_name: str) -> OCRResult:
    """تكييف OCRResult الخاصة بـ ocr-core إلى العقد المحلي."""
    get = core_result.get if isinstance(core_result, dict) else lambda k, d=None: getattr(core_result, k, d)
    return OCRResult(
        text=get("text", "") or "",
        words=_adapt_words(get("words")),
        confidence=get("confidence", 0.0),
        engine=engine_name,
        error=get("error"),
    )


class HandwritingEngine:
    """واجهة المشروع العامة — تفوّض كل شيء إلى ocr-core.

    الاستخدام::
        engine = HandwritingEngine(EngineConfig(engines=["tesseract", "paddle"]))
        result = engine.process_image("rx.png")
        if result.error: ...        # فشل — لا استثناء
    """

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()
        self._built: dict[str, Any] = {}
        self._failed: set[str] = set()

    # ── بناء كسول ──────────────────────────────
    def _get_engine(self, name: str) -> Any | None:
        if name in self._built:
            return self._built[name]
        if name in self._failed:
            return None
        try:
            engine = _load_engine_class(name)()
        except Exception as exc:  # غياب extra أو تعذر التحميل — ليس فشل صورة
            self._failed.add(name)
            warnings.warn(f"[handwriting] المحرك '{name}' غير متاح: {exc}", stacklevel=2)
            return None
        self._built[name] = engine
        return engine

    def _roster(self) -> dict[str, Any]:
        roster = {}
        for name in self.config.engines:
            engine = self._get_engine(name)
            if engine is not None:
                roster[name] = engine
        return roster

    # ── الواجهة العامة ─────────────────────────
    def process_image(self, image_path: str) -> OCRResult:
        roster = self._roster()
        if not roster:
            return OCRResult(
                text="", confidence=0.0, engine=None,
                error="no_engines_available: لا محرك OCR متاح (ثبّت extras في ocr-core)",
            )
        try:
            if len(roster) == 1:
                name, engine = next(iter(roster.items()))
                return _adapt_result(engine.process_image(image_path), name)
            from ocr_core.engines.ensemble import EnsembleEngine
            best = EnsembleEngine(roster).process_image(image_path)
            # EnsembleEngine يرجع أفضل نتيجة (ثقة×طول×صلاحية) — التكييف يحدد محركها
            for name, engine in roster.items():
                if engine is getattr(best, "_engine", None):
                    return _adapt_result(best, name)
            return _adapt_result(best, "+".join(roster))
        except Exception as exc:
            return OCRResult(text="", confidence=0.0, engine=None, error=f"engine_failure: {exc}")
