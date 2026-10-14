"""
api/index.py - Vercel Serverless Function Entrypoint para ECONODE Studio
Permite el despliegue serverless de alta velocidad en Vercel conectado a Supabase PostgreSQL.
Resuelve de forma transparente las rutas reescritas por Vercel para mantener compatibilidad 100% con REST API.
"""

import sys
import os
import urllib.parse

# Configurar rutas para importar módulos del proyecto en el runtime de Vercel
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
STUDIO_DIR = os.path.join(ROOT_DIR, "econode_studio")

for p in (ROOT_DIR, STUDIO_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import json
import traceback

from econode_studio.server import EconodeRequestHandler

# Clase 'handler' esperada nativamente por el runtime de Python en Vercel
class handler(EconodeRequestHandler):
    """Manejador Serverless de Vercel para ECONODE Studio API."""

    def _resolve_real_path(self):
        """
        Restaura la ruta original solicitada por el cliente.
        En Vercel Serverless, los rewrites pueden entregar '/api/index.py' en self.path,
        pero la ruta real viene en cabeceras o en el parámetro '__slug'.
        """
        # 1. Verificar cabeceras de proxy de Vercel
        for h in ("x-matched-path", "x-vercel-original-url", "x-original-url", "x-rewrite-url", "x-forwarded-uri"):
            val = self.headers.get(h)
            if val and val.startswith("/api") and not val.startswith("/api/index.py"):
                self.path = val
                return

        # 2. Verificar query parameter '__slug' inyectado por vercel.json
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if "__slug" in qs and qs["__slug"]:
            slug = qs["__slug"][0].lstrip("/")
            other_qs = {k: v for k, v in qs.items() if k != "__slug"}
            new_query = urllib.parse.urlencode(other_qs, doseq=True)
            self.path = f"/api/{slug}" + (f"?{new_query}" if new_query else "")
            return

        # 3. Si self.path viene como /api/index.py/endpoint
        if self.path.startswith("/api/index.py/"):
            self.path = self.path.replace("/api/index.py/", "/api/", 1)

    def _send_serverless_error(self, exc: Exception, status: int = 500):
        tb = traceback.format_exc()
        sys.stderr.write(f"[ECONODE VERCEL SERVERLESS ERROR] {tb}\n")
        try:
            body = json.dumps({
                "status": "error",
                "message": str(exc),
                "type": type(exc).__name__,
                "traceback": tb
            }, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            self.wfile.write(body)
            try:
                self.wfile.flush()
            except Exception:
                pass
        except Exception:
            pass

    def do_GET(self):
        try:
            self._resolve_real_path()
            super().do_GET()
        except Exception as e:
            self._send_serverless_error(e)

    def do_POST(self):
        try:
            self._resolve_real_path()
            super().do_POST()
        except Exception as e:
            self._send_serverless_error(e)

    def do_OPTIONS(self):
        try:
            self._resolve_real_path()
            super().do_OPTIONS()
        except Exception as e:
            self._send_serverless_error(e)

    def do_HEAD(self):
        try:
            self._resolve_real_path()
            super().do_HEAD()
        except Exception as e:
            self._send_serverless_error(e)
