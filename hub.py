import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

CASES_DIR = Path("cases")
SAFE_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
SAFE_HOST = re.compile(r"^[A-Za-z0-9._:-]+$")
SAFE_MODULE_TARGET = re.compile(r"^[A-Za-z0-9_.:]+$")
SHELL_METACHARACTERS = ("|", ";", "&&", "||", "`", "$(", ">", "<")
ALLOWED_EXECUTABLES = {"docker", "python", "python3", "uvicorn"}


def get_case_path(case_id):
    for directory in CASES_DIR.iterdir():
        if directory.is_dir() and directory.name.startswith(case_id):
            return directory
    return None


def load_case_config(case_path):
    try:
        import yaml
    except ImportError:
        return None

    config_file = case_path / "case.yml"
    if not config_file.exists():
        return None
    with open(config_file, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _ensure_path_within(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ValueError(f"Unsafe path outside case root: {resolved_candidate}")
    return resolved_candidate


def _resolve_working_dir(case_path: Path, working_dir: str | None) -> Path:
    if not working_dir:
        return case_path
    candidate = Path(working_dir)
    if candidate.is_absolute():
        raise ValueError("case.yml working_dir must be relative to the case root.")
    return _ensure_path_within(case_path, case_path / candidate)


def _validate_python_command(argv: list[str], case_path: Path, working_dir: Path) -> None:
    if len(argv) < 2:
        raise ValueError("Python commands in case.yml require a script or module.")

    if argv[1] == "-m":
        if len(argv) < 4 or argv[2] != "uvicorn":
            raise ValueError("Only 'python -m uvicorn ...' is allowed in case.yml.")
        _validate_uvicorn_command(["uvicorn", *argv[3:]])
        return

    if argv[1].startswith("-"):
        raise ValueError("Inline Python flags are not allowed in case.yml.")

    script_path = _ensure_path_within(case_path, working_dir / argv[1])
    if script_path.suffix != ".py":
        raise ValueError("Only Python scripts are allowed in case.yml commands.")


def _validate_uvicorn_command(argv: list[str]) -> None:
    if len(argv) < 2 or not SAFE_MODULE_TARGET.fullmatch(argv[1]):
        raise ValueError("Uvicorn commands must point to a safe module target.")

    index = 2
    while index < len(argv):
        token = argv[index]
        if token == "--reload":
            index += 1
            continue
        if token in {"--host", "--port"}:
            if index + 1 >= len(argv):
                raise ValueError(f"Missing value for uvicorn flag {token}.")
            value = argv[index + 1]
            if token == "--host" and not SAFE_HOST.fullmatch(value):
                raise ValueError("Invalid host value in uvicorn command.")
            if token == "--port" and (not value.isdigit() or not 0 < int(value) < 65536):
                raise ValueError("Invalid port value in uvicorn command.")
            index += 2
            continue
        raise ValueError(f"Unsupported uvicorn flag in case.yml: {token}")


def _validate_docker_command(argv: list[str], case_path: Path, working_dir: Path) -> None:
    if len(argv) < 3 or argv[1] != "compose":
        raise ValueError("Only 'docker compose ...' commands are allowed in case.yml.")

    index = 2
    while index < len(argv):
        token = argv[index]
        if token == "-f":
            if index + 1 >= len(argv):
                raise ValueError("docker compose requires a file after -f.")
            _ensure_path_within(case_path, working_dir / argv[index + 1])
            index += 2
            continue
        if token in {"up", "down", "--build", "--remove-orphans"}:
            index += 1
            continue
        raise ValueError(f"Unsupported docker compose token in case.yml: {token}")


def _validate_case_command(argv: list[str], case_path: Path, working_dir: Path) -> None:
    executable = Path(argv[0]).name.lower()
    if executable not in ALLOWED_EXECUTABLES:
        raise ValueError(f"Executable '{argv[0]}' is not allowed in case.yml.")

    if executable in {"python", "python3"}:
        _validate_python_command(argv, case_path, working_dir)
        return
    if executable == "uvicorn":
        _validate_uvicorn_command(argv)
        return
    _validate_docker_command(argv, case_path, working_dir)


def resolve_case_command(command: str, case_path: Path, working_dir: str | None = None) -> tuple[list[str], Path]:
    raw_command = (command or "").strip()
    if not raw_command:
        raise ValueError("Empty command in case.yml.")

    for token in SHELL_METACHARACTERS:
        if token in raw_command:
            raise ValueError("Shell metacharacters are not allowed in case.yml commands.")

    resolved_cwd = _resolve_working_dir(case_path, working_dir)
    argv = shlex.split(raw_command, posix=True)
    if not argv:
        raise ValueError("Empty command in case.yml.")

    _validate_case_command(argv, case_path, resolved_cwd)
    return argv, resolved_cwd


def _validated_env(case_env: dict | None) -> dict[str, str]:
    if not case_env:
        return {}

    safe_env: dict[str, str] = {}
    for name, value in case_env.items():
        if not SAFE_ENV_NAME.fullmatch(str(name)):
            raise ValueError(f"Unsafe environment variable declared in case.yml: {name}")
        safe_env[str(name)] = str(value)
    return safe_env


def _run_case_command(
    command: str,
    case_path: Path,
    *,
    working_dir: str | None = None,
    env: dict | None = None,
) -> None:
    argv, cwd = resolve_case_command(command, case_path, working_dir)
    subprocess.run(argv, check=True, cwd=cwd, env=env)


def cmd_list(args):
    print(f"{'ID':<5} | {'Name':<30} | {'Status'}")
    print("-" * 50)
    for directory in sorted(CASES_DIR.iterdir()):
        if directory.is_dir():
            case_id = directory.name.split("-")[0]
            name = "-".join(directory.name.split("-")[1:])
            has_config = (directory / "case.yml").exists()
            if case_id in ["09", "10", "13"]:
                status = "Industrial (v3.8.0)"
            elif case_id in ["01", "02"]:
                status = "Operational (v3.8.0)"
            elif has_config:
                status = "Scaffold (v1.0)"
            else:
                status = "Legacy"

            print(f"{case_id:<5} | {name[:30]:<30} | {status}")


def cmd_run(args):
    case_path = get_case_path(args.case)
    if not case_path:
        print(f"Error: Case {args.case} not found.")
        sys.exit(1)

    config = load_case_config(case_path)
    if not config:
        print(
            f"Error: Case {args.case} is not standardized or PyYAML is missing (case.yml unavailable)."
        )
        sys.exit(1)

    entrypoint = config.get("entrypoint")
    if not entrypoint:
        print(f"Error: No entrypoint defined for Case {args.case}")
        sys.exit(1)

    env = os.environ.copy()
    try:
        env.update(_validated_env(config.get("env")))
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    if args.input:
        env["INPUT"] = args.input

    print(f"Running Case {args.case}...")
    try:
        _run_case_command(
            entrypoint,
            case_path,
            working_dir=config.get("working_dir"),
            env=env,
        )
    except (subprocess.CalledProcessError, ValueError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            print(f"Error: Case execution failed with exit code {exc.returncode}")
            sys.exit(exc.returncode)
        print(f"Error: {exc}")
        sys.exit(1)


def cmd_serve(args):
    case_path = get_case_path(args.case)
    if not case_path:
        print(f"Error: Case {args.case} not found.")
        sys.exit(1)

    config = load_case_config(case_path)
    if not config or "serve" not in config:
        print(f"Error: Case {args.case} does not support 'serve' or requires PyYAML.")
        sys.exit(1)

    print(f"Serving Case {args.case}...")
    try:
        _run_case_command(
            config["serve"],
            case_path,
            working_dir=config.get("working_dir"),
            env=os.environ.copy(),
        )
    except (subprocess.CalledProcessError, ValueError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            print(f"Error: Serve failed with exit code {exc.returncode}")
            sys.exit(exc.returncode)
        print(f"Error: {exc}")
        sys.exit(1)


def cmd_doctor(args):
    print("Checking Hub environment...")
    try:
        import yaml  # noqa: F401

        print("[OK] PyYAML is installed.")
    except ImportError:
        print("[FAIL] PyYAML is missing. Run 'pip install -r requirements.txt'.")

    docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True)
    if docker_check.returncode == 0:
        print(f"[OK] {docker_check.stdout.strip()}")
    else:
        print("[FAIL] Docker is not installed or not in PATH.")

    if CASES_DIR.exists():
        print(f"[OK] Cases directory found: {CASES_DIR.absolute()}")
    else:
        print("[FAIL] Cases directory not found.")


def main():
    parser = argparse.ArgumentParser(description="Hub CLI for LangGraph Real-World Cases")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all cases")

    run_parser = subparsers.add_parser("run", help="Run a specific case")
    run_parser.add_argument("case", help="Case ID (e.g. '09')")
    run_parser.add_argument("--input", help="Input parameters")

    serve_parser = subparsers.add_parser("serve", help="Serve a case (web/cli)")
    serve_parser.add_argument("case", help="Case ID")

    subparsers.add_parser("doctor", help="Check environment health")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "doctor":
        cmd_doctor(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

