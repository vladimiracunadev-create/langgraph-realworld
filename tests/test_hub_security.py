import shutil
import tempfile
from pathlib import Path

import pytest

from hub import load_case_config, resolve_case_command


def make_case_path() -> Path:
    temp_root = Path('.pytest-tmp')
    temp_root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=temp_root))


def test_case01_entrypoint_resolves_inside_backend():
    case_path = Path('cases/01-soporte-cliente-omnicanal')
    config = load_case_config(case_path)

    argv, cwd = resolve_case_command(
        config['entrypoint'],
        case_path,
        config.get('working_dir'),
    )

    assert argv[:3] == ['python', '-m', 'uvicorn']
    assert cwd == (case_path / 'backend').resolve()


def test_rejects_python_inline_execution():
    case_path = make_case_path()
    try:
        with pytest.raises(ValueError, match='Inline Python flags are not allowed'):
            resolve_case_command('python -c "print(1)"', case_path)
    finally:
        shutil.rmtree(case_path, ignore_errors=True)


def test_rejects_shell_metacharacters():
    case_path = make_case_path()
    try:
        with pytest.raises(ValueError, match='Shell metacharacters'):
            resolve_case_command('docker compose -f compose.yml up --build; whoami', case_path)
    finally:
        shutil.rmtree(case_path, ignore_errors=True)
