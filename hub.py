import os
import sys
import yaml
import subprocess
import argparse
from pathlib import Path

CASES_DIR = Path("cases")

def get_case_path(case_id):
    # Support both "09" and "09-rrhh-screening-agenda"
    for d in CASES_DIR.iterdir():
        if d.is_dir() and d.name.startswith(case_id):
            return d
    return None

def load_case_config(case_path):
    config_file = case_path / "case.yml"
    if not config_file.exists():
        return None
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def cmd_list(args):
    print(f"{'ID':<5} | {'Name':<30} | {'Status'}")
    print("-" * 50)
    for d in sorted(CASES_DIR.iterdir()):
        if d.is_dir():
            case_id = d.name.split("-")[0]
            name = "-".join(d.name.split("-")[1:])
            has_config = (d / "case.yml").exists()
            status = "Standardized" if has_config else "Legacy"
            print(f"{case_id:<5} | {name[:30]:<30} | {status}")

def cmd_run(args):
    case_path = get_case_path(args.case)
    if not case_path:
        print(f"Error: Case {args.case} not found.")
        sys.exit(1)
    
    config = load_case_config(case_path)
    if not config:
        print(f"Error: Case {args.case} is not standardized (missing case.yml).")
        sys.exit(1)
    
    entrypoint = config.get("entrypoint")
    if not entrypoint:
        print(f"Error: No entrypoint defined for Case {args.case}")
        sys.exit(1)
    
    env = os.environ.copy()
    case_env = config.get("env", {})
    if case_env:
        env.update(case_env)
    
    if args.input:
        env["INPUT"] = args.input

    print(f"Running Case {args.case}...")
    try:
        subprocess.run(entrypoint, shell=True, check=True, cwd=case_path, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error: Case execution failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def cmd_serve(args):
    case_path = get_case_path(args.case)
    if not case_path:
        print(f"Error: Case {args.case} not found.")
        sys.exit(1)
    
    config = load_case_config(case_path)
    if not config or "serve" not in config:
        print(f"Error: Case {args.case} does not support 'serve'.")
        sys.exit(1)
    
    serve_cmd = config["serve"]
    print(f"Serving Case {args.case}...")
    try:
        subprocess.run(serve_cmd, shell=True, check=True, cwd=case_path)
    except subprocess.CalledProcessError as e:
        print(f"Error: Serve failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def cmd_doctor(args):
    print("Checking Hub environment...")
    # Check dependencies
    try:
        import yaml
        print("[OK] PyYAML is installed.")
    except ImportError:
        print("[FAIL] PyYAML is missing. Run 'pip install pyyaml'.")
    
    # Check Docker
    docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True)
    if docker_check.returncode == 0:
        print(f"[OK] {docker_check.stdout.strip()}")
    else:
        print("[FAIL] Docker is not installed or not in PATH.")

    # Check cases directory
    if CASES_DIR.exists():
        print(f"[OK] Cases directory found: {CASES_DIR.absolute()}")
    else:
        print("[FAIL] Cases directory not found.")

def main():
    parser = argparse.ArgumentParser(description="Hub CLI for LangGraph Real-World Cases")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all cases")
    
    run_parser = subparsers.add_parser("run", help="Run a specific case")
    run_parser.add_argument("case", help="Case ID (e.0. '09')")
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
