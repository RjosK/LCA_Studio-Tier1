import re

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Tuned Canvas HTML that fits cleanly in 820px
new_canvas_html = '''        <!-- Interactive Studio Canvas Viewport (Exact replica of ECONODE Studio Canvas) -->
        <div class="case-canvas-board">
          <!-- Canvas Top Toolbar -->
          <div class="case-canvas-bar">
            <div class="case-canvas-bar-left">
              <span class="case-canvas-dot"></span>
              <span class="case-canvas-title">Lienzo Nodal de Ciclo de Vida: Cafetera Dom&eacute;stica (Pr&aacute;ctica 4)</span>
              <span class="case-canvas-pill">ecoinvent 3.12 Cut-off</span>
              <div class="case-canvas-modes">
                <button type="button" class="case-canvas-mode-btn active" id="btnModeStd" onclick="setCanvasMode('std')">Est&aacute;ndar</button>
                <button type="button" class="case-canvas-mode-btn" id="btnModeMass" onclick="setCanvasMode('mass')">Sankey Masa</button>
                <button type="button" class="case-canvas-mode-btn" id="btnModeEnergy" onclick="setCanvasMode('energy')">Sankey Energ&iacute;a</button>
              </div>
            </div>
            <div class="case-canvas-bar-right">
              <span class="case-canvas-balance-badge">&radic; Balance de Masa: 100% OK</span>
            </div>
          </div>

          <!-- Canvas Stage with Dot Grid and SVG Connectors -->
          <div class="case-canvas-stage-wrap">
            <svg class="case-canvas-svg" viewBox="0 0 820 550" preserveAspectRatio="xMinYMin meet">
              <defs>
                <linearGradient id="wireGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#0E7F5E" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#2563EB" stop-opacity="0.9"/>
                </linearGradient>
              </defs>

              <!-- Curved Bézier Connector Wires (6 Components into Ensamble) -->
              <path d="M 190,48 C 215,48 210,268 235,268" class="canvas-wire wire-cuerpo" />
              <path d="M 190,138 C 215,138 210,268 235,268" class="canvas-wire wire-jarra" />
              <path d="M 190,228 C 215,228 210,268 235,268" class="canvas-wire wire-cable" />
              <path d="M 190,318 C 215,318 210,268 235,268" class="canvas-wire wire-partes" />
              <path d="M 190,408 C 215,408 210,268 235,268" class="canvas-wire wire-empaque" />
              <path d="M 190,498 C 215,498 210,268 235,268" class="canvas-wire wire-transporte" />

              <!-- Ensamble into Uso -->
              <path d="M 430,268 C 450,268 450,268 470,268" class="canvas-wire wire-main" />

              <!-- Uso into Disposición -->
              <path d="M 650,268 C 668,268 668,268 685,268" class="canvas-wire wire-main" />
            </svg>

            <!-- HTML Nodes Positioned Absolute -->
            <div class="case-canvas-nodes-layer">

              <!-- NODE 1: CUERPO -->
              <div class="studio-node-card" style="top: 12px; left: 15px; width: 175px;" onmouseenter="highlightWire('wire-cuerpo')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cuerpo</span>
                  <span class="snode-code">PR-1001</span>
                </div>
                <div class="snode-sub">Pol&iacute;meros &amp; Al</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cuerpo (1 u)" data-mass="Masa: 1.04 kg" data-energy="12.4 MJ">&bull; flujo_cuerpo (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PP granulate: 0.94 kg</span>
                  <span>&diams; Injection: 0.94 kg</span>
                  <span>&diams; Al sheet: 0.1 kg</span>
                </div>
                <div class="snode-port-out" style="top: 36px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 102px; left: 15px; width: 175px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_jarra (1 u)" data-mass="Masa: 0.60 kg" data-energy="8.2 MJ">&bull; flujo_jarra (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Glass: 0.4 kg</span>
                  <span>&diams; PP granulate: 0.2 kg</span>
                  <span>&diams; Heat natural gas: 4 MJ</span>
                </div>
                <div class="snode-port-out" style="top: 36px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 192px; left: 15px; width: 175px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cable</span>
                  <span class="snode-code">PR-1003</span>
                </div>
                <div class="snode-sub">Cables</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cable (1 u)" data-mass="Masa: 0.16 kg" data-energy="3.1 MJ">&bull; flujo_cable (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PVC resin: 105 g</span>
                  <span>&diams; Copper wire: 60 g</span>
                </div>
                <div class="snode-port-out" style="top: 36px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 282px; left: 15px; width: 175px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Partes</span>
                  <span class="snode-code">PR-1004</span>
                </div>
                <div class="snode-sub">Met&aacute;licos</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_partes (1 u)" data-mass="Masa: 0.17 kg" data-energy="4.8 MJ">&bull; flujo_partes (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Steel tinplate: 150 g</span>
                  <span>&diams; Copper sheet: 20 g</span>
                </div>
                <div class="snode-port-out" style="top: 36px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 372px; left: 15px; width: 175px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_empaque (1 u)" data-mass="Masa: 0.34 kg" data-energy="1.9 MJ">&bull; flujo_empaque (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Corrugated box: 300 g</span>
                  <span>&diams; Graphic paper: 40 g</span>
                </div>
                <div class="snode-port-out" style="top: 36px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 462px; left: 15px; width: 175px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_transporte (1 u)" data-mass="400 km flete" data-energy="14.5 MJ">&bull; flujo_transporte (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Lorry: 0.35 t*km</span>
                </div>
                <div class="snode-port-out" style="top: 36px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 175px; left: 235px; width: 195px;">
                <div class="snode-port-in" style="top: 93px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Ensamble</span>
                  <span class="snode-code" style="background: #E8F5E9; color: #0E7F5E;">PR-ENS-01</span>
                </div>
                <div class="snode-sub">Montaje Central (1000W)</div>
                <div class="snode-flow-bar" style="background: #0E7F5E; color: #FFFFFF;" data-std="&bull; flujo_ensamble (1.0 u)" data-mass="Masa: 2.315 kg" data-energy="0.8 MJ">&bull; flujo_ensamble (1.0 u)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_cuerpo [Cuerpo]</span>
                  <span>&diams; flujo_jarra [Jarra]</span>
                  <span>&diams; flujo_cable [Cable]</span>
                  <span style="color: #94A3B8;">+ 3 flujos m&aacute;s...</span>
                </div>
                <div class="snode-port-out" style="top: 93px;"></div>
              </div>

              <!-- NODE 8: USO CAFETERA -->
              <div class="studio-node-card" style="top: 175px; left: 470px; width: 180px;">
                <div class="snode-port-in" style="top: 93px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Uso Cafetera</span>
                  <span class="snode-code">PR-USO-01</span>
                </div>
                <div class="snode-sub">Fase Uso (5 a&ntilde;os)</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_uso (1.0 u)" data-mass="Insumos: 8.5 kg" data-energy="3,285 MJ">&bull; flujo_uso (1.0 u)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_ensamble [Ensamble]</span>
                  <span>&diams; Electricity AC: 3,285 MJ</span>
                  <span>&diams; Filter paper: 7.3 kg</span>
                </div>
                <div class="snode-port-out" style="top: 93px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 220px; left: 685px; width: 125px;">
                <div class="snode-port-in" style="top: 48px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Disposici&oacute;n</span>
                  <span class="snode-code" style="font-size: 8px;">PR-EOL</span>
                </div>
                <div class="snode-sub">Fin de Vida</div>
                <div class="snode-flow-bar" data-std="&bull; disposicion (1 u)" data-mass="2.3 kg" data-energy="0.5 MJ">&bull; disposicion (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_uso [Uso]</span>
                </div>
              </div>

            </div>
          </div>

          <!-- Bottom Canvas Footer -->
          <div class="case-canvas-footer">
            <span class="case-canvas-legend-txt">Topolog&iacute;a de 10 procesos unitarios interconectados con 6 flujos de producto y 1 flujo de referencia.</span>
            <a href="index.html#viewStudio" class="case-canvas-open-link" onclick="loadAndOpenStudio(event)">
              Abrir modelo interactivo en ECONODE Studio &rarr;
            </a>
          </div>
        </div>'''

# Replace current .case-canvas-board with new_canvas_html
pattern = r'<div class="case-canvas-board">.*?<!-- Bottom Canvas Footer -->\s*<div class="case-canvas-footer">.*?</div>\s*</div>'
match = re.search(pattern, html, re.DOTALL)
if match:
    html = html[:match.start()] + new_canvas_html + html[match.end():]
    print("Replaced with tuned 820px canvas board successfully!")
else:
    print("Could not find case-canvas-board match with regex")

# Also update the stage-wrap and svg styles
html = html.replace('width: 1020px;', 'width: 100%; max-width: 820px;')
html = html.replace('height: 570px;', 'height: 550px;')

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated case_cafetera.html")

