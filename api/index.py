"""
api/index.py - Vercel Serverless Function Entrypoint para ECONODE Studio
Permite el despliegue serverless de alta velocidad en Vercel conectado a Supabase PostgreSQL.
"""

import sys
import os

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
    pass

