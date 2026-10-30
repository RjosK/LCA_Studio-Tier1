import re

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Tuned stage height in CSS: 750px
html = html.replace('height: 680px;', 'height: 750px;')

# Tuned SVG for 750px height with 34px card separation
tuned_svg_750 = '''            <svg class="case-canvas-svg" viewBox="0 0 1040 750" preserveAspectRatio="xMinYMin meet">
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
              <path id="wire-cuerpo" d="M 213,63 C 280,63 265,310 320,310" class="canvas-wire wire-cuerpo" />
              <path id="wire-jarra" d="M 213,183 C 280,183 265,330 320,330" class="canvas-wire wire-jarra" />
              <path id="wire-cable" d="M 213,303 C 275,303 270,350 320,350" class="canvas-wire wire-cable" />
              <path id="wire-partes" d="M 213,423 C 275,423 270,370 320,370" class="canvas-wire wire-partes" />
              <path id="wire-empaque" d="M 213,543 C 280,543 265,390 320,390" class="canvas-wire wire-empaque" />
              <path id="wire-transporte" d="M 213,663 C 280,663 265,410 320,410" class="canvas-wire wire-transporte" />

              <!-- Inlets dots along left edge of Ensamble -->
              <circle cx="320" cy="310" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="330" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="350" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="370" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="390" r="4" class="canvas-inlet-dot" />
              <circle cx="320" cy="410" r="4" class="canvas-inlet-dot" />

              <!-- Ensamble into Uso (2.315 kg total machine) -->
              <path id="wire-ensamble-uso" d="M 540,360 C 585,360 585,360 630,360" class="canvas-wire wire-ensamble-uso" />

              <!-- Uso into Disposición (2.315 kg final waste) -->
              <path id="wire-uso-eol" d="M 835,360 C 862,360 862,360 890,360" class="canvas-wire wire-uso-eol" />

              <!-- Sankey Flow Value Tags (Visible in Sankey modes) -->
              <g class="sankey-tag-group" id="sankeyTagGroup" style="opacity: 1; transition: opacity 0.3s ease;">
                <!-- Tag Cuerpo -->
                <rect x="233" y="130" width="76" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="143" text-anchor="middle" class="sankey-tag-text" id="tagValCuerpo">1.040 kg</text>

                <!-- Tag Jarra -->
                <rect x="235" y="225" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="238" text-anchor="middle" class="sankey-tag-text" id="tagValJarra">0.600 kg</text>

                <!-- Tag Cable -->
                <rect x="235" y="305" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="318" text-anchor="middle" class="sankey-tag-text" id="tagValCable">0.165 kg</text>

                <!-- Tag Partes -->
                <rect x="235" y="385" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="398" text-anchor="middle" class="sankey-tag-text" id="tagValPartes">0.170 kg</text>

                <!-- Tag Empaque -->
                <rect x="235" y="475" width="72" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="488" text-anchor="middle" class="sankey-tag-text" id="tagValEmpaque">0.340 kg</text>

                <!-- Tag Transporte -->
                <rect x="231" y="565" width="80" height="19" rx="4" class="sankey-tag-rect" />
                <text x="271" y="578" text-anchor="middle" class="sankey-tag-text" id="tagValTransporte">0.35 t*km</text>

                <!-- Tag Ensamble Trunk -->
                <rect x="552" y="322" width="66" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="585" y="336" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEnsamble">2.315 kg</text>

                <!-- Tag EoL Trunk -->
                <rect x="832" y="322" width="56" height="21" rx="5" class="sankey-tag-rect highlight" />
                <text x="860" y="336" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEol">2.315 kg</text>
              </g>
            </svg>'''

svg_pattern = r'<svg class="case-canvas-svg".*?</svg>'
html = re.sub(svg_pattern, tuned_svg_750.strip(), html, flags=re.DOTALL)

# Tuned Node Layer HTML with 34px gap between every card in Col 1!
nodes_layer_new = '''            <!-- HTML Process Nodes Positioned Absolute with Generous Whitespace (No Overlapping!) -->
            <div class="case-canvas-nodes-layer">

              <!-- NODE 1: CUERPO -->
              <div class="studio-node-card" style="top: 20px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-cuerpo')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cuerpo</span>
                  <span class="snode-code">PR-1001</span>
                </div>
                <div class="snode-sub">Pol&iacute;meros &amp; Al</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cuerpo (1 u)" data-mass="Masa: 1.040 kg (44.9%)" data-energy="Energ&iacute;a: 12.4 MJ">Masa: 1.040 kg (44.9%)</div>
                <div class="snode-inputs">
                  <span>&bull; PP granulate: 0.94 kg</span>
                  <span>&bull; Al sheet: 0.10 kg</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 140px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_jarra (1 u)" data-mass="Masa: 0.600 kg (25.9%)" data-energy="Energ&iacute;a: 8.2 MJ">Masa: 0.600 kg (25.9%)</div>
                <div class="snode-inputs">
                  <span>&bull; Container glass: 0.40 kg</span>
                  <span>&bull; PP granulate: 0.20 kg</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 260px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cable</span>
                  <span class="snode-code">PR-1003</span>
                </div>
                <div class="snode-sub">Cables &amp; Conectores</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cable (1 u)" data-mass="Masa: 0.165 kg (7.1%)" data-energy="Energ&iacute;a: 3.1 MJ">Masa: 0.165 kg (7.1%)</div>
                <div class="snode-inputs">
                  <span>&bull; PVC resin: 105 g</span>
                  <span>&bull; Copper wire: 60 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 380px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Partes</span>
                  <span class="snode-code">PR-1004</span>
                </div>
                <div class="snode-sub">Met&aacute;licos &amp; Placa</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_partes (1 u)" data-mass="Masa: 0.170 kg (7.3%)" data-energy="Energ&iacute;a: 4.8 MJ">Masa: 0.170 kg (7.3%)</div>
                <div class="snode-inputs">
                  <span>&bull; Steel tinplate: 150 g</span>
                  <span>&bull; Copper sheet: 20 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 500px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje &amp; Manual</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_empaque (1 u)" data-mass="Masa: 0.340 kg (14.7%)" data-energy="Energ&iacute;a: 1.9 MJ">Masa: 0.340 kg (14.7%)</div>
                <div class="snode-inputs">
                  <span>&bull; Corrugated box: 300 g</span>
                  <span>&bull; Graphic paper: 40 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 620px; left: 18px; width: 195px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica Intermodal</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_transporte (1 u)" data-mass="Flete: 400 km (0.35 t*km)" data-energy="Energ&iacute;a: 14.5 MJ">Flete: 400 km (0.35 t*km)</div>
                <div class="snode-inputs">
                  <span>&bull; Cami&oacute;n 16-32t: 0.35 t*km</span>
                  <span>&bull; Di&eacute;sel EURO 5</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 275px; left: 320px; width: 220px;">
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
                <div class="snode-port-out" style="top: 85px;"></div>
              </div>

              <!-- NODE 8: USO CAFETERA -->
              <div class="studio-node-card" id="cardNodeUso" style="top: 285px; left: 630px; width: 205px;">
                <div class="snode-port-in" style="top: 75px;"></div>
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
                <div class="snode-port-out" style="top: 75px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 315px; left: 890px; width: 135px;">
                <div class="snode-port-in" style="top: 45px;"></div>
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

            </div>'''

nodes_pattern = r'<!-- HTML Process Nodes Positioned Absolute.*?</div>\s*</div>\s*<!-- Bottom Canvas Footer'
match_nodes = re.search(nodes_pattern, html, re.DOTALL)
if match_nodes:
    html = html[:match_nodes.start()] + nodes_layer_new.strip() + '\n          </div>\n\n          <!-- Bottom Canvas Footer' + html[match_nodes.end():]
    print("Replaced nodes layer with un-overlapped spacious cards!")
else:
    print("Could not find nodes layer match")

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated case_cafetera.html successfully.")

