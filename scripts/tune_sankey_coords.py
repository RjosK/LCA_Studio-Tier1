import re

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Tuned 1040px SVG with zero scrollbar
tuned_svg = '''            <svg class="case-canvas-svg" viewBox="0 0 1040 680" preserveAspectRatio="xMinYMin meet">
              <defs>
                <linearGradient id="wireGradStd" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#818CF8" stop-opacity="0.75"/>
                  <stop offset="100%" stop-color="#6366F1" stop-opacity="0.88"/>
                </linearGradient>
                <linearGradient id="wireGradMass" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#10B981" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#059669" stop-opacity="0.95"/>
                </linearGradient>
                <linearGradient id="wireGradEnergy" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.85"/>
                  <stop offset="100%" stop-color="#0284C7" stop-opacity="0.95"/>
                </linearGradient>
              </defs>

              <!-- Curved Bézier Connector Wires (6 Components into Ensamble with dedicated inputs) -->
              <path id="wire-cuerpo" d="M 213,57 C 280,57 265,260 320,260" class="canvas-wire wire-cuerpo" />
              <path id="wire-jarra" d="M 213,167 C 280,167 265,280 320,280" class="canvas-wire wire-jarra" />
              <path id="wire-cable" d="M 213,277 C 275,277 270,300 320,300" class="canvas-wire wire-cable" />
              <path id="wire-partes" d="M 213,387 C 275,387 270,320 320,320" class="canvas-wire wire-partes" />
              <path id="wire-empaque" d="M 213,497 C 280,497 265,340 320,340" class="canvas-wire wire-empaque" />
              <path id="wire-transporte" d="M 213,607 C 280,607 265,360 320,360" class="canvas-wire wire-transporte" />

              <!-- Inlets dots along left edge of Ensamble -->
              <circle cx="320" cy="260" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="280" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="300" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="320" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="340" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="360" r="4" class="canvas-inlet-dot" />

              <!-- Ensamble into Uso (2.315 kg total machine) -->
              <path id="wire-ensamble-uso" d="M 540,310 C 585,310 585,310 630,310" class="canvas-wire wire-ensamble-uso" />

              <!-- Uso into Disposición (2.315 kg final waste) -->
              <path id="wire-uso-eol" d="M 835,310 C 862,310 862,310 890,310" class="canvas-wire wire-uso-eol" />

              <!-- Sankey Flow Value Tags (Visible in Sankey modes) -->
              <g class="sankey-tag-group" id="sankeyTagGroup" style="opacity: 1; transition: opacity 0.3s ease;">
                <!-- Tag Cuerpo -->
                <rect x="233" y="112" width="76" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="125" text-anchor="middle" class="sankey-tag-text" id="tagValCuerpo">1.040 kg</text>

                <!-- Tag Jarra -->
                <rect x="235" y="196" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="209" text-anchor="middle" class="sankey-tag-text" id="tagValJarra">0.600 kg</text>

                <!-- Tag Cable -->
                <rect x="235" y="268" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="281" text-anchor="middle" class="sankey-tag-text" id="tagValCable">0.165 kg</text>

                <!-- Tag Partes -->
                <rect x="235" y="338" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="351" text-anchor="middle" class="sankey-tag-text" id="tagValPartes">0.170 kg</text>

                <!-- Tag Empaque -->
                <rect x="235" y="408" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="421" text-anchor="middle" class="sankey-tag-text" id="tagValEmpaque">0.340 kg</text>

                <!-- Tag Transporte -->
                <rect x="231" y="478" width="80" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="491" text-anchor="middle" class="sankey-tag-text" id="tagValTransporte">0.35 t*km</text>

                <!-- Tag Ensamble Trunk -->
                <rect x="552" y="272" width="66" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="585" y="286" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEnsamble">2.315 kg</text>

                <!-- Tag EoL Trunk -->
                <rect x="832" y="272" width="56" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="860" y="286" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEol">2.315 kg</text>
              </g>
            </svg>'''

svg_pattern = r'<svg class="case-canvas-svg".*?</svg>'
html = re.sub(svg_pattern, tuned_svg.strip(), html, flags=re.DOTALL)

# Update node card inline positions
# Col 1: left: 18px, width: 195px
html = html.replace('style="top: 15px; left: 20px; width: 200px;"', 'style="top: 15px; left: 18px; width: 195px;"')
html = html.replace('style="top: 125px; left: 20px; width: 200px;"', 'style="top: 125px; left: 18px; width: 195px;"')
html = html.replace('style="top: 235px; left: 20px; width: 200px;"', 'style="top: 235px; left: 18px; width: 195px;"')
html = html.replace('style="top: 345px; left: 20px; width: 200px;"', 'style="top: 345px; left: 18px; width: 195px;"')
html = html.replace('style="top: 455px; left: 20px; width: 200px;"', 'style="top: 455px; left: 18px; width: 195px;"')
html = html.replace('style="top: 565px; left: 20px; width: 200px;"', 'style="top: 565px; left: 18px; width: 195px;"')

# Col 2: left: 320px, width: 220px
html = html.replace('style="top: 220px; left: 330px; width: 220px;"', 'style="top: 220px; left: 320px; width: 220px;"')

# Col 3: left: 630px, width: 205px
html = html.replace('style="top: 230px; left: 650px; width: 205px;"', 'style="top: 230px; left: 630px; width: 205px;"')

# Col 4: left: 890px, width: 135px
html = html.replace('style="top: 260px; left: 915px; width: 135px;"', 'style="top: 260px; left: 890px; width: 135px;"')

# Update CSS dimensions of svg and nodes layer to 1040px
html = html.replace('width: 1260px;', 'width: 1040px;')

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Tuned coordinates saved successfully.")

