#!/usr/bin/env python3
"""
sync_shared.py — Propaga archivos canónicos de `shared/lgrw_common/` a cada caso.

Single source of truth para auth.py y settings.py (idénticos en los 25 casos).

Uso:
  python scripts/sync_shared.py            # copia shared → cada caso
  python scripts/sync_shared.py --check    # CI mode: exit 1 si hay drift

Diseño: extracción ligera v4.15.0. Cambiar el contenido en `shared/` y correr
este script. CI ejecuta `--check` para impedir merges con copias desincronizadas.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED = REPO_ROOT / "shared" / "lgrw_common"
CASES_DIR = REPO_ROOT / "cases"

# (source_in_shared, dest_relative_to_case_backend_src)
FILE_MAP = [
    ("auth.py", "auth.py"),
    ("settings.py", "settings.py"),
]


def iter_case_backends():
    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        backend_src = case_dir / "backend" / "src"
        if backend_src.is_dir():
            yield case_dir.name, backend_src


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="Modo verificación: exit 1 si alguna copia difiere de shared/")
    args = parser.parse_args()

    drift = []
    synced = []

    for case_name, backend_src in iter_case_backends():
        for src_name, dest_name in FILE_MAP:
            source = SHARED / src_name
            target = backend_src / dest_name
            if not source.is_file():
                print(f"ERROR: fuente canónica no encontrada: {source}")
                return 2
            if not target.exists():
                if args.check:
                    drift.append(f"{case_name}/{dest_name}: NO EXISTE")
                else:
                    target.write_bytes(source.read_bytes())
                    synced.append(f"{case_name}/{dest_name}: creado")
                continue
            if source.read_bytes() != target.read_bytes():
                if args.check:
                    drift.append(f"{case_name}/{dest_name}: difiere de shared/")
                else:
                    target.write_bytes(source.read_bytes())
                    synced.append(f"{case_name}/{dest_name}: actualizado")

    if args.check:
        if drift:
            print("DRIFT DETECTADO — corre `python scripts/sync_shared.py` para alinear:")
            for d in drift:
                print(f"  - {d}")
            return 1
        print(f"OK — todos los casos están sincronizados con shared/ ({sum(1 for _ in iter_case_backends())} casos × {len(FILE_MAP)} archivos).")
        return 0

    if synced:
        print(f"Sincronizados {len(synced)} archivos:")
        for s in synced:
            print(f"  + {s}")
    else:
        print("No había drift — nada que sincronizar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
