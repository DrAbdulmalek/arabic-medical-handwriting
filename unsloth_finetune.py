#!/usr/bin/env python3
# unsloth_finetune.py — تدريب TrOCR/نموذج عربي على Colab (Unsloth)
# المصدر: محادثة DeepSeek 1m3ih8eveq98lv7aqc — رسالة 223 (14 خلية مُجمّعة)
# التشغيل: انسخ الخلايا إلى Colab (T4 GPU) أو شغله كسكربت محليًا.

# ═══════════════════════════════════════════════════════════
# الخلية 1: تثبيت Unsloth والتبعيات
# ═══════════════════════════════════════════════════════════

%%capture
import os
if "COLAB_" not in "".join(os.environ.keys()):
    # محليًا — تثبيت عادي
    !pip install unsloth
else:
    # على Colab — نسخة متوافقة مع CUDA
    import torch
    v = torch.__version__
    !pip install --no-deps bitsandbytes accelerate xformers==0.0.29.post3 peft trl triton cut_cross_entropy unsloth_zoo
    !pip install sentencepiece protobuf "datasets>=3.4.1" huggingface_hub hf_transfer
    !pip install --no-deps unsloth

# تحقق من GPU
!nvidia-smi

# ═══════════════════════════════════════════════════════════
# الخلية 2: تحميل النموذج بـ 4-bit QLoRA
# ═══════════════════════════════════════════════════════════

from unsloth import FastLanguageModel
import torch

# اختَر النموذج حسب الموارد:
# - T4 مجاني (15GB): Qwen2.5-3B أو Llama-3.2-3B
# - T4 + Pro: Qwen2.5-7B
# - A100: Qwen2.5-14B

MODEL_NAME = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"

MAX_SEQ_LENGTH = 2048      # كافٍ لمعظم الأزواج
DTYPE = None               # auto
LOAD_IN_4BIT = True        # توفير 70% من VRAM

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
)

print(f"✅ النموذج محمّل: {MODEL_NAME}")
print(f"   VRAM المستخدم: {torch.cuda.memory_allocated()/1e9:.2f} GB")

# ═══════════════════════════════════════════════════════════
# الخلية 3: إضافة محوّلات LoRA
# ═══════════════════════════════════════════════════════════

model = FastLanguageModel.get_peft_model(
    model,
    r=16,                    # LoRA rank — 16 كافٍ للطبي
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0,          # 0 محسّن في Unsloth
    bias="none",
    use_gradient_checkpointing="unsloth",  # يوفر 30% ذاكرة
    random_state=42,
    use_rslora=False,
    loftq_config=None,
)

# احسب معاملات LoRA
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"✅ LoRA مُضاف")
print(f"   معاملات قابلة للتدريب: {trainable:,}")
print(f"   إجمالي: {total:,}")
print(f"   النسبة: {100 * trainable / total:.2f}%")

# ═══════════════════════════════════════════════════════════
# الخلية 4: تحميل PEACH Corpus + تنسيق Dataset
# ═══════════════════════════════════════════════════════════

import json
from datasets import Dataset
from tqdm import tqdm

# حمّل PEACH إن لم يكن موجودًا
import os
if not os.path.exists("peach.jsonl"):
    print("→ تنزيل PEACH Corpus...")
    !wget -q -O peach.zip "https://data.mendeley.com/public-api/zip/5k6yrrhng7/download/3"
    !unzip -q peach.zip -d peach_raw
    !ls -la peach_raw/
    # ⚠️ عدّل هذا السطر حسب بنية الملفات الفعلية
    # عادةً يكون هناك CSV أو ملفان TXT
    # شغّل السكريبت: peach_to_jsonl.py
    print("⚠️ شغّل peach_to_jsonl.py أولًا")
else:
    print("✅ peach.jsonl موجود")

# حمّل الأزواج
with open("peach.jsonl", encoding="utf-8") as f:
    pairs = [json.loads(line) for line in f if line.strip()]

print(f"📊 عدد الأزواج: {len(pairs):,}")

# قسّم: 90% تدريب، 5% تحقق، 5% اختبار
import random
random.seed(42)
random.shuffle(pairs)

n = len(pairs)
train_end = int(n * 0.90)
val_end = int(n * 0.95)

train_pairs = pairs[:train_end]
val_pairs = pairs[train_end:val_end]
test_pairs = pairs[val_end:]

print(f"   تدريب: {len(train_pairs):,}")
print(f"   تحقق: {len(val_pairs):,}")
print(f"   اختبار: {len(test_pairs):,}")

# احفظ
for name, data in [("train", train_pairs), ("val", val_pairs), ("test", test_pairs)]:
    with open(f"{name}.jsonl", "w", encoding="utf-8") as f:
        for p in data:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

# ═══════════════════════════════════════════════════════════
# الخلية الخامسة: تنسيق Prompt للتدريب
# ═══════════════════════════════════════════════════════════

# قالب التدريب — Qwen2.5 chat format
PROMPT_TEMPLATE = """<|im_start|>system
أنت مترجم طبي متخصص من الإنجليزية إلى العربية. ترجم بدقة عالية مع الحفاظ على المصطلحات الطبية.
<|im_end|>
<|im_start|>user
ترجم النص الطبي التالي إلى العربية:

{source}
<|im_end|>
<|im_start|>assistant
{target}
<|im_end|>"""

EOS_TOKEN = tokenizer.eos_token


def format_prompts(examples):
    """يُنسّق الدفعة."""
    sources = examples["source_en"]
    targets = examples["target_ar"]

    texts = []
    for src, tgt in zip(sources, targets):
        text = PROMPT_TEMPLATE.format(
            source=src.strip(),
            target=tgt.strip(),
        ) + EOS_TOKEN
        texts.append(text)

    return {"text": texts}


# حمّل Dataset
from datasets import load_dataset

dataset = load_dataset(
    "json",
    data_files={
        "train": "train.jsonl",
        "validation": "val.jsonl",
        "test": "test.jsonl",
    },
)

# طبّق التنسيق
dataset = dataset.map(
    format_prompts,
    batched=True,
    remove_columns=dataset["train"].column_names,
)

print("✅ Dataset جاهز")
print(f"   عدد عينات التدريب: {len(dataset['train']):,}")
print(f"\n📝 مثال:")
print(dataset["train"][0]["text"][:400])

# ═══════════════════════════════════════════════════════════
# الخلية السادسة: SFTTrainer من TRL
# ═══════════════════════════════════════════════════════════

from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,           # مهم للترجمة — لا نُدمج العينات
    args=TrainingArguments(
        # Batch
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,   # فعال = 8
        per_device_eval_batch_size=2,

        # Epochs
        num_train_epochs=1,               # للبيانات الكبيرة
        # max_steps=60,                   # للتجربة السريعة

        # Learning rate
        warmup_steps=10,
        learning_rate=2e-4,
        lr_scheduler_type="linear",

        # Precision
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),

        # Logging
        logging_steps=10,
        logging_dir="logs",

        # Eval
        eval_strategy="steps",
        eval_steps=100,

        # Save
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,

        # Optimization
        optim="adamw_8bit",
        weight_decay=0.01,
        seed=42,

        # Output
        output_dir="outputs",
        report_to="none",       # لا wandb
    ),
)

print("✅ Trainer جاهز")

# ═══════════════════════════════════════════════════════════
# الخلية السابعة: بدء التدريب
# ═══════════════════════════════════════════════════════════

import time

print("🚀 بدء التدريب...")
print(f"   عدد خطوات التدريب: {len(dataset['train']) // 8}")

start = time.time()
stats = trainer.train()
elapsed = time.time() - start

print(f"\n✅ اكتمل التدريب")
print(f"   الزمن: {elapsed/60:.1f} دقيقة")
print(f"   Loss النهائي: {stats.training_loss:.4f}")
print(f"   VRAM الأقصى: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")

# ═══════════════════════════════════════════════════════════
# الخلية الثامنة: التقييم على مجموعة الاختبار
# ═══════════════════════════════════════════════════════════

FastLanguageModel.for_inference(model)

def translate(text: str, max_new_tokens: int = 256) -> str:
    """ترجمة نموذج واحد."""
    prompt = PROMPT_TEMPLATE.format(source=text, target="").rsplit(
        "<|im_start|>assistant", 1
    )[0] + "<|im_start|>assistant\n"

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=0.1,
        repetition_penalty=1.1,
    )
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # استخرج الترجمة فقط
    if "<|im_start|>assistant" in result:
        result = result.split("<|im_start|>assistant", 1)[1]
    return result.replace("<|im_end|>", "").strip()


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# اختبر على 100 عينة
N_EVAL = 100
results = []
print(f"🧪 التقييم على {N_EVAL} عينة...")

for i, sample in enumerate(tqdm(test_pairs[:N_EVAL])):
    pred = translate(sample["source_en"])
    ref = sample["target_ar"]

    cer = levenshtein(pred, ref) / max(len(ref), 1)
    results.append({
        "source": sample["source_en"],
        "reference": ref,
        "prediction": pred,
        "cer": cer,
    })

    if i < 3:
        print(f"\n--- مثال {i+1} ---")
        print(f"EN: {sample['source_en'][:100]}")
        print(f"مرجع: {ref[:100]}")
        print(f"تنبؤ: {pred[:100]}")
        print(f"CER: {cer:.3f}")

# متوسط CER
avg_cer = sum(r["cer"] for r in results) / len(results)
print(f"\n📊 CER المتوسط: {avg_cer:.4f}")
print(f"   ({avg_cer*100:.2f}%)")

# احفظ
with open("eval_results.jsonl", "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# ═══════════════════════════════════════════════════════════
# الخلية التاسعة: Baseline مقابل Fine-tuned
# ═══════════════════════════════════════════════════════════

# ⚠️ شغّل هذا قبل التدريب في نوت بوك منفصل، أو احفظ baseline مسبقًا
# هنا نفترض أن عندك baseline_cer مكتوب

BASELINE_CER = 0.35  # ضعه من نموذج بلا تدريب

print(f"📊 المقارنة:")
print(f"   Baseline CER:     {BASELINE_CER:.4f}")
print(f"   Fine-tuned CER:   {avg_cer:.4f}")

delta = BASELINE_CER - avg_cer
delta_pct = (delta / BASELINE_CER) * 100

print(f"\n   التحسّن: {delta:+.4f} ({delta_pct:+.1f}%)")

if delta > 0.05:
    print("   ✅ تحسّن ممتاز!")
elif delta > 0:
    print("   ⚠️ تحسّن طفيف — قد يحتاج مزيدًا من البيانات")
else:
    print("   ❌ لا تحسّن — راجع البيانات أو الإعدادات")

# ═══════════════════════════════════════════════════════════
# الخلية 10: التصدير بصيغ متعددة
# ═══════════════════════════════════════════════════════════

# 10.1 احفظ LoRA adapters (صغير ~50 MB)
model.save_pretrained("lora_adapters")
tokenizer.save_pretrained("lora_adapters")
print("✅ LoRA adapters: ./lora_adapters/ (~50 MB)")

# 10.2 احفظ بصيغة GGUF (للاستخدام المحلي مع Ollama/llama.cpp)
print("\n→ تحويل إلى GGUF...")
model.save_pretrained_gguf(
    "model_gguf",
    tokenizer,
    quantization_method="q4_k_m",     # توازن جيد
)
print("✅ GGUF: ./model_gguf/ (~2 GB)")

# 10.3 ارفع إلى HuggingFace (اختياري)
HF_TOKEN = ""  # املأ التوكن
HF_REPO = "DrAbdulmalek/medical-ar-qwen-3b"

if HF_TOKEN:
    model.push_to_hub_merged(
        HF_REPO,
        tokenizer,
        save_method="lora",
        token=HF_TOKEN,
    )
    print(f"✅ رُفع: https://huggingface.co/{HF_REPO}")
else:
    print("⚠️ لم يُرفع — املأ HF_TOKEN")

# 10.4 حمّل الملفات للجهاز
from google.colab import files
import shutil

shutil.make_archive("medical-ar-qwen-3b", "zip", ".", "model_gguf")
files.download("medical-ar-qwen-3b.zip")
print("✅ الملف جاهز للتنزيل")

# ═══════════════════════════════════════════════════════════
# الخلية 11: اختبار أمثلة طبية حقيقية
# ═══════════════════════════════════════════════════════════

test_sentences = [
    "The patient presents with acute appendicitis.",
    "Prescribe 500mg of amoxicillin three times daily.",
    "Blood pressure: 140/90 mmHg.",
    "MRI shows a herniated disc at L4-L5.",
    "Take the medication on an empty stomach.",
    "Follow up in two weeks for suture removal.",
]

print("=" * 70)
print("🧪 اختبار ترجمات طبية")
print("=" * 70)

for en in test_sentences:
    ar = translate(en)
    print(f"\n🇬🇧 {en}")
    print(f"🇸🇦 {ar}")

# ═══════════════════════════════════════════════════════════
# الخلية 12: دمج النموذج في مشروع ocr-core
# ═══════════════════════════════════════════════════════════

# بعد التنزيل محليًا:
"""
# في مشروع ocr-core، أنشئ:
# src/ocr_core/engines/translation_qwen.py

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class QwenMedicalTranslator:
    name = "qwen-medical-ar"
    
    def __init__(self, model_path: str = "model_gguf/"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.float16,
        )
    
    def translate(self, text: str) -> str:
        # نفس PROMPT_TEMPLATE
        ...
"""

print("✅ اكتمل! النموذج جاهز للدمج في ocr-core")
print("\n📋 الملفات المُنتَجة:")
print("   ./lora_adapters/           ← LoRA فقط (50 MB)")
print("   ./model_gguf/              ← نموذج GGUF كامل (~2 GB)")
print("   ./eval_results.jsonl       ← نتائج التقييم")
print("   ./medical-ar-qwen-3b.zip   ← للتنزيل")
