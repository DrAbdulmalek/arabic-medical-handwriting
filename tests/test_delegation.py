"""اختبارات التفويض إلى ocr-core — بحقن وحدات وهمية (لا تحتاج محركات فعلية)."""
from __future__ import annotations

import sys
import types

import pytest


def _fake_module(name: str, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


@pytest.fixture
def fake_ocr_core(monkeypatch):
    """يحقن ocr_core وهمياً — يعزل الاختبار عن تثبيت ocr-core الفعلي."""
    captured: dict = {}

    class _CoreResult:
        def __init__(self, text="", confidence=0.0, words=None, error=None):
            self.text, self.confidence, self.words, self.error = text, confidence, words or [], error

    class _Tess:
        def process_image(self, path):
            captured["tess_path"] = path
            return _CoreResult(text="دواء 500 مجم", confidence=0.0)  # ثقة مجهولة عمداً

    class _RTLFixer:
        def fix(self, t): return t[::-1]
        def detect_direction(self, t): return "rtl"

    class _Fields:
        def extract_fields(self, t): return {"dose": "500", "name": "دواء"}

    pkg = _fake_module("ocr_core")
    engines_pkg = _fake_module("ocr_core.engines")
    _fake_module("ocr_core.engines.tesseract", TesseractEngine=_Tess)
    _fake_module("ocr_core.rtl_utils", ArabicRTLFixer=_RTLFixer)
    _fake_module("ocr_core.postprocess")
    _fake_module("ocr_core.postprocess.field_extractor", ArabicMedicalFieldExtractor=_Fields)
    _fake_module("ocr_core.postprocess.normalization", normalize_for_search=lambda t: t.strip())
    injected = [
        "ocr_core", "ocr_core.engines", "ocr_core.engines.tesseract",
        "ocr_core.rtl_utils", "ocr_core.postprocess",
        "ocr_core.postprocess.field_extractor", "ocr_core.postprocess.normalization",
    ]
    yield captured
    # تنظيف إلزامي بعد الاختبار (teardown): الوحدات الوهمية تُزال حتى لا تسرّب
    # إلى بقية جلسة pytest (طبّقنا: normalize/fields في test_stubs فشلا بسبب الترتيب)
    for name in injected:
        sys.modules.pop(name, None)


def test_engine_delegates_and_marks_unknown_confidence(fake_ocr_core, tmp_path):
    from ocr.config import EngineConfig
    from ocr.engine import HandwritingEngine

    engine = HandwritingEngine(EngineConfig(engines=["tesseract"]))
    result = engine.process_image(str(tmp_path / "rx.png"))

    assert fake_ocr_core["tess_path"].endswith("rx.png")
    assert result.text == "دواء 500 مجم"
    assert result.confidence == 0.0          # المجهولة تبقى مجهولة — لا اختلاق
    assert result.error is None


def test_no_engines_returns_error_not_exception(fake_ocr_core):
    from ocr.config import EngineConfig
    from ocr.engine import HandwritingEngine

    engine = HandwritingEngine(EngineConfig(engines=["paddle"]))  # غير محقون = غير متاح
    result = engine.process_image("x.png")
    assert result.error is not None
    assert result.confidence == 0.0


def test_fields_delegation_and_dose_guard(fake_ocr_core):
    from extract.fields import extract_doses, extract_fields

    assert extract_fields("أي نص") == {"dose": "500", "name": "دواء"}
    assert extract_doses("أي نص") == {"dose": "500"}  # الجرعة فقط — الحارس يعمل


def test_rtl_delegation(fake_ocr_core):
    from ocr.rtl import detect_direction, fix_rtl

    assert fix_rtl("abc") == "cba"
    assert detect_direction("أي شيء") == "rtl"


def test_normalize_delegation(fake_ocr_core):
    from ocr.normalize import normalize_for_search

    assert normalize_for_search("  نص  ") == "نص"
