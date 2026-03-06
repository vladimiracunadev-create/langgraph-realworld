import os
import glob

replacements = {
    "| **💻 Desarrollador / DevOps** | [**Caso 09 (Reference Case - Industrial)**](cases/09-rrhh-screening-agenda/README.md)": "| **💻 Desarrollador / DevOps** | [**Casos 09 y 10 (Reference Cases)**](cases/09-rrhh-screening-agenda/README.md)",
    "make case-up CASE=09    # Lanzar Caso 09 (Usa Docker": "make case-up CASE=09    # Lanzar Caso 09 o 10 (Usa Docker",
    "Para habilitar el razonamiento avanzado en el Caso 09": "Para habilitar el razonamiento avanzado en los Casos 09 y 10",
    "El Caso 09 detecta automáticamente": "Tanto el Caso 09 como el 10 detectan automáticamente",
    "El **Caso 09** es el punto de referencia": "Los **Casos 09 y 10** son los puntos de referencia",
    "El Caso 09 (RR.HH. Screening) y el Caso 10 (Onboarding)": "Los Casos 09 y 10",
    "[**Caso 09 (Reference Case - Industrial)**](cases/09-rrhh-screening-agenda/README.md)": "[**Casos 09 y 10 (Reference Cases)**](cases/09-rrhh-screening-agenda/README.md)",
    "El **Caso 09** es el punto de referencia": "Los **Casos 09 y 10** son los puntos de referencia"
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
