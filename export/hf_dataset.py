"""تصدير قصاصات الخط اليدوي إلى HuggingFace Dataset — سقالة.

الخطة (محادثة 1m3ih8eveq98lv7aqc — msg251): بنية
    arabic-medical-handwriting/  (dataset repo)
    ├── data/{train,test}/  قصاصات PNG + labels
    └── README.md (dataset card)

حتى التنفيذ، يمكن استخدام أدوات القائمة:
  - intelli-file-manager: HFExporter (JSONL + رفع صريح بتوكن)
  - ocr-core: export.hf_dataset command
هذه الوحدة import-safe.
"""
from __future__ import annotations
from pathlib import Path


def build_dataset_card(name: str = "arabic-medical-handwriting") -> str:
    """يولّد نص dataset card (Markdown)."""
    return (
        f"# {name}\n\n"
        "Arabic medical handwriting snippets for HTR training.\n\n"
        "## License\n\nCC BY-NC 4.0 (بيانات تدريبية — راجع المصدر).\n"
    )


def export_snippets(snippets_dir: str, out_dir: str) -> dict:
    """سقالة: يحصي القصاصات تحت snippets_dir (لا رفع تلقائيًا)."""
    src = Path(snippets_dir)
    pngs = list(src.rglob("*.png")) if src.exists() else []
    return {"count": len(pngs), "out_dir": out_dir, "pushed": False}
