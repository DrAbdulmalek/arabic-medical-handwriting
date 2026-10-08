"""اختبارات OCRResult."""
from ocr.contract import OCRResult, WordBox


def test_empty_result():
    r = OCRResult()
    assert r.is_empty is True
    assert r.word_count == 0


def test_result_with_text():
    r = OCRResult(text="مرحبا بالعالم", engine="tesseract")
    assert r.is_empty is False
    assert r.word_count == 2


def test_result_with_words():
    r = OCRResult(
        text="مرحبا",
        words=[WordBox(text="مرحبا", bbox=(10, 20, 100, 60), confidence=0.95)],
    )
    assert len(r.words) == 1
    assert r.words[0].text == "مرحبا"
    assert r.words[0].bbox == (10, 20, 100, 60)


def test_summary():
    r = OCRResult(text="مرحبا بالعالم", engine="tesseract",
                   confidence=0.87, duration_ms=234.5)
    s = r.summary()
    assert "tesseract" in s
    assert "2 كلمة" in s
    assert "87%" in s


def test_to_dict():
    r = OCRResult(text="نص", engine="test")
    d = r.to_dict()
    assert d["text"] == "نص"
    assert d["engine"] == "test"
    assert "created_at" in d
