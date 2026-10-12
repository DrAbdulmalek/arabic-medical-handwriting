# arabic-medical-handwriting

مشروع **OCR للخط اليدوي الطبي العربي** — عقد `OCRResult` موحّد، مع تفويض منطق OCR وRTL والتطبيع واستخراج الحقول إلى `ocr-core` المركزي.

> **الحالة:** تفويض كامل مطبّق على فرع التطوير. `ocr/contract.py` يبقى عقد الواجهة المحلية، بينما `engine/rtl/normalize/fields` واجهات رفيعة حول `ocr_core.*`. لا يُعد هذا المستند إثباتًا لنجاح الاختبارات؛ راجع حالة CI على طلب الدمج.

## لماذا التفويض؟

يمنع التفويض إنشاء نسخ متعددة من منطق OCR والتطبيع. يبقى في هذا المستودع العقد والسياسات الخاصة بالمستهلك فقط، بينما يبقى `ocr-core` مصدر الحقيقة لمحركات OCR وRTL والتطبيع واستخراج الحقول.

## البنية

```
ocr/
├── contract.py     عقد OCRResult + WordBox
├── engine.py       HandwritingEngine — بناء كسول وتكييف النتائج وEnsemble
├── rtl.py          fix_rtl عبر ArabicRTLFixer.fix_text + سياسة detect_direction المحلية
├── normalize.py    normalize_for_search عبر arabic_normalize
└── config.py       EngineConfig
extract/
├── fields.py       extract_fields عبر ArabicMedicalFieldExtractor + حارس الجرعات
└── correction.py   تفويض التصحيح العربي إلى ocr-core
export/
└── hf_dataset.py   سقالة بطاقة مجموعة البيانات وتصدير المقاطع
unsloth_finetune.py تدريب على Colab (Unsloth)
tests/              اختبارات العقد والتفويض والتوافق مع ocr-core
```

## سياسة الثقة

`confidence == 0.0` تعني أن الثقة **غير معروفة**؛ لا تُختلق درجة. تُعرض الأخطاء عبر `OCRResult.error` حيث يدعم المحرك ذلك.

## التثبيت والتشغيل

```bash
# تثبيت المشروع وتبعيات التطوير؛ يعتمد على ocr-core من الوسم v0.6.0
pip install -e ".[dev]"
pytest -q

# تثبيت ocr-core مع محرك اختياري من الوسم نفسه (الحزمة ليست معتمدة على PyPI)
pip install "marathon-ocr-core[tesseract] @ git+https://github.com/DrAbdulmalek/ocr-core.git@v0.6.0"
# البدائل المتاحة في ocr-core v0.6.0: [paddle] أو [easyocr] أو [surya]

# تبعيات تدريب TrOCR (قد تتطلب تنزيل نماذج وموارد كبيرة)
pip install -e ".[trocr]"

# التدريب على Colab (GPU): افتح Colab، اختر T4، ثم استخدم خلايا unsloth_finetune.py
```

إضافة `arabic` (arabic-reshaper/python-bidi) تبقى اختيارية لأدوات العرض أو الاختبارات الذهبية، وليست شرطًا لمسار RTL المفوّض إلى `ocr-core`.

## تنسيق الإصدارات

| المستهلك | إصدار `ocr-core` المثبّت |
|---|---|
| `arabic-medical-handwriting` | `v0.6.0` |
| `marathon-suite` | يجب أن يطابق `v0.6.0` حتى ترقية منسقة |

عند ترقية `ocr-core`، حدّث الـ pin في المستهلكين معًا، ثم شغّل `pytest -q` في `arabic-medical-handwriting` وبوابة التكامل في `marathon-suite`. لا ترقِّ أحدهما منفردًا.

## العلاقة بالمستودعات الأخرى

- `ocr-core` (`marathon-ocr-core`): المصدر المركزي لمنطق OCR وRTL والتطبيع واستخراج الحقول.
- `marathon-suite`: المنسّق؛ يجب أن يطابق pin الخاص به إصدار هذا المشروع.
- `omni-handwriting-samples-private`: مصدر عينات الخط اليدوي الخاصة.
- `omni-medical-suite`: المصدر التاريخي لبعض العقود.

## الترخيص

الكود: MIT. تحقّق من تراخيص كل نموذج وبيانات خارجية قبل إعادة توزيعها. بيانات التدريب المأخوذة من `omni-handwriting-samples-private` تبقى خاصة.