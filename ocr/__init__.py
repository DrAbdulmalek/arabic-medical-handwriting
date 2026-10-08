"""ocr — نواة OCR لمشروع arabic-medical-handwriting.

العقد (OCRResult/WordBox) منفذ في contract.py. المحركات والمعالجة
(rtl/normalize/engine) سقالة — تُنقل من omni-medical-suite وفق الخطة
(docs في README). كل الوحدات import-safe (لا تبعيات ثقيلة عند الاستيراد).
"""
from .contract import OCRResult, WordBox

__all__ = ["OCRResult", "WordBox"]
