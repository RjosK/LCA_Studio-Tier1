import sys

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Prepare CSS to insert before </style>
css_add = '''
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
      flex-wrap: wrap;
    }

    .case-canvas-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #0E7F5E;
      display: inline-block;
      box-shadow: 0 0 0 3px rgba(14, 127, 94, 0.2);
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

    .case-canvas-modes {
      display: inline-flex;
      background: #ECE9DF;
      padding: 2px;
      border-radius: 8px;
      gap: 2px;
      margin-left: 6px;
    }

    .case-canvas-mode-btn {
      border: none;
      background: transparent;
      font-family: 'JetBrains Mono', monospace;
      font-size: 10.5px;
      font-weight: 600;
      color: #55606B;
      padding: 3px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .case-canvas-mode-btn.active {
      background: #FFFFFF;
      color: #18232C;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

    .case-canvas-stage-wrap {
      position: relative;
      width: 100%;
      height: 570px;
      background: #FDFCFA;
      background-image: radial-gradient(rgba(24, 35, 44, 0.08) 1.2px, transparent 1.2px);
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
      stroke: #818CF8;
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
      filter: drop-shadow(0 2px 8px rgba(14, 127, 94, 0.5));
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
      width: 215px;
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.12);
      border-radius: 12px;
      padding: 9px 11px;
      box-shadow: 0 4px 12px rgba(24, 35, 44, 0.04);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
    }

    .studio-node-card:hover {
      transform: translateY(-2px);
      border-color: #0E7F5E;
      box-shadow: 0 8px 24px rgba(14, 127, 94, 0.12);
    }

    .studio-node-card.highlight-node {
      border: 2px solid #0E7F5E;
      box-shadow: 0 6px 20px rgba(14, 127, 94, 0.15);
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
      margin-bottom: 5px;
    }

    .snode-flow-bar {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px;
      font-weight: 600;
      background: #EBF7EE;
      color: #0E7F5E;
      border: 1px solid rgba(14, 127, 94, 0.25);
      border-radius: 4px;
      padding: 2.5px 6px;
      margin-bottom: 5px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      transition: all 0.2s ease;
    }

    .snode-inputs {
      font-size: 9px;
      color: #55606B;
      display: flex;
      flex-direction: column;
      gap: 2px;
      line-height: 1.35;
      overflow: hidden;
    }

    .snode-inputs span {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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

# 2. Prepare Canvas HTML
canvas_board_html = '''        <!-- Interactive Studio Canvas Viewport (Exact replica of ECONODE Studio Canvas) -->
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
            <svg class="case-canvas-svg" viewBox="0 0 1020 570" preserveAspectRatio="xMinYMin meet">
              <defs>
                <linearGradient id="wireGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#0E7F5E" stop-opacity="0.8"/>
                  <stop offset="100%" stop-color="#2563EB" stop-opacity="0.9"/>
                </linearGradient>
              </defs>

              <!-- Curved Bézier Connector Wires (6 Components into Ensamble) -->
              <path d="M 235,53 C 285,53 285,268 335,268" class="canvas-wire wire-cuerpo" />
              <path d="M 235,143 C 285,143 285,268 335,268" class="canvas-wire wire-jarra" />
              <path d="M 235,233 C 285,233 285,268 335,268" class="canvas-wire wire-cable" />
              <path d="M 235,323 C 285,323 285,268 335,268" class="canvas-wire wire-partes" />
              <path d="M 235,413 C 285,413 285,268 335,268" class="canvas-wire wire-empaque" />
              <path d="M 235,503 C 285,503 285,268 335,268" class="canvas-wire wire-transporte" />

              <!-- Ensamble into Uso -->
              <path d="M 550,268 C 575,268 575,268 600,268" class="canvas-wire wire-main" />

              <!-- Uso into Disposición -->
              <path d="M 795,268 C 818,268 818,268 840,268" class="canvas-wire wire-main" />
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
                <div class="snode-flow-bar" data-std="&bull; flujo_cuerpo (1 u)" data-mass="Masa: 1.040 kg" data-energy="Energ&iacute;a: 12.4 MJ">&bull; flujo_cuerpo (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PP granulate: 0.94 kg</span>
                  <span>&diams; Injection moulding: 0.94 kg</span>
                  <span>&diams; Al sheet: 0.1 kg</span>
                  <span style="color: #94A3B8;">+ 1 insumo m&aacute;s...</span>
                </div>
                <div class="snode-port-out" style="top: 35px;"></div>
              </div>

              <!-- NODE 2: JARRA -->
              <div class="studio-node-card" style="top: 108px; left: 20px;" onmouseenter="highlightWire('wire-jarra')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Jarra</span>
                  <span class="snode-code">PR-1002</span>
                </div>
                <div class="snode-sub">Vidrio &amp; PP</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_jarra (1 u)" data-mass="Masa: 0.600 kg" data-energy="Energ&iacute;a: 8.2 MJ">&bull; flujo_jarra (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Container glass: 0.4 kg</span>
                  <span>&diams; PP granulate: 0.2 kg</span>
                  <span>&diams; Heat natural gas: 4 MJ</span>
                </div>
                <div class="snode-port-out" style="top: 35px;"></div>
              </div>

              <!-- NODE 3: CABLE -->
              <div class="studio-node-card" style="top: 198px; left: 20px;" onmouseenter="highlightWire('wire-cable')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Cable</span>
                  <span class="snode-code">PR-1003</span>
                </div>
                <div class="snode-sub">Cables</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_cable (1 u)" data-mass="Masa: 0.165 kg" data-energy="Energ&iacute;a: 3.1 MJ">&bull; flujo_cable (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PVC resin: 105 g</span>
                  <span>&diams; Copper wire: 60 g</span>
                </div>
                <div class="snode-port-out" style="top: 35px;"></div>
              </div>

              <!-- NODE 4: PARTES -->
              <div class="studio-node-card" style="top: 288px; left: 20px;" onmouseenter="highlightWire('wire-partes')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Partes</span>
                  <span class="snode-code">PR-1004</span>
                </div>
                <div class="snode-sub">Met&aacute;licos</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_partes (1 u)" data-mass="Masa: 0.170 kg" data-energy="Energ&iacute;a: 4.8 MJ">&bull; flujo_partes (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Steel tinplate: 150 g</span>
                  <span>&diams; Copper sheet: 20 g</span>
                  <span>&diams; PVC resin: 20 g</span>
                </div>
                <div class="snode-port-out" style="top: 35px;"></div>
              </div>

              <!-- NODE 5: EMPAQUE -->
              <div class="studio-node-card" style="top: 378px; left: 20px;" onmouseenter="highlightWire('wire-empaque')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Empaque</span>
                  <span class="snode-code">PR-1005</span>
                </div>
                <div class="snode-sub">Embalaje</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_empaque (1 u)" data-mass="Masa: 0.340 kg" data-energy="Energ&iacute;a: 1.9 MJ">&bull; flujo_empaque (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; PE-LD granulate: 10 g</span>
                  <span>&diams; Corrugated box: 300 g</span>
                  <span>&diams; Graphic paper: 40 g</span>
                </div>
                <div class="snode-port-out" style="top: 35px;"></div>
              </div>

              <!-- NODE 6: TRANSPORTE -->
              <div class="studio-node-card" style="top: 468px; left: 20px;" onmouseenter="highlightWire('wire-transporte')" onmouseleave="resetWires()">
                <div class="snode-header">
                  <span class="snode-title">Transporte</span>
                  <span class="snode-code">PR-1006</span>
                </div>
                <div class="snode-sub">Log&iacute;stica</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_transporte (1 u)" data-mass="Distancia: 400 km" data-energy="Energ&iacute;a: 14.5 MJ">&bull; flujo_transporte (1 u)</div>
                <div class="snode-inputs">
                  <span>&diams; Lorry transport: 0.35 t*km</span>
                </div>
                <div class="snode-port-out" style="top: 35px;"></div>
              </div>

              <!-- NODE 7: ENSAMBLE CENTRAL -->
              <div class="studio-node-card highlight-node" style="top: 160px; left: 335px; width: 215px;">
                <div class="snode-port-in" style="top: 108px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Ensamble</span>
                  <span class="snode-code" style="background: #E8F5E9; color: #0E7F5E;">PR-ENS-01</span>
                </div>
                <div class="snode-sub">Montaje Central (1000W)</div>
                <div class="snode-flow-bar" style="background: #0E7F5E; color: #FFFFFF;" data-std="&bull; flujo_ensamble (1.0 item)" data-mass="Masa Total: 2.315 kg" data-energy="Energ&iacute;a: 0.8 MJ">&bull; flujo_ensamble (1.0 item)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_cuerpo [Cuerpo]</span>
                  <span>&diams; flujo_jarra [Jarra]</span>
                  <span>&diams; flujo_cable [Cable]</span>
                  <span style="color: #94A3B8;">+ 3 insumos m&aacute;s...</span>
                </div>
                <div class="snode-port-out" style="top: 108px;"></div>
              </div>

              <!-- NODE 8: USO CAFETERA -->
              <div class="studio-node-card" style="top: 175px; left: 600px; width: 195px;">
                <div class="snode-port-in" style="top: 93px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Uso Cafetera</span>
                  <span class="snode-code">PR-USO-01</span>
                </div>
                <div class="snode-sub">Fase Uso (5 a&ntilde;os)</div>
                <div class="snode-flow-bar" data-std="&bull; flujo_uso (1.0 item)" data-mass="Insumos: 8.5 kg" data-energy="Energ&iacute;a: 3,285 MJ">&bull; flujo_uso (1.0 item)</div>
                <div class="snode-inputs">
                  <span>&diams; flujo_ensamble [Ensamble]</span>
                  <span>&diams; Electricity AC: 3,285 MJ</span>
                  <span>&diams; Filter paper: 7.3 kg</span>
                  <span style="color: #94A3B8;">+ 1 insumo m&aacute;s...</span>
                </div>
                <div class="snode-port-out" style="top: 93px;"></div>
              </div>

              <!-- NODE 9: DISPOSICIÓN -->
              <div class="studio-node-card" style="top: 220px; left: 840px; width: 160px;">
                <div class="snode-port-in" style="top: 48px;"></div>
                <div class="snode-header">
                  <span class="snode-title">Disposici&oacute;n</span>
                  <span class="snode-code">PR-EOL-01</span>
                </div>
                <div class="snode-sub">Fin de Vida</div>
                <div class="snode-flow-bar" data-std="&bull; disposicion_flow (1 u)" data-mass="Masa: 2.315 kg" data-energy="Energ&iacute;a: 0.5 MJ">&bull; disposicion_flow (1 u)</div>
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

# 3. Prepare JS to insert into <script>
js_add = '''
    function highlightWire(wireClass) {
      document.querySelectorAll('.canvas-wire').forEach(w => w.classList.remove('active'));
      const activeWire = document.querySelector('.' + wireClass);
      if (activeWire) activeWire.classList.add('active');
    }

    function resetWires() {
      document.querySelectorAll('.canvas-wire').forEach(w => w.classList.remove('active'));
    }

    function setCanvasMode(mode) {
      document.querySelectorAll('.case-canvas-mode-btn').forEach(b => b.classList.remove('active'));
      if (mode === 'std') {
        document.getElementById('btnModeStd').classList.add('active');
        document.querySelectorAll('.snode-flow-bar').forEach(el => {
          if (el.dataset.std) el.innerHTML = el.dataset.std;
        });
      } else if (mode === 'mass') {
        document.getElementById('btnModeMass').classList.add('active');
        document.querySelectorAll('.snode-flow-bar').forEach(el => {
          if (el.dataset.mass) el.innerHTML = el.dataset.mass;
        });
      } else if (mode === 'energy') {
        document.getElementById('btnModeEnergy').classList.add('active');
        document.querySelectorAll('.snode-flow-bar').forEach(el => {
          if (el.dataset.energy) el.innerHTML = el.dataset.energy;
        });
      }
    }
'''

# Apply replacement to CSS
if '</style>' in html:
    html = html.replace('</style>', css_add + '\n  </style>', 1)

# Apply replacement to HTML
start_str = '<div class="case-system-arch">'
end_str = '        <p class="case-section-text">\n          La matriz de tecnolog&iacute;a'

idx_start = html.find(start_str)
idx_end = html.find(end_str)

if idx_start != -1 and idx_end != -1:
    html = html[:idx_start] + canvas_board_html + '\n\n' + html[idx_end:]
    print("Replaced case-system-arch successfully!")
else:
    print("Error finding start or end indices:", idx_start, idx_end)

# Apply replacement to Script
if '<script>' in html:
    html = html.replace('<script>', '<script>\n' + js_add, 1)

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved case_cafetera.html updated.")

