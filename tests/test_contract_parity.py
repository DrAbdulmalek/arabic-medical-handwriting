"""اختبار تكافؤ العقد (S2-T3) — يمنع الانزلاق بين الشكل المحلي والقانوني.

يفشل فورًا إذا: تغيّرت مجموعة الحقول القانونية المجمدة، أو هبط حقل محلي
خارج خريطة to_canonical الموثقة، أو اختلفت دلالات تحويل الوحدة (ms→ث).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ocr.canonical import CANONICAL_FIELDS, HAS_OCR_CORE, to_canonical
from ocr.contract import OCRResult, WordBox


def _sample() -> OCRResult:
    return OCRResult(
        text="نص المريض",
        words=[WordBox(text="نص", bbox=(0, 0, 10, 20), confidence=0.95)],
        confidence=0.95,
        engine="trocr",
        language="ar",
        duration_ms=1500.0,
        raw_text="نص المريض الخام",
        metadata={"page": 2, "warnings_local": "x"},
        warnings=["خط منخفض الثقة"],
        error=None,
    )


def test_canonical_field_set_is_frozen():
    assert CANONICAL_FIELDS == (
        "text", "engine", "confidence", "processing_time", "error", "pages", "meta",
    )


def test_every_amh_field_lands_somewhere():
    out = to_canonical(_sample())
    assert isinstance(out, dict) and set(out) == set(CANONICAL_FIELDS)
    assert out["text"] == "نص المريض"
    assert out["engine"] == "trocr"          # تمرير بلا إكراه
    assert out["confidence"] == 0.95
    assert out["processing_time"] == 1.5     # 1500ms → 1.5s (تحويل الوحدة موثق)
    assert out["error"] is None
    assert out["pages"] == 1                 # الافتراضي القانوني
    meta = out["meta"]
    assert meta["words"] and meta["words"][0].text == "نص"
    assert meta["language"] == "ar"
    assert meta["raw_text"] == "نص المريض الخام"
    assert meta["warnings"] == ["خط منخفض الثقة"]
    assert meta["created_at"]               # طابع إنشاء محفوظ
    assert meta["page"] == 2                 # metadata المحلي مدمج
    assert meta["warnings_local"] == "x"


def test_engine_default_unknown_passes_through():
    res = _sample()
    res.engine = "unknown"
    out = to_canonical(res)
    assert out["engine"] == "unknown"


def test_canonical_object_when_ocr_core_installed():
    if not HAS_OCR_CORE:
        import pytest
        pytest.skip("ocr-core غير مثبت في هذه البيئة — مسار dict يغطيه اختبار أعلاه")
    out = to_canonical(_sample())
    assert type(out).__name__ == "OCRResult"
    assert out.processing_time == 1.5
    assert out.meta["language"] == "ar"
