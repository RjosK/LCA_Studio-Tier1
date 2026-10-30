# Script to generate the spacious canvas board with dynamic Sankey ribbons

canvas_board_html = '''        <!-- Interactive Studio Canvas Viewport (Spacious & Dynamic Sankey Ribbons) -->
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
              <span class="case-canvas-balance-badge" id="canvasBalanceBadge">&radic; Balance de Masa: 100% OK</span>
              <span class="case-canvas-mode-tag" id="canvasModeTag">Modo Ingenier&iacute;a de Procesos</span>
            </div>
          </div>

          <!-- Canvas Stage with Dot Grid, Spacious Layout & Dynamic SVG Sankey Ribbons -->
          <div class="case-canvas-stage-wrap">
            <svg class="case-canvas-svg" viewBox="0 0 1260 680" preserveAspectRatio="xMinYMin meet">
              <defs>
                <!-- Gradients for standard & Sankey modes -->
                <linearGradient id="wireGradStd" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#818CF8" stop-opacity="0.7"/>
                  <stop offset="100%" stop-color="#6366F1" stop-opacity="0.85"/>
                </linearGradient>
                <linearGradient id="wireGradMass" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#10B981" stop-opacity="0.75"/>
                  <stop offset="100%" stop-color="#059669" stop-opacity="0.95"/>
                </linearGradient>
                <linearGradient id="wireGradEnergy" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#0284C7" stop-opacity="0.95"/>
                </linearGradient>
                <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              <!-- Curved Bézier Connector Wires (6 Components into Ensamble with dedicated inputs) -->
              <!-- Wire 1: Cuerpo (1.04 kg / 12.4 MJ) -->
              <path id="wire-cuerpo" d="M 248,58 C 343,58 325,260 420,260" class="canvas-wire wire-cuerpo" />
              
              <!-- Wire 2: Jarra (0.60 kg / 8.2 MJ) -->
              <path id="wire-jarra" d="M 248,168 C 343,168 325,280 420,280" class="canvas-wire wire-jarra" />
              
              <!-- Wire 3: Cable (0.165 kg / 3.1 MJ) -->
              <path id="wire-cable" d="M 248,278 C 343,278 325,300 420,300" class="canvas-wire wire-cable" />
              
              <!-- Wire 4: Partes (0.170 kg / 4.8 MJ) -->
              <path id="wire-partes" d="M 248,388 C 343,388 325,320 420,320" class="canvas-wire wire-partes" />
              
              <!-- Wire 5: Empaque (0.340 kg / 1.9 MJ) -->
              <path id="wire-empaque" d="M 248,498 C 343,498 325,340 420,340" class="canvas-wire wire-empaque" />
              
              <!-- Wire 6: Transporte (0.350 t*km / 14.5 MJ) -->
              <path id="wire-transporte" d="M 248,608 C 343,608 325,360 420,360" class="canvas-wire wire-transporte" />

              <!-- Inlet dots along left edge of Ensamble -->
              <circle cx="420" cy="260" r="3.5" class="canvas-inlet-dot" />
              <circle cx="420" cy="280" r="3.5" class="canvas-inlet-dot" />
              <circle cx="420" cy="300" r="3.5" class="canvas-inlet-dot" />
              <circle cx="420" cy="320" r="3.5" class="canvas-inlet-dot" />
              <circle cx="420" cy="340" r="3.5" class="canvas-inlet-dot" />
              <circle cx="420" cy="360" r="3.5" class="canvas-inlet-dot" />

              <!-- Wire 7: Ensamble into Uso (2.315 kg total machine / 44.9 MJ) -->
              <path id="wire-ensamble-uso" d="M 660,310 C 715,310 715,310 770,310" class="canvas-wire wire-ensamble-uso" />

              <!-- Wire 8: Uso into Disposición (2.315 kg final waste / 0.5 MJ) -->
              <path id="wire-uso-eol" d="M 990,310 C 1035,310 1035,310 1080,310" class="canvas-wire wire-uso-eol" />

              <!-- Sankey Flow Value Tags (Visible in Sankey modes) -->
              <g class="sankey-tag-group" id="sankeyTagGroup" style="opacity: 0; transition: opacity 0.3s ease;">
                <!-- Tag Cuerpo -->
                <rect x="290" y="115" width="80" height="20" rx="4" class="sankey-tag-rect" />
                <text x="330" y="129" text-anchor="middle" class="sankey-tag-text" id="tagValCuerpo">1.040 kg</text>

                <!-- Tag Jarra -->
                <rect x="295" y="200" width="76" height="20" rx="4" class="sankey-tag-rect" />
                <text x="333" y="214" text-anchor="middle" class="sankey-tag-text" id="tagValJarra">0.600 kg</text>

                <!-- Tag Cable -->
                <rect x="295" y="275" width="76" height="20" rx="4" class="sankey-tag-rect" />
                <text x="333" y="289" text-anchor="middle" class="sankey-tag-text" id="tagValCable">0.165 kg</text>

                <!-- Tag Partes -->
                <rect x="295" y="345" width="76" height="20" rx="4" class="sankey-tag-rect" />
                <text x="333" y="359" text-anchor="middle" class="sankey-tag-text" id="tagValPartes">0.170 kg</text>

                <!-- Tag Empaque -->
                <rect x="295" y="415" width="76" height="20" rx="4" class="sankey-tag-rect" />
                <text x="333" y="429" text-anchor="middle" class="sankey-tag-text" id="tagValEmpaque">0.340 kg</text>

                <!-- Tag Transporte -->
                <rect x="295" y="490" width="84" height="20" rx="4" class="sankey-tag-rect" />
                <text x="337" y="504" text-anchor="middle" class="sankey-tag-text" id="tagValTransporte">0.35 t*km</text>

                <!-- Tag Ensamble Trunk -->
                <rect x="680" y="270" width="70" height="22" rx="5" class="sankey-tag-rect highlight" />
                <text x="715" y="285" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEnsamble">2.315 kg</text>

                <!-- Tag EoL Trunk -->
                <rect x="1005" y="270" width="60" height="22" rx="5" class="sankey-tag-rect highlight" />
                <text x="1035" y="285" text-anchor="middle" class="sankey-tag-text highlight" id="tagValEol">2.315 kg</text>
              </g>
            </svg>

            <!-- HTML Process Nodes Positioned Absolute with Generous Whitespace -->
            <div class="case-canvas-nodes-layer">

              <!-- NODE 1: CUERPO -->
              <div class="studio-node-card" style="top: 16px; left: 28px; width: 220px;" onmouseenter="highlightWire('wire-cuerpo')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cuerpo</span>
                  <span class="snode-code">PR-1001</span>
                </div>
                <div class="snode-sub">Pol&iacute;meros &amp; Al</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cuerpo (1 u)" data-mass="Masa: 1.040 kg (44.9%)" data-energy="Energ&iacute;a: 12.4 MJ">&bull; flujo_cuerpo (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PP granulate: 0.94 kg</span>
                  <span>&diams; Injection moulding: 0.94 kg</span>
                  <span>&diams; Al sheet: 0.1 kg</span>
                  <span style="color: #94A3B8;">+ 1 insumo m&aacute;s...</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 126px; left: 28px; width: 220px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_jarra (1 u)" data-mass="Masa: 0.600 kg (25.9%)" data-energy="Energ&iacute;a: 8.2 MJ">&bull; flujo_jarra (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Container glass: 0.4 kg</span>
                  <span>&diams; PP granulate: 0.2 kg</span>
                  <span>&diams; Heat natural gas: 4 MJ</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 236px; left: 28px; width: 220px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cable</span>
                  <span class="snode-code">PR-1003</span>
                </div>
                <div class="snode-sub">Cables &amp; Conectores</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cable (1 u)" data-mass="Masa: 0.165 kg (7.1%)" data-energy="Energ&iacute;a: 3.1 MJ">&bull; flujo_cable (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PVC resin: 105 g</span>
                  <span>&diams; Copper wire: 60 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 346px; left: 28px; width: 220px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Partes</span>
                  <span class="snode-code">PR-1004</span>
                </div>
                <div class="snode-sub">Met&aacute;licos &amp; Placa</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_partes (1 u)" data-mass="Masa: 0.170 kg (7.3%)" data-energy="Energ&iacute;a: 4.8 MJ">&bull; flujo_partes (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Steel tinplate: 150 g</span>
                  <span>&diams; Copper sheet: 20 g</span>
                  <span>&diams; PVC resin: 20 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 456px; left: 28px; width: 220px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje &amp; Manual</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_empaque (1 u)" data-mass="Masa: 0.340 kg (14.7%)" data-energy="Energ&iacute;a: 1.9 MJ">&bull; flujo_empaque (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Corrugated box: 300 g</span>
                  <span>&diams; Graphic paper: 40 g</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 566px; left: 28px; width: 220px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica Intermodal</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_transporte (1 u)" data-mass="Flete: 400 km (0.35 t*km)" data-energy="Energ&iacute;a: 14.5 MJ">&bull; flujo_transporte (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Lorry transport: 0.35 t*km</span>
                </div>
                <div class="snode-port-out" style="top: 42px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 220px; left: 420px; width: 240px;">
                <div class="snode-header">
                  <span class="snode-title">Ensamble</span>
                  <span class="snode-code" style="background: #E8F5E9; color: #0E7F5E;">PR-ENS-01</span>
                </div>
                <div class="snode-sub">Montaje Central (1000W)</div>
                <div class="snode-flow-bar" style="background: #0E7F5E; color: #FFFFFF;" data-std="&bull; flujo_ensamble (1.0 u)" data-mass="Masa Ensamblada: 2.315 kg" data-energy="Energ&iacute;a: 44.9 MJ">&bull; flujo_ensamble (1.0 u)</div>
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
              <div class="studio-node-card" id="cardNodeUso" style="top: 230px; left: 770px; width: 220px;">
                <div class="snode-port-in" style="top: 80px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Uso Cafetera</span>
                  <span class="snode-code">PR-USO-01</span>
                </div>
                <div class="snode-sub">Fase Uso (5 a&ntilde;os &middot; 1,200 ciclos)</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_uso (1.0 u)" data-mass="Consumibles: 8.5 kg" data-energy="Energ&iacute;a: 3,285 MJ (98.6%)">&bull; flujo_uso (1.0 u)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_ensamble [Ensamble]</span>
                  <span>&diams; Electricity AC: 3,285 MJ</span>
                  <span>&diams; Filter paper: 7.3 kg</span>
                  <span>&diams; Agua corriente: 150 L</span>
                </div>
                <div class="snode-port-out" style="top: 80px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 260px; left: 1080px; width: 160px;">
                <div class="snode-port-in" style="top: 50px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Disposici&oacute;n</span>
                  <span class="snode-code">PR-EOL-01</span>
                </div>
                <div class="snode-sub">Fin de Vida (Cuna a Tumba)</div>
                <div class="snode-flow-bar" data-std="&bull; disposicion_flow (1 u)" data-mass="Residuo: 2.315 kg" data-energy="Energ&iacute;a: 0.5 MJ">&bull; disposicion_flow (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_uso [Cafetera en Desuso]</span>
                  <span style="font-size: 8.5px; color: #94A3B8;">Incineraci&oacute;n &amp; Relleno</span>
                </div>
              </div>

            </div>
          </div>

          <!-- Bottom Canvas Footer with Dynamic Legend -->
          <div class="case-canvas-footer">
            <div class="case-canvas-legend-wrap">
              <span class="case-canvas-legend-dot" id="canvasLegendDot"></span>
              <span class="case-canvas-legend-txt" id="canvasLegendText">
                Modo Est&aacute;ndar: Topolog&iacute;a de 10 procesos unitarios con 6 flujos de producto hacia ensamble central.
              </span>
            </div>
            <a href="index.html#viewStudio" class="case-canvas-open-link" onclick="loadAndOpenStudio(event)">
              Abrir modelo interactivo en ECONODE Studio &rarr;
            </a>
          </div>
        </div>
'''

print("Length of canvas_board_html:", len(canvas_board_html))

