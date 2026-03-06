import subprocess
import time
import sys
import os

def launch():
    root = os.path.dirname(os.path.abspath(__file__))
    
    # Configuración de comandos (usando los venv de cada caso)
    py09 = os.path.join(root, "cases", "09-rrhh-screening-agenda", "backend", ".venv", "Scripts", "python.exe")
    py10 = os.path.join(root, "cases", "10-onboarding-empleados", "backend", ".venv", "Scripts", "python.exe")
    py_portal = sys.executable

    print("🚀 Lanzando ecosistema LangGraph Realworld...")

    # 1. Caso 09 (Puerto 8009)
    print("📦 Iniciando Caso 09 (RR.HH. Screening) en puerto 8009...")
    p09 = subprocess.Popen(
        [py09, "-m", "uvicorn", "src.api:app", "--port", "8009"],
        cwd=os.path.join(root, "cases", "09-rrhh-screening-agenda", "backend"),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # 2. Caso 10 (Puerto 8010)
    print("📦 Iniciando Caso 10 (Onboarding) en puerto 8010...")
    p10 = subprocess.Popen(
        [py10, "-m", "uvicorn", "src.api:app", "--port", "8010"],
        cwd=os.path.join(root, "cases", "10-onboarding-empleados", "backend"),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # 3. Portal (Puerto 8080)
    print("🌐 Iniciando Portal Principal en puerto 8080...")
    p_portal = subprocess.Popen(
        [py_portal, "serve_site.py"],
        cwd=root
    )

    print("\n✅ Todo listo! Accede a:")
    print("👉 Portal: http://localhost:8080")
    print("👉 Caso 09: http://localhost:8009")
    print("👉 Caso 10: http://localhost:8010")
    print("\nPresiona Ctrl+C para detener todos los servicios.")

    try:
        while True:
            time.sleep(1)
            if p_portal.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
    finally:
        p09.terminate()
        p10.terminate()
        p_portal.terminate()

if __name__ == "__main__":
    launch()
