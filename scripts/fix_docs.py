import os
import glob

replacements = {
    "uvicorn cases.09-rrhh-screening-agenda.backend.src.api:app --port 8009": "cd cases/09-rrhh-screening-agenda/backend && uvicorn src.api:app --port 8009",
    "uvicorn cases.10-onboarding-empleados.backend.src.api:app --port 8010": "cd cases/10-onboarding-empleados/backend && uvicorn src.api:app --port 8010",
    "uvicorn src.api:app --reload --port 8009": "cd cases/09-rrhh-screening-agenda/backend && uvicorn src.api:app --reload --port 8009",
    "uvicorn src.api:app --port 8009": "cd cases/09-rrhh-screening-agenda/backend && uvicorn src.api:app --port 8009",
    "(Caso 09).": "(Casos 09 y 10).",
    "| **09** | [RRHH Screening Agenda](cases/09-rrhh-screening-agenda/README.md) | `COMPLETADO` | FastAPI + Sqlite + Pydantic + Resilience |\\n\\n": "| **09** | [RRHH Screening Agenda](cases/09-rrhh-screening-agenda/README.md) | `COMPLETADO` | FastAPI + Sqlite + Pydantic + Resilience |\\n| **10** | [Onboarding Empleados](cases/10-onboarding-empleados/README.md) | `COMPLETADO` | FastAPI + Streaming NDJSON |\\n\\n"
}

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        orig_content = content
        for old_str, new_str in replacements.items():
            content = content.replace(old_str, new_str)
            
        if content != orig_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

paths_to_check = [
    "*.md",
    "docs/*.md",
    "docs/wiki/*.md"
]

for pat in paths_to_check:
    for f in glob.glob(pat):
        process_file(f)
