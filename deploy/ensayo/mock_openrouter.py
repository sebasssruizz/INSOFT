"""Mock HTTPS de OpenRouter para el ensayo local. NO es el servicio real.

Responde a POST /api/v1/chat/completions con el formato de OpenRouter
({"choices":[{"message":{"content":...}}]}). Clasifica por el prompt de sistema:
  - generación de preguntas (prompt con "JSON")  -> 2 preguntas válidas, 4 opciones
  - normalización (prompt "reformula")           -> devuelve la pregunta
  - respuesta del asistente                      -> texto de prueba
Si el mensaje del usuario contiene "FALLAR" responde 503 (simula proveedor caído).
Cada llamada se registra en stdout para poder contarla.
"""
import json
import ssl
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CERT = "/run/tls/openrouter.crt"
KEY = "/run/tls/openrouter.key"


def _log(kind):
    print(json.dumps({"ev": "llm_call", "kind": kind}), flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "mock-openrouter/1"

    def log_message(self, fmt, *args):  # silencio: solo registramos llamadas
        pass

    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"ok": True})

    def do_POST(self):
        if self.path != "/api/v1/chat/completions":
            self._send(404, {"error": "ruta no soportada por el mock"})
            return
        largo = int(self.headers.get("Content-Length", "0"))
        try:
            data = json.loads(self.rfile.read(largo) or b"{}")
        except ValueError:
            self._send(400, {"error": "json inválido"})
            return
        mensajes = data.get("messages", [])
        sistema = mensajes[0].get("content", "") if mensajes else ""
        usuario = mensajes[-1].get("content", "") if mensajes else ""

        if "FALLAR" in usuario:
            _log("fallo")
            self._send(503, {"error": {"message": "proveedor simulado caído"}})
            return
        if "JSON" in sistema:
            _log("generar")
            preguntas = []
            for _ in range(2):
                preguntas.append({
                    "prompt": f"¿Pregunta de ensayo generada {uuid.uuid4().hex[:10]}?",
                    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                    "correct_index": 1,
                    "explanation": "Explicación de prueba del mock.",
                })
            texto = json.dumps({"questions": preguntas}, ensure_ascii=False)
        elif "reformula" in sistema:
            _log("normalizar")
            texto = usuario.strip()[:500]
        else:
            _log("responder")
            texto = "Respuesta de prueba del mock, basada en el contexto recibido."
        self._send(200, {"id": "mock", "choices": [{"message": {"role": "assistant", "content": texto}}]})


def main():
    httpd = ThreadingHTTPServer(("0.0.0.0", 443), Handler)
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto.load_cert_chain(CERT, KEY)
    httpd.socket = contexto.wrap_socket(httpd.socket, server_side=True)
    print(json.dumps({"ev": "mock_listo"}), flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
