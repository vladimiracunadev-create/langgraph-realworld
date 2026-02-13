import http.server
import socketserver
import os
import sys

PORT = 8080

def run_server():
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        Handler = http.server.SimpleHTTPRequestHandler
        # Permitir reutilizar el puerto inmediatamente después de cerrar
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Portal de LangGraph operativo en http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error al iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
