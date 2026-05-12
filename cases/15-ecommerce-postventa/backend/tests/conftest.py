import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

CASE_DIR = BACKEND_DIR.parent
DATA_DIR = CASE_DIR / "data"

os.environ.setdefault("DATA_DIR", str(DATA_DIR))
# Fecha fija para tests deterministas (los pedidos están datados ~mayo 2026).
os.environ.setdefault("FECHA_HOY", "2026-05-11")
