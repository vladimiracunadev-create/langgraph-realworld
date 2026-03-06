"""conftest.py – configura sys.path para que pytest encuentre 'src'."""
import sys
from pathlib import Path

# Agrega el directorio backend/ al path para que 'src' sea importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
