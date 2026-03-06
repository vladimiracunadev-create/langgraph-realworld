import os
import glob

replacements = {
    "| **💻 Desarrollador / DevOps** | [**Casos 09 y 10 (Reference Cases)**](cases/09-rrhh-screening-agenda/README.md) | Explorar código real: FastAPI, streaming, Pydantic y grafos. |": "| **💻 Desarrollador / DevOps (Caso 09)** | [**RRHH Screening (Reference)**](cases/09-rrhh-screening-agenda/README.md) | Explorar código real: FastAPI, streaming, Pydantic y grafos. |\\n| **💻 Desarrollador / DevOps (Caso 10)** | [**Onboarding (Reference)**](cases/10-onboarding-empleados/README.md) | Explorar integraciones reales: Multi-Node streaming, APIs externas y RBAC. |"
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
