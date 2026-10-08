"""يجعل `import ocr/extract/export` يعمل من جذر المستودع في الاختبارات."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
