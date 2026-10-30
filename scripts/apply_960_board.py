import re

tuned_spacious_board_960 = '''        <!-- Interactive Studio Canvas Viewport (Spacious & Dynamic Sankey Ribbons - 960px Height) -->
        <div class="case-canvas-board sankey-mode-mass">
          <!-- Canvas Top Toolbar -->
          <div class="case-canvas-bar">
            <div class="case-canvas-bar-left">
              <span class="case-canvas-dot"></span>
              <span class="case-canvas-title">Lienzo Nodal de Ciclo de Vida: Cafetera Dom&eacute;stica (Pr&aacute;ctica 4)</span>
              <span class="case-canvas-pill">ecoinvent 3.12 Cut-off</span>
              <div class="case-canvas-modes">
                <button type="button" class="case-canvas-mode-btn" id="btnModeStd" onclick="setCanvasMode('std')">Est&aacute;ndar</button>
                <button type="button" class="case-canvas-mode-btn active" id="btnModeMass" onclick="setCanvasMode('mass')">Sankey Masa</button>
                <button type="button" class="case-canvas-mode-btn" id="btnModeEnergy" onclick="setCanvasMode('energy')">Sankey Energ&iacute;a</button>
              </div>
            </div>
            <div class="case-canvas-bar-right">
              <span class="case-canvas-balance-badge" id="canvasBalanceBadge" style="color: #059669; background: #ECFDF5;">&radic; Masa Entrante = Saliente (2.315 kg)</span>
              <span class="case-canvas-mode-tag" id="canvasModeTag">Sankey de Masa F&iacute;sica</span>
            </div>
          </div>

          <!-- Canvas Stage with Dot Grid, Spacious Layout & Dynamic SVG Sankey Ribbons -->
          <div class="case-canvas-stage-wrap">
            <svg class="case-canvas-svg" viewBox="0 0 1040 960" preserveAspectRatio="xMinYMin meet">
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
              <path id="wire-cuerpo" d="M 213,75 C 290,75 270,420 330,420" class="canvas-wire wire-cuerpo" />
              <path id="wire-jarra" d="M 213,230 C 290,230 270,440 330,440" class="canvas-wire wire-jarra" />
              <path id="wire-cable" d="M 213,385 C 285,385 275,460 330,460" class="canvas-wire wire-cable" />
              <path id="wire-partes" d="M 213,540 C 285,540 275,480 330,480" class="canvas-wire wire-partes" />
              <path id="wire-empaque" d="M 213,695 C 290,695 270,500 330,500" class="canvas-wire wire-empaque" />
              <path id="wire-transporte" d="M 213,850 C 290,850 270,520 330,520" class="canvas-wire wire-transporte" />

              <!-- Inlets dots along left edge of Ensamble -->
              <circle cx="330" cy="420" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="440" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="460" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="480" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="500" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="520" r="4" class="canvas-inlet-dot" />

              <!-- Ensamble into Uso (2.315 kg total machine) -->
              <path id="wire-ensamble-uso" d="M 550,470 C 595,470 595,470 640,470" class="canvas-wire wire-ensamble-uso" />

              <!-- Uso into Disposición (2.315 kg final waste) -->
              <path id="wire-uso-eol" d="M 845,470 C 872,470 872,470 900,470" class="canvas-wire wire-uso-eol" />

              <!-- Sankey Flow Value Tags (Visible in Sankey modes) -->
              <g class="sankey-tag-group" id="sankeyTagGroup" style="opacity: 1; transition: opacity 0.3s ease;">
                <!-- Tag Cuerpo -->
                <rect x="238" y="155" width="76" height="19" rx="4" class="sankey-tag-rect" />
                <text x="276" y="168" text-anchor="middle" class="sankey-tag-text" id="tagValCuerpo">1.040 kg</text>

                <!-- Tag Jarra -->
                <rect x="240" y="295" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="276" y="308" text-anchor="middle" class="sankey-tag-text" id="tagValJarra">0.600 kg</text>

                <!-- Tag Cable -->
                <rect x="240" y="410" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="276" y="423" text-anchor="middle" class="sankey-tag-text" id="tagValCable">0.165 kg</text>

                <!-- Tag Partes -->
                <rect x="240" y="500" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="276" y="513" text-anchor="middle" class="sankey-tag-text" id="tagValPartes">0.170 kg</text>

                <!-- Tag Empaque -->
                <rect x="240" y="605" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="276" y="618" text-anchor="middle" class="sankey-tag-text" id="tagValEmpaque">0.340 kg</text>

                <!-- Tag Transporte -->
                <rect x="236" y="730" width="80" height="19" rx="4" class="sankey-tag-rect" />
                <text x="276" y="743" text-anchor="middle" class="sankey-tag-text" id="tagValTransporte">0.35 t*km</text>

                <!-- Tag Ensamble Trunk -->
                <rect x="562" y="432" width="66" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="595" y="446" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEnsamble">2.315 kg</text>

                <!-- Tag EoL Trunk -->
                <rect x="842" y="432" width="56" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="870" y="446" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEol">2.315 kg</text>
              </g>
            </svg>

            <!-- HTML Process Nodes Positioned Absolute with Generous Whitespace (35px gap!) -->
            <div class="case-canvas-nodes-layer">

              <!-- NODE 1: CUERPO -->
              <div class="studio-node-card" style="top: 25px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-cuerpo')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cuerpo</span>
                  <span class="snode-code">PR-1001</span>
                </div>
                <div class="snode-sub">Pol&iacute;meros &amp; Al</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cuerpo (1 u)" data-mass="Masa: 1.040 kg (44.9%)" data-energy="Energ&iacute;a: 12.4 MJ">Masa: 1.040 kg (44.9%)</div>
                <div class="snode-inputs">
                  <span>&diams; PP granulate: 0.94 kg</span>
                  <span>&diams; Injection: 0.94 kg</span>
                  <span>&diams; Al sheet: 0.10 kg</span>
                </div>
                <div class="snode-port-out" style="top: 50px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 180px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_jarra (1 u)" data-mass="Masa: 0.600 kg (25.9%)" data-energy="Energ&iacute;a: 8.2 MJ">Masa: 0.600 kg (25.9%)</div>
                <div class="snode-inputs">
                  <span>&diams; Glass: 0.40 kg</span>
                  <span>&diams; PP granulate: 0.20 kg</span>
                  <span>&diams; Gas nat: 4.0 MJ</span>
                </div>
                <div class="snode-port-out" style="top: 50px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 335px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cable</span>
                  <span class="snode-code">PR-1003</span>
                </div>
                <div class="snode-sub">Cables &amp; Conectores</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cable (1 u)" data-mass="Masa: 0.165 kg (7.1%)" data-energy="Energ&iacute;a: 3.1 MJ">Masa: 0.165 kg (7.1%)</div>
                <div class="snode-inputs">
                  <span>&diams; PVC resin: 105 g</span>
                  <span>&diams; Copper wire: 60 g</span>
                </div>
                <div class="snode-port-out" style="top: 50px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 490px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Partes</span>
                  <span class="snode-code">PR-1004</span>
                </div>
                <div class="snode-sub">Met&aacute;licos &amp; Placa</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_partes (1 u)" data-mass="Masa: 0.170 kg (7.3%)" data-energy="Energ&iacute;a: 4.8 MJ">Masa: 0.170 kg (7.3%)</div>
                <div class="snode-inputs">
                  <span>&diams; Steel tinplate: 150 g</span>
                  <span>&diams; Copper sheet: 20 g</span>
                  <span>&diams; PVC resin: 20 g</span>
                </div>
                <div class="snode-port-out" style="top: 50px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 645px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje &amp; Manual</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_empaque (1 u)" data-mass="Masa: 0.340 kg (14.7%)" data-energy="Energ&iacute;a: 1.9 MJ">Masa: 0.340 kg (14.7%)</div>
                <div class="snode-inputs">
                  <span>&diams; Corrugated box: 300 g</span>
                  <span>&diams; Graphic paper: 40 g</span>
                  <span>&diams; Film PE: 10 g</span>
                </div>
                <div class="snode-port-out" style="top: 50px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 800px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica Intermodal</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_transporte (1 u)" data-mass="Flete: 400 km (0.35 t*km)" data-energy="Energ&iacute;a: 14.5 MJ">Flete: 400 km (0.35 t*km)</div>
                <div class="snode-inputs">
                  <span>&diams; Cami&oacute;n 16-32t: 0.35 t*km</span>
                  <span>&diams; Di&eacute;sel EURO 5</span>
                </div>
                <div class="snode-port-out" style="top: 50px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 375px; left: 330px; width: 220px;">
                <div class="snode-header">
                  <span class="snode-title">Ensamble</span>
                  <span class="snode-code" style="background: #E8F5E9; color: #0E7F5E;">PR-ENS-01</span>
                </div>
                <div class="snode-sub">Montaje Central (1000W)</div>
                <div class="snode-flow-bar" style="background: #0E7F5E; color: #FFFFFF;" data-std="&bull; flujo_ensamble (1.0 u)" data-mass="Masa Ensamblada: 2.315 kg" data-energy="Energ&iacute;a: 44.9 MJ">Masa Ensamblada: 2.315 kg</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_cuerpo [Cuerpo] (1.04 kg)</span>
                  <span>&diams; flujo_jarra [Jarra] (0.60 kg)</span>
                  <span>&diams; flujo_cable [Cable] (0.165 kg)</span>
                  <span>&diams; flujo_partes [Partes] (0.170 kg)</span>
                  <span>&diams; flujo_empaque [Empaque] (0.340 kg)</span>
                  <span>&diams; flujo_transporte [Log&iacute;stica]</span>
                </div>
                <div class="snode-port-out" style="top: 95px;"></div>
              </div>

              <!-- NODE 8: USO CAFETERA -->
              <div class="studio-node-card" id="cardNodeUso" style="top: 385px; left: 640px; width: 205px;">
                <div class="snode-port-in" style="top: 85px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Uso Cafetera</span>
                  <span class="snode-code">PR-USO-01</span>
                </div>
                <div class="snode-sub">Fase Uso (5 a&ntilde;os &middot; 1,200 ciclos)</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_uso (1.0 u)" data-mass="Consumibles: 8.5 kg" data-energy="Energ&iacute;a: 3,285 MJ (98.6%)">Consumibles: 8.5 kg</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_ensamble [Ensamble]</span>
                  <span>&diams; Electricity AC: 3,285 MJ</span>
                  <span>&diams; Filter paper: 7.3 kg</span>
                  <span>&diams; Agua corriente: 150 L</span>
                </div>
                <div class="snode-port-out" style="top: 85px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 415px; left: 900px; width: 135px;">
                <div class="snode-port-in" style="top: 55px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Disposici&oacute;n</span>
                  <span class="snode-code" style="font-size: 8px;">PR-EOL</span>
                </div>
                <div class="snode-sub">Fin de Vida</div>
                <div class="snode-flow-bar" data-std="&bull; disposicion (1 u)" data-mass="Residuo: 2.315 kg" data-energy="Energ&iacute;a: 0.5 MJ">Residuo: 2.315 kg</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_uso [Uso]</span>
                  <span style="font-size: 8.5px; color: #94A3B8;">Relleno &amp; Incin.</span>
                </div>
              </div>

            </div>
          </div>

          <!-- Bottom Canvas Footer with Dynamic Legend -->
          <div class="case-canvas-footer">
            <div class="case-canvas-legend-wrap">
              <span class="case-canvas-legend-dot" id="canvasLegendDot" style="background: #059669;"></span>
              <span class="case-canvas-legend-txt" id="canvasLegendText">
                <strong>Sankey de Masa</strong>: El grosor de cada l&iacute;nea de flujo es proporcional a la masa f&iacute;sica (kg) que alimenta al ensamble (total 2.315 kg).
              </span>
            </div>
            <a href="index.html#viewStudio" class="case-canvas-open-link" onclick="loadAndOpenStudio(event)">
              Abrir modelo interactivo en ECONODE Studio &rarr;
            </a>
          </div>
        </div>'''

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update CSS stage height to 960px
html = html.replace('height: 750px;', 'height: 960px;')
html = html.replace('height: 680px;', 'height: 960px;')

# Replace board
board_pattern = r'<div class="case-canvas-board.*?<!-- Bottom Canvas Footer -->\s*<div class="case-canvas-footer">.*?</div>\s*</div>'
match = re.search(board_pattern, html, re.DOTALL)
if match:
    html = html[:match.start()] + tuned_spacious_board_960.strip() + html[match.end():]
    print("Replaced with 960px spacious board successfully!")
else:
    print("Could not find regex match, falling back to substring")
    idx1 = html.find('<div class="case-canvas-board')
    idx2 = html.find('<p class="case-section-text">\n          La matriz de tecnolog', idx1)
    if idx1 != -1 and idx2 != -1:
        html = html[:idx1] + tuned_spacious_board_960.strip() + '\n\n        ' + html[idx2:]
        print("Replaced via substring successfully!")

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved case_cafetera.html with 960px height and 35px separation between every card.")

