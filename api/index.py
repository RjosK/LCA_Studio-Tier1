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

    def do_GET(self):
        self._resolve_real_path()
        super().do_GET()

    def do_POST(self):
        self._resolve_real_path()
        super().do_POST()

    def do_OPTIONS(self):
        self._resolve_real_path()
        super().do_OPTIONS()

    def do_HEAD(self):
        self._resolve_real_path()
        super().do_HEAD()
