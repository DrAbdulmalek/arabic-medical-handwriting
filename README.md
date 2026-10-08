# arabic-medical-handwriting

مشروع **OCR للخط اليدوي الطبي العربي** — نظيف (clean-room)، يُبنى حول
5 ملفات منتقاة من `omni-medical-suite` بدل تدقيق الـmonorepo كله (3,832 ملفًا).

> **الحالة: سقالة + عقد منفَّذ.** `ocr/contract.py` (عقد `OCRResult`/`WordBox`)
> منفَّذ ومُختبَر (5 اختبارات). المحركات والمعالجة (rtl/normalize/engine/
> extract/export) **سقالة import-safe** — الخطة نقلها من omni أو تفويضها
> إلى `ocr-core` المركزي.
>
> المصدر: محادثة DeepSeek `1m3ih8eveq98lv7aqc` (رسائل 250-259).

## القرار المعماري (من المحادثة)

بدل تدقيق `omni-medical-suite` بالكامل — نأخذ منه **5 ملفات فقط** ونبني
مشروعًا نظيفًا حولها:

| من omni | إلى هنا | لماذا |
|---|---|---|
| `src/ocr/rtl_utils.py` | `ocr/rtl.py` | معالجة RTL — نادرة، لا تُكتب من الصفر |
| `src/ocr/normalization.py` | `ocr/normalize.py` | التطبيع العربي |
| `src/ocr/field_extractor.py` | `extract/fields.py` | استخراج حقول طبية |
| نمط `packages/omni_ocr/adapter.py` (OCRResult) | `ocr/contract.py` ✅ **منفَّذ** | عقد موحّد |
| نمط `handwriting/.../ocr_engine.py` | `ocr/engine.py` | محرك متعدد — مع **إصلاح Mistral** (لا ثقة مخترعة) |

**لا monorepo، لا `packages/*`، لا 3,832 ملفًا.**

## البنية

```
ocr/
├── contract.py     ✅ OCRResult + WordBox (منفَّذ + مُختبَر)
├── engine.py       🔧 HandwritingEngine — multi-engine سقالة (tesseract احتياطي)
├── rtl.py          🔧 reshape/detect_direction (نقل من omni)
├── normalize.py    🔧 normalize_for_search (non-destructive)
└── config.py       🔧 EngineConfig (قائمة محركات + حد ثقة)
extract/
├── fields.py       🔧 extract_doses (حارس أرقام)
└── correction.py   🔧 يفوّض إلى ocr-core corrections_ar
export/
└── hf_dataset.py   🔧 dataset card + export_snippets (سقالة)
unsloth_finetune.py 🔧 تدريب على Colab (Unsloth) — 12 خلية مُجمّعة
tests/              ✅ test_contract.py (5) + test_stubs.py
```
✅ منفَّذ · 🔧 سقالة import-safe

## سياسة الثقة (محفوظة من ocr-core)

`confidence == 0.0` = **غير معروفة** — لا تُختلق درجة أبدًا. المحركات تبلّغ
الأخطاء عبر `OCRResult.error` ولا ترفع استثناءات. هذا هو "إصلاح Mistral"
المشار إليه في الخطة.

## التثبيت والتشغيل

```bash
pip install -e ".[dev]"          # سقالة + اختبارات (خفيف، بلا GPU)
pytest -q                        # 5+ اختبارات

pip install -e ".[ocr,arabic]"   # لمحرك tesseract + reshaping فعلي
pip install -e ".[trocr]"        # لـ TrOCR (يحتاج torch)

# التدريب على Colab (GPU):
#   افتح Colab → T4 GPU → الصق خلايا unsloth_finetune.py
```

## التدريب (unsloth_finetune.py)

سكربت Colab كامل (12 خلية) لضبط نموذج عربي (Qwen2.5/TrOCR) عبر Unsloth على
T4 GPU مجاني. خلايا: تثبيت Unsloth ← تحميل بيانات ← LoRA ← تدريب ← حفظ ← رفع HF.

## العلاقة بالمستودعات الأخرى

- **ocr-core**: المحرك المركزي — `extract/correction.py` يفوّض إليه، ويمكن
  استخدام `ocr_core.engines` مباشرة بدل `ocr/engine.py`.
- **omni-handwriting-samples-private**: مصدر عينات الخط اليدوي (S-series).
- **omni-medical-suite**: مصدر الـ5 ملفات (rtl/normalize/field_extractor).

## الترخيص

MIT (الكود). النماذج: TrOCR (MIT)، AraBERT (Apache-2.0)، Qwen (Apache-2.0).
بيانات التدريب (إن أُخذت من omni-handwriting-samples-private) خاصة.
