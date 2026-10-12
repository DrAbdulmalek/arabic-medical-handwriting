"""اختبارات السقالة — العقد الجديد (P0-4): تفويض كامل إلى ocr-core.

القديم كان يختبر سقالة محلية (reshape/normalize/config/available) —
هذه حُذفت عمداً لصالح التفويض. الاختبارات هنا تتحقق من:
  1. import-safe بلا محركات ثقيلة (paddle/easyocr غير مثبتة).
  2. سياسة الثقة (لا اختلاق ثقة، أخطاء عبر OCRResult.error).
  3. التوافق السطحي مع ocr-core الحقيقي المثبت (mandatory dep).
"""
from __future__ import annotations


def test_rtl_detect_direction_policy():
    # سياسة الاتجاه — نقية على حافة المشروع (ocr-core لا يوفرها)
    from ocr.rtl import detect_direction

    assert detect_direction("السلام عليكم") == "rtl"
    assert detect_direction("hello world") == "ltr"
    assert detect_direction("hello السلام") == "mixed"


def test_rtl_fix_rtl_delegates_and_returns_str():
    # الإصلاح نفسه مفوَّض إلى ocr_core.rtl_utils.ArabicRTLFixer.fix_text
    from ocr.rtl import fix_rtl

    assert isinstance(fix_rtl("نص تجريبي"), str)


def test_normalize_for_search_matches_ocr_core_semantics():
    # الدلالة الحقيقية من ocr_core.postprocess.normalization.arabic_normalize
    from ocr.normalize import normalize_for_search

    assert normalize_for_search("أَحْمَد") == "احمد"
    assert normalize_for_search("  مستشفى   الجامعة ") == "مستشفي الجامعه"


def test_config_defaults_no_confidence_fabrication():
    from ocr.config import EngineConfig

    c = EngineConfig()
    assert "tesseract" in c.engines
    # سياسة الثقة: 0.0 = مجهولة — لا حدّ افتراضي يختلق ثقة
    assert c.confidence_threshold == 0.0


def test_engine_import_safe_without_heavy_extras():
    # بلا paddle/easyocr extras → لا استثناء، بل error موصوف في OCRResult
    from ocr.config import EngineConfig
    from ocr.engine import HandwritingEngine

    e = HandwritingEngine(EngineConfig(engines=["paddle"]))
    # real ocr-core: engines construct lazily; failures surface per-call
    result = e.process_image("whatever.png")
    assert result.error is not None  # خطأ موصوف — لا استثناء
    assert result.confidence == 0.0 and result.text == ""


def test_fields_extract_doses_returns_dict_guard():
    # عقد الجرعات: dict مفصول بحقل جرعة فقط — بلا حقول → {} وليس اختلاقاً
    from extract.fields import extract_doses

    d = extract_doses("نص غير طبي بلا أي حقول")
    assert isinstance(d, dict) and d == {}


def test_fields_extract_doses_filters_empty_values(monkeypatch):
    import extract.fields as fields

    monkeypatch.setattr(
        fields,
        "extract_fields",
        lambda _text: {
            "dose": None,
            "dosage": "",
            "dose_units": [],
            "dose_amount": "500",
            "patient_name": "مريض",
        },
    )

    assert fields.extract_doses("أي نص") == {"dose_amount": "500"}


def test_correction_delegates_safely():
    from extract.correction import correct_arabic

    txt, n = correct_arabic("نص تجريبي")
    assert isinstance(txt, str) and isinstance(n, int)


def test_export_card_and_count(tmp_path):
    from export.hf_dataset import build_dataset_card, export_snippets

    assert "arabic-medical-handwriting" in build_dataset_card()
    r = export_snippets(str(tmp_path), str(tmp_path / "out"))
    assert r["count"] == 0 and r["pushed"] is False
