import sys
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[2]
if str(CASE_ROOT) not in sys.path:
    sys.path.insert(0, str(CASE_ROOT))
