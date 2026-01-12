import os
import sys
from pathlib import Path

# Asegura que `import src...` funcione cuando pytest corre desde la raíz del repo.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

CASE_DIR = BACKEND_DIR.parent  # cases/09-rrhh-screening-agenda
DATA_DIR = CASE_DIR / "data"

# Forzamos rutas robustas en CI/pytest
os.environ.setdefault("DATA_DIR", str(DATA_DIR))
os.environ.setdefault("CHECKPOINT_DB", ":memory:")
