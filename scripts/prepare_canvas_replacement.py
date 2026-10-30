canvas_board_html = '''        <!-- Interactive Studio Canvas Viewport (Exact replica of ECONODE Studio Canvas) -->
        <div class="case-canvas-board">
          <!-- Canvas Top Toolbar -->
          <div class="case-canvas-bar">
            <div class="case-canvas-bar-left">
              <span class="case-canvas-dot"></span>
              <span class="case-canvas-title">Lienzo Nodal de Ciclo de Vida: Cafetera Dom&eacute;stica (Pr&aacute;ctica 4)</span>
              <span class="case-canvas-pill">ecoinvent 3.12 Cut-off</span>
            </div>
            <div class="case-canvas-bar-right">
              <span class="case-canvas-balance-badge">&radic; Balance de Masa: 100% OK</span>
              <span class="case-canvas-tag-interactive">Lienzo Interactivo</span>
            </div>
          </div>

          <!-- Canvas Stage with Dot Grid and SVG Connectors -->
          <div class="case-canvas-stage-wrap">
            <svg class="case-canvas-svg" viewBox="0 0 1020 570" preserveAspectRatio="xMinYMin meet">
              <defs>
                <linearGradient id="wireGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#0E7F5E" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#2563EB" stop-opacity="0.9"/>
                </linearGradient>
                <linearGradient id="wireActive" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#55D6A9"/>
                  <stop offset="100%" stop-color="#0E7F5E"/>
                </linearGradient>
              </defs>

              <!-- Curved Bézier Connector Wires (6 Components into Ensamble) -->
              <path d="M 230,55 C 280,55 280,270 330,270" class="canvas-wire wire-cuerpo" />
              <path d="M 230,145 C 280,145 280,270 330,270" class="canvas-wire wire-jarra" />
              <path d="M 230,235 C 280,235 280,270 330,270" class="canvas-wire wire-cable" />
              <path d="M 230,325 C 280,325 280,270 330,270" class="canvas-wire wire-partes" />
              <path d="M 230,415 C 280,415 280,270 330,270" class="canvas-wire wire-empaque" />
              <path d="M 230,505 C 280,505 280,270 330,270" class="canvas-wire wire-transporte" />

              <!-- Ensamble into Uso -->
              <path d="M 540,270 C 570,270 570,270 600,270" class="canvas-wire wire-main" />

              <!-- Uso into Disposición -->
              <path d="M 790,270 C 815,270 815,270 840,270" class="canvas-wire wire-main" />
            </svg>

            <!-- HTML Nodes Positioned Absolute -->
            <div class="case-canvas-nodes-layer">

              <!-- NODE 1: CUERPO -->
              <div class="studio-node-card" style="top: 18px; left: 20px;" onmouseenter="highlightWire('wire-cuerpo')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cuerpo</span>
                  <span class="snode-code">PR-1001</span>
                </div>
                <div class="snode-sub">Pol&iacute;meros &amp; Al</div>
                <div class="snode-flow-bar">&bull; flujo_cuerpo (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PP granulate: 0.94 kg</span>
                  <span>&diams; Injection moulding: 0.94 kg</span>
                  <span>&diams; Al sheet: 0.1 kg</span>
                </div>
                <div class="snode-port-out" style="top: 37px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 108px; left: 20px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar">&bull; flujo_jarra (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Container glass: 0.4 kg</span>
                  <span>&diams; PP granulate: 0.2 kg</span>
                  <span>&diams; Heat natural gas: 4 MJ</span>
                </div>
                <div class="snode-port-out" style="top: 37px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 198px; left: 20px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cable</span>
                  <span class="snode-code">PR-1003</span>
                </div>
                <div class="snode-sub">Cables &amp; Conectores</div>
                <div class="snode-flow-bar">&bull; flujo_cable (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PVC resin: 105 g</span>
                  <span>&diams; Copper wire: 60 g</span>
                </div>
                <div class="snode-port-out" style="top: 37px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 288px; left: 20px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Partes</span>
                  <span class="snode-code">PR-1004</span>
                </div>
                <div class="snode-sub">Met&aacute;licos &amp; Placa</div>
                <div class="snode-flow-bar">&bull; flujo_partes (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Steel tinplate: 150 g</span>
                  <span>&diams; Copper sheet: 20 g</span>
                </div>
                <div class="snode-port-out" style="top: 37px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 378px; left: 20px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje &amp; Manual</div>
                <div class="snode-flow-bar">&bull; flujo_empaque (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Corrugated box: 300 g</span>
                  <span>&diams; Graphic paper: 40 g</span>
                </div>
                <div class="snode-port-out" style="top: 37px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 468px; left: 20px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica Intermodal</div>
                <div class="snode-flow-bar">&bull; flujo_transporte (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Lorry transport: 0.35 t*km</span>
                </div>
                <div class="snode-port-out" style="top: 37px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 170px; left: 330px; width: 210px;">
                <div class="snode-port-in" style="top: 100px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Ensamble</span>
                  <span class="snode-code" style="background: #E8F5E9; color: #0E7F5E;">PR-ENS-01</span>
                </div>
                <div class="snode-sub">Montaje Central (1000W)</div>
                <div class="snode-flow-bar" style="background: #0E7F5E; color: #FFFFFF;">&bull; flujo_ensamble (1.0 item)</div>
                <div class="snode-inputs" style="max-height: 110px;">
                  <span>&diams; flujo_cuerpo [Cuerpo]</span>
                  <span>&diams; flujo_jarra [Jarra]</span>
                  <span>&diams; flujo_cable [Cable]</span>
                  <span>&diams; flujo_partes [Partes]</span>
                  <span>&diams; flujo_empaque [Empaque]</span>
                  <span>&diams; flujo_transporte [Flete]</span>
                </div>
                <div class="snode-port-out" style="top: 100px;"></div>
              </div>

              <!-- NODE 8: USO CAFETERA -->
              <div class="studio-node-card" style="top: 185px; left: 600px; width: 190px;">
                <div class="snode-port-in" style="top: 85px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Uso Cafetera</span>
                  <span class="snode-code">PR-USO-01</span>
                </div>
                <div class="snode-sub">Fase Uso (5 a&ntilde;os)</div>
                <div class="snode-flow-bar">&bull; flujo_uso (1.0 item)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_ensamble [Ensamble]</span>
                  <span>&diams; Electricity AC: 3,285 MJ</span>
                  <span>&diams; Filter paper: 7.3 kg</span>
                  <span>&diams; Tap water: 150 L</span>
                </div>
                <div class="snode-port-out" style="top: 85px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 220px; left: 840px; width: 160px;">
                <div class="snode-port-in" style="top: 50px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Disposici&oacute;n</span>
                  <span class="snode-code">PR-EOL-01</span>
                </div>
                <div class="snode-sub">Fin de Vida</div>
                <div class="snode-flow-bar">&bull; disposicion_flow (1 u)</div>
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
              Abrir modelo interactivo en el lienzo &rarr;
            </a>
          </div>
        </div>
'''

css_canvas = '''
    /* =============================================================
       STUDIO CANVAS REPLICA IN CASE STUDY
       ============================================================= */
    .case-canvas-board {
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.1);
      border-radius: 20px;
      overflow: hidden;
      margin: 28px 0;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
    }

    .case-canvas-bar {
      background: #FAF6ED;
      border-bottom: 1px solid rgba(0, 0, 0, 0.08);
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .case-canvas-bar-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .case-canvas-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #0E7F5E;
      display: inline-block;
    }

    .case-canvas-title {
      font-size: 13px;
      font-weight: 700;
      color: #18232C;
    }

    .case-canvas-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      font-weight: 600;
      background: #ECE9DF;
      color: #55606B;
      padding: 3px 8px;
      border-radius: 999px;
    }

    .case-canvas-bar-right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .case-canvas-balance-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: #0E7F5E;
      background: #E8F5E9;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(14, 127, 94, 0.25);
    }

    .case-canvas-tag-interactive {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      color: #7A8691;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .case-canvas-stage-wrap {
      position: relative;
      width: 100%;
      height: 570px;
      background: #FDFCFA;
      background-image: radial-gradient(rgba(24, 35, 44, 0.08) 1px, transparent 1px);
      background-size: 20px 20px;
      overflow-x: auto;
      overflow-y: hidden;
    }

    .case-canvas-svg {
      position: absolute;
      top: 0;
      left: 0;
      width: 1020px;
      height: 570px;
      pointer-events: none;
      z-index: 1;
    }

    .canvas-wire {
      fill: none;
      stroke: #7C93A4;
      stroke-width: 2px;
      opacity: 0.65;
      transition: all 0.25s ease;
    }

    .canvas-wire.wire-main {
      stroke: #0E7F5E;
      stroke-width: 2.5px;
      opacity: 0.9;
    }

    .canvas-wire.active {
      stroke: #0E7F5E;
      stroke-width: 3.5px;
      opacity: 1;
      filter: drop-shadow(0 2px 6px rgba(14, 127, 94, 0.4));
    }

    .case-canvas-nodes-layer {
      position: absolute;
      top: 0;
      left: 0;
      width: 1020px;
      height: 570px;
      z-index: 2;
    }

    /* Process Node Card in Canvas */
    .studio-node-card {
      position: absolute;
      width: 210px;
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.12);
      border-radius: 12px;
      padding: 10px 12px;
      box-shadow: 0 4px 12px rgba(24, 35, 44, 0.04);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: default;
    }

    .studio-node-card:hover {
      transform: translateY(-2px);
      border-color: #0E7F5E;
      box-shadow: 0 8px 24px rgba(14, 127, 94, 0.12);
    }

    .studio-node-card.highlight-node {
      border-color: #0E7F5E;
      box-shadow: 0 6px 20px rgba(14, 127, 94, 0.1);
    }

    .snode-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2px;
    }

    .snode-title {
      font-size: 12px;
      font-weight: 700;
      color: #18232C;
    }

    .snode-code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px;
      font-weight: 600;
      background: #ECE9DF;
      color: #55606B;
      padding: 1px 6px;
      border-radius: 4px;
    }

    .snode-sub {
      font-size: 10px;
      color: #7A8691;
      margin-bottom: 6px;
    }

    .snode-flow-bar {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px;
      font-weight: 600;
      background: #EBF7EE;
      color: #0E7F5E;
      border: 1px solid rgba(14, 127, 94, 0.2);
      border-radius: 4px;
      padding: 2px 6px;
      margin-bottom: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .snode-inputs {
      font-size: 9.5px;
      color: #55606B;
      display: flex;
      flex-direction: column;
      gap: 2px;
      line-height: 1.35;
      overflow: hidden;
    }

    .snode-port-out {
      position: absolute;
      right: -6px;
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2.5px solid #0E7F5E;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }

    .snode-port-in {
      position: absolute;
      left: -6px;
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2.5px solid #2563EB;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }

    .case-canvas-footer {
      background: #FAF6ED;
      border-top: 1px solid rgba(0, 0, 0, 0.08);
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .case-canvas-legend-txt {
      font-size: 12px;
      color: #55606B;
    }

    .case-canvas-open-link {
      font-size: 12.5px;
      font-weight: 600;
      color: #0E7F5E;
      text-decoration: none;
      transition: transform 0.2s ease;
    }

    .case-canvas-open-link:hover {
      text-decoration: underline;
      transform: translateX(2px);
    }
'''

js_highlight = '''
    function highlightWire(wireClass) {
      document.querySelectorAll('.canvas-wire').forEach(w => w.classList.remove('active'));
      const activeWire = document.querySelector('.' + wireClass);
      if (activeWire) activeWire.classList.add('active');
    }

    function resetWires() {
      document.querySelectorAll('.canvas-wire').forEach(w => w.classList.remove('active'));
    }
'''

with open('C:/Users/Josue/Documents/Espacio/ECONODE/scripts/canvas_replacement_data.py', 'w', encoding='utf-8') as f:
    f.write('# Data container for replacing canvas in case_cafetera.html\\n')

print('Variables prepared')

