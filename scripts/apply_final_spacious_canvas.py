import re

canvas_board_final = '''        <!-- Interactive Studio Canvas Viewport (Spacious & Dynamic Sankey Ribbons) -->
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
            <svg class="case-canvas-svg" viewBox="0 0 1060 680" preserveAspectRatio="xMinYMin meet">
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
              <path id="wire-cuerpo" d="M 220,57 C 290,57 270,260 330,260" class="canvas-wire wire-cuerpo" />
              <path id="wire-jarra" d="M 220,167 C 290,167 270,280 330,280" class="canvas-wire wire-jarra" />
              <path id="wire-cable" d="M 220,277 C 285,277 275,300 330,300" class="canvas-wire wire-cable" />
              <path id="wire-partes" d="M 220,387 C 285,387 275,320 330,320" class="canvas-wire wire-partes" />
              <path id="wire-empaque" d="M 220,497 C 290,497 270,340 330,340" class="canvas-wire wire-empaque" />
              <path id="wire-transporte" d="M 220,607 C 290,607 270,360 330,360" class="canvas-wire wire-transporte" />

              <!-- Inlets dots along left edge of Ensamble -->
              <circle cx="330" cy="260" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="280" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="300" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="320" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="340" r="4" class="canvas-inlet-dot" />
              <circle cx="330" cy="360" r="4" class="canvas-inlet-dot" />

              <!-- Ensamble into Uso (2.315 kg total machine) -->
              <path id="wire-ensamble-uso" d="M 550,310 C 600,310 600,310 650,310" class="canvas-wire wire-ensamble-uso" />

              <!-- Uso into Disposición (2.315 kg final waste) -->
              <path id="wire-uso-eol" d="M 855,310 C 885,310 885,310 915,310" class="canvas-wire wire-uso-eol" />

              <!-- Sankey Flow Value Tags (Visible in Sankey modes) -->
              <g class="sankey-tag-group" id="sankeyTagGroup" style="opacity: 1; transition: opacity 0.3s ease;">
                <!-- Tag Cuerpo -->
                <rect x="240" y="112" width="76" height="19" rx="4" class="sankey-tag-rect" />
                <text x="278" y="125" text-anchor="middle" class="sankey-tag-text" id="tagValCuerpo">1.040 kg</text>

                <!-- Tag Jarra -->
                <rect x="242" y="196" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="278" y="209" text-anchor="middle" class="sankey-tag-text" id="tagValJarra">0.600 kg</text>

                <!-- Tag Cable -->
                <rect x="242" y="268" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="278" y="281" text-anchor="middle" class="sankey-tag-text" id="tagValCable">0.165 kg</text>

                <!-- Tag Partes -->
                <rect x="242" y="338" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="278" y="351" text-anchor="middle" class="sankey-tag-text" id="tagValPartes">0.170 kg</text>

                <!-- Tag Empaque -->
                <rect x="242" y="408" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="278" y="421" text-anchor="middle" class="sankey-tag-text" id="tagValEmpaque">0.340 kg</text>

                <!-- Tag Transporte -->
                <rect x="238" y="478" width="80" height="19" rx="4" class="sankey-tag-rect" />
                <text x="278" y="491" text-anchor="middle" class="sankey-tag-text" id="tagValTransporte">0.35 t*km</text>

                <!-- Tag Ensamble Trunk -->
                <rect x="568" y="272" width="66" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="601" y="286" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEnsamble">2.315 kg</text>

                <!-- Tag EoL Trunk -->
                <rect x="858" y="272" width="56" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="886" y="286" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEol">2.315 kg</text>
              </g>
            </svg>

            <!-- HTML Process Nodes Positioned Absolute with Generous Whitespace -->
            <div class="case-canvas-nodes-layer">

              <!-- NODE 1: CUERPO -->
              <div class="studio-node-card" style="top: 15px; left: 20px; width: 200px;" onmouseenter="highlightWire('wire-cuerpo')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cuerpo</span>
                  <span class="snode-code">PR-1001</span>
                </div>
                <div class="snode-sub">Pol&iacute;meros &amp; Al</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cuerpo (1 u)" data-mass="Masa: 1.040 kg (44.9%)" data-energy="Energ&iacute;a: 12.4 MJ">Masa: 1.040 kg (44.9%)</div>
                <div class="snode-inputs">
                  <span>&diams; PP granulate: 0.94 kg</span>
                  <span>&diams; Injection: 0.94 kg</span>
                  <span>&diams; Al sheet: 0.1 kg</span>
                  <span style="color: #94A3B8;">+ 1 insumo m&aacute;s...</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 125px; left: 20px; width: 200px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_jarra (1 u)" data-mass="Masa: 0.600 kg (25.9%)" data-energy="Energ&iacute;a: 8.2 MJ">Masa: 0.600 kg (25.9%)</div>
                <div class="snode-inputs">
                  <span>&diams; Glass: 0.4 kg</span>
                  <span>&diams; PP granulate: 0.2 kg</span>
                  <span>&diams; Gas nat: 4 MJ</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 235px; left: 20px; width: 200px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
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
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 345px; left: 20px; width: 200px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
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
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 455px; left: 20px; width: 200px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje &amp; Manual</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_empaque (1 u)" data-mass="Masa: 0.340 kg (14.7%)" data-energy="Energ&iacute;a: 1.9 MJ">Masa: 0.340 kg (14.7%)</div>
                <div class="snode-inputs">
                  <span>&diams; Corrugated box: 300 g</span>
                  <span>&diams; Graphic paper: 40 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 565px; left: 20px; width: 200px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica Intermodal</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_transporte (1 u)" data-mass="Flete: 400 km (0.35 t*km)" data-energy="Energ&iacute;a: 14.5 MJ">Flete: 400 km (0.35 t*km)</div>
                <div class="snode-inputs">
                  <span>&diams; Lorry transport: 0.35 t*km</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 220px; left: 330px; width: 220px;">
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
                <div class="snode-port-out" style="top: 90px;"></div>
              </div>

              <!-- NODE 8: USO CAFETERA -->
              <div class="studio-node-card" id="cardNodeUso" style="top: 230px; left: 650px; width: 205px;">
                <div class="snode-port-in" style="top: 80px;"></div>
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
                <div class="snode-port-out" style="top: 80px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 260px; left: 915px; width: 135px;">
                <div class="snode-port-in" style="top: 50px;"></div>
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

board_pattern = r'<div class="case-canvas-board.*?<!-- Bottom Canvas Footer -->\s*<div class="case-canvas-footer">.*?</div>\s*</div>'
match = re.search(board_pattern, html, re.DOTALL)
if match:
    html = html[:match.start()] + canvas_board_final.strip() + html[match.end():]
    print("Replaced with final spacious canvas board successfully!")
else:
    print("Could not find canvas board match")

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated case_cafetera.html successfully.")

