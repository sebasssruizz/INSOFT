"""Sirve el build de producción del frontend como lo hace Vercel con vercel.json:

- los archivos estáticos tal cual;
- cualquier otra ruta de la SPA -> index.html (si no es un archivo real).

Esto es lo que necesita un servidor local para hacer recorridos con rutas
anidadas (/dashboard, /courses/...). Vercel ya lo hace por la reescritura de
vercel.json, y nginx lo hace con try_files, pero el http.server de Python no.

    python3 deploy/ensayo/servir_frontend.py frontend/dist 4173
"""
import http.server
import os
import sys


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        ruta = self.translate_path(self.path)
        if not os.path.exists(ruta):
            self.path = "/index.html"
        return super().send_head()

    def log_message(self, fmt, *args):  # sin ruido en la consola
        pass


if __name__ == "__main__":
    raiz, puerto = sys.argv[1], int(sys.argv[2])
    os.chdir(raiz)
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), SPAHandler)
    print(f"frontend en http://127.0.0.1:{puerto} (raíz {raiz}, rutas SPA -> index.html)")
    servidor.serve_forever()
