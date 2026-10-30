import re

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update SVG with distinct inlet ports and circles
new_svg = '''            <svg class="case-canvas-svg" viewBox="0 0 820 570" preserveAspectRatio="xMinYMin meet">
              <defs>
                <linearGradient id="wireGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#0E7F5E" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#2563EB" stop-opacity="0.9"/>
                </linearGradient>
              </defs>

              <!-- Curved Bézier Connector Wires (6 Components into Ensamble with dedicated inputs) -->
              <path d="M 190,48 C 218,48 212,215 235,215" class="canvas-wire wire-cuerpo" />
              <path d="M 190,138 C 218,138 212,230 235,230" class="canvas-wire wire-jarra" />
              <path d="M 190,228 C 215,228 215,245 235,245" class="canvas-wire wire-cable" />
              <path d="M 190,318 C 215,318 215,260 235,260" class="canvas-wire wire-partes" />
              <path d="M 190,408 C 218,408 212,275 235,275" class="canvas-wire wire-empaque" />
              <path d="M 190,498 C 218,498 212,290 235,290" class="canvas-wire wire-transporte" />

              <!-- Inlets dots on Ensamble -->
              <circle cx="235" cy="215" r="3" fill="#818CF8" />
              <circle cx="235" cy="230" r="3" fill="#818CF8" />
              <circle cx="235" cy="245" r="3" fill="#818CF8" />
              <circle cx="235" cy="260" r="3" fill="#818CF8" />
              <circle cx="235" cy="275" r="3" fill="#818CF8" />
              <circle cx="235" cy="290" r="3" fill="#818CF8" />

              <!-- Ensamble into Uso -->
              <path d="M 430,250 C 450,250 450,250 470,250" class="canvas-wire wire-main" />

              <!-- Uso into Disposición -->
              <path d="M 650,250 C 668,250 668,250 685,250" class="canvas-wire wire-main" />
            </svg>'''

pattern = r'<svg class="case-canvas-svg".*?</svg>'
html = re.sub(pattern, new_svg, html, flags=re.DOTALL)

# Update stage height in CSS
html = html.replace('height: 550px;', 'height: 570px;')

# Ensure Ensamble node ports match y=250 (top: 175px, height: 145px, so y=250 is top: 75px)
html = html.replace('<div class="snode-port-out" style="top: 93px;"></div>', '<div class="snode-port-out" style="top: 75px;"></div>')
html = html.replace('<div class="snode-port-in" style="top: 93px;"></div>', '<div class="snode-port-in" style="top: 75px;"></div>')
html = html.replace('<div class="snode-port-in" style="top: 108px;"></div>', '') # removed since we have 6 inlet dots in SVG!

# For Disposición: top: 220px, y=250 is top: 30px
html = html.replace('<div class="snode-port-in" style="top: 48px;"></div>', '<div class="snode-port-in" style="top: 30px;"></div>')

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Refined SVG wiring and port alignments.")

