"""اختبارات السقالة — تضمن أن الوحدات import-safe وتعمل بالحد الأدنى."""
def test_rtl_detect_direction():
    from ocr.rtl import detect_direction
    assert detect_direction("السلام عليكم") == "rtl"
    assert detect_direction("hello world") == "ltr"
    assert detect_direction("hello السلام") == "mixed"


def test_rtl_reshape_safe_without_deps():
    from ocr.rtl import reshape_arabic
    # بلا arabic_reshaper → تراجع آمن (يعيد النص)
    assert isinstance(reshape_arabic("نص"), str)


def test_normalize_for_search():
    from ocr.normalize import normalize_for_search
    assert normalize_for_search("أَحْمَد") == "احمد"
    assert normalize_for_search("  مستشفى   الجامعة ") == "مستشفي الجامعه"


def test_config_defaults():
    from ocr.config import EngineConfig, DEFAULT
    c = EngineConfig()
    assert "tesseract" in c.engines
    assert c.confidence_floor == 0.6
    assert DEFAULT.language == "ar"


def test_engine_available_and_import_safe():
    from ocr.engine import HandwritingEngine
    e = HandwritingEngine()
    avail = e.available()          # لا يرفع حتى بلا محركات
    assert isinstance(avail, list)


def test_fields_extract_doses():
    from extract.fields import extract_doses
    d = extract_doses("جرعة 500 mg مرتين و 10 ml")
    vals = {(x["value"], x["unit"].lower()) for x in d}
    assert ("500", "mg") in vals
    assert ("10", "ml") in vals


def test_correction_delegates_safely():
    from extract.correction import correct_arabic
    txt, n = correct_arabic("نص تجريبي")
    assert isinstance(txt, str) and isinstance(n, int)


def test_export_card_and_count(tmp_path):
    from export.hf_dataset import build_dataset_card, export_snippets
    assert "arabic-medical-handwriting" in build_dataset_card()
    r = export_snippets(str(tmp_path), str(tmp_path / "out"))
    assert r["count"] == 0 and r["pushed"] is False
