mkdir arabic-medical-handwriting && cd arabic-medical-handwriting
git init
mkdir -p ocr extract export tests/fixtures data/samples data/corrections

cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "arabic-medical-handwriting"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pillow>=10.0",
    "pytesseract>=0.3.10",
    "transformers>=4.40",
    "torch>=2.2",
    "sentencepiece>=0.2",
]

[project.optional-dependencies]
app = ["streamlit>=1.36"]
dev = ["pytest>=8.0", "ruff>=0.6"]

[project.scripts]
amh = "ocr.cli:main"
EOF

cat > README.md <<'EOF'
# Arabic Medical Handwriting OCR

OCR للكتب الطبية المكتوبة بخط يدوي — عربي.
EOF

cat > LICENSE <<'EOF'
MIT License
Copyright (c) 2026 DrAbdulmalek
EOF

cat > .gitignore <<'EOF'
__pycache__/
*.pyc
.venv/
data/samples/*
data/corrections/*
!data/samples/.gitkeep
!data/corrections/.gitkeep
EOF

touch data/samples/.gitkeep data/corrections/.gitkeep
touch ocr/__init__.py extract/__init__.py export/__init__.py tests/__init__.py

git add .
git commit -m "chore: initial structure"
