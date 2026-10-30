import re

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update CSS
css_new = '''
    /* =============================================================
       STUDIO CANVAS REPLICA IN CASE STUDY (Spacious & Sankey Lines)
       ============================================================= */
    .case-canvas-board {
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.1);
      border-radius: 20px;
      overflow: hidden;
      margin: 36px 0 40px -190px;
      width: calc(100% + 190px);
      max-width: 1040px;
      box-shadow: 0 10px 36px rgba(0, 0, 0, 0.05);
      transition: all 0.3s ease;
    }

    @media (max-width: 1080px) {
      .case-canvas-board {
        margin-left: 0;
        width: 100%;
      }
    }

    .case-canvas-bar {
      background: #FAF6ED;
      border-bottom: 1px solid rgba(0, 0, 0, 0.08);
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .case-canvas-bar-left {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .case-canvas-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #0E7F5E;
      display: inline-block;
      box-shadow: 0 0 0 3px rgba(14, 127, 94, 0.2);
    }

    .case-canvas-title {
      font-size: 13.5px;
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
      padding: 3px;
      border-radius: 8px;
      gap: 3px;
      margin-left: 8px;
    }

    .case-canvas-mode-btn {
      border: none;
      background: transparent;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      color: #55606B;
      padding: 4px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .case-canvas-mode-btn:hover {
      color: #18232C;
    }

    .case-canvas-mode-btn.active {
      background: #FFFFFF;
      color: #18232C;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
    }

    .case-canvas-bar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .case-canvas-balance-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: #0E7F5E;
      background: #E8F5E9;
      padding: 5px 12px;
      border-radius: 999px;
      border: 1px solid rgba(14, 127, 94, 0.25);
      transition: all 0.25s ease;
    }

    .case-canvas-mode-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      color: #7A8691;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .case-canvas-stage-wrap {
      position: relative;
      width: 100%;
      height: 680px;
      background: #FDFCFA;
      background-image: radial-gradient(rgba(24, 35, 44, 0.08) 1.2px, transparent 1.2px);
      background-size: 20px 20px;
      overflow-x: auto;
      overflow-y: hidden;
      scrollbar-width: thin;
      scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
    }

    .case-canvas-svg {
      position: absolute;
      top: 0;
      left: 0;
      width: 1260px;
      height: 680px;
      pointer-events: none;
      z-index: 1;
    }

    .canvas-wire {
      fill: none;
      stroke: #818CF8;
      stroke-width: 3px;
      stroke-linecap: round;
      opacity: 0.7;
      transition: stroke-width 0.4s cubic-bezier(0.16, 1, 0.3, 1),
                  stroke 0.4s ease,
                  opacity 0.4s ease,
                  filter 0.3s ease;
    }

    .canvas-wire.wire-ensamble-uso,
    .canvas-wire.wire-uso-eol {
      stroke: #0E7F5E;
      stroke-width: 3.5px;
      opacity: 0.9;
    }

    .canvas-wire.active {
      stroke: #0E7F5E !important;
      stroke-width: 5px !important;
      opacity: 1 !important;
      filter: drop-shadow(0 2px 8px rgba(14, 127, 94, 0.6)) !important;
    }

    .canvas-inlet-dot {
      fill: #818CF8;
      transition: fill 0.3s ease, r 0.3s ease;
    }

    /* SANKEY MASA (Mass Flow Ribbons) */
    .sankey-mode-mass #wire-cuerpo {
      stroke: #059669;
      stroke-width: 16px;
      opacity: 0.85;
    }
    .sankey-mode-mass #wire-jarra {
      stroke: #059669;
      stroke-width: 11px;
      opacity: 0.85;
    }
    .sankey-mode-mass #wire-cable {
      stroke: #059669;
      stroke-width: 4px;
      opacity: 0.85;
    }
    .sankey-mode-mass #wire-partes {
      stroke: #059669;
      stroke-width: 4.5px;
      opacity: 0.85;
    }
    .sankey-mode-mass #wire-empaque {
      stroke: #059669;
      stroke-width: 7px;
      opacity: 0.85;
    }
    .sankey-mode-mass #wire-transporte {
      stroke: #059669;
      stroke-width: 6px;
      opacity: 0.85;
    }
    .sankey-mode-mass #wire-ensamble-uso {
      stroke: #059669;
      stroke-width: 28px;
      opacity: 0.9;
      filter: drop-shadow(0 3px 10px rgba(5, 150, 105, 0.25));
    }
    .sankey-mode-mass #wire-uso-eol {
      stroke: #059669;
      stroke-width: 28px;
      opacity: 0.9;
      filter: drop-shadow(0 3px 10px rgba(5, 150, 105, 0.25));
    }
    .sankey-mode-mass .canvas-inlet-dot {
      fill: #059669;
      r: 4.5;
    }

    /* SANKEY ENERGIA (Cumulative Energy Ribbons) */
    .sankey-mode-energy #wire-cuerpo {
      stroke: #0284C7;
      stroke-width: 7px;
      opacity: 0.88;
    }
    .sankey-mode-energy #wire-jarra {
      stroke: #0284C7;
      stroke-width: 5px;
      opacity: 0.88;
    }
    .sankey-mode-energy #wire-cable {
      stroke: #0284C7;
      stroke-width: 3px;
      opacity: 0.88;
    }
    .sankey-mode-energy #wire-partes {
      stroke: #0284C7;
      stroke-width: 4px;
      opacity: 0.88;
    }
    .sankey-mode-energy #wire-empaque {
      stroke: #0284C7;
      stroke-width: 2.5px;
      opacity: 0.88;
    }
    .sankey-mode-energy #wire-transporte {
      stroke: #0284C7;
      stroke-width: 8px;
      opacity: 0.88;
    }
    .sankey-mode-energy #wire-ensamble-uso {
      stroke: #0284C7;
      stroke-width: 14px;
      opacity: 0.92;
    }
    .sankey-mode-energy #wire-uso-eol {
      stroke: #0284C7;
      stroke-width: 3px;
      opacity: 0.8;
    }
    .sankey-mode-energy .canvas-inlet-dot {
      fill: #0284C7;
      r: 4;
    }

    .sankey-mode-energy #cardNodeUso {
      border: 2px solid #0284C7 !important;
      box-shadow: 0 0 24px rgba(2, 132, 199, 0.25) !important;
    }

    /* SVG Sankey Tag Rect & Text */
    .sankey-tag-rect {
      fill: #FFFFFF;
      stroke: #059669;
      stroke-width: 1.5px;
      filter: drop-shadow(0 2px 5px rgba(0,0,0,0.08));
      transition: all 0.3s ease;
    }
    .sankey-mode-energy .sankey-tag-rect {
      stroke: #0284C7;
    }
    .sankey-tag-rect.highlight {
      fill: #0E7F5E;
      stroke: #0E7F5E;
    }
    .sankey-mode-energy .sankey-tag-rect.highlight {
      fill: #0284C7;
      stroke: #0284C7;
    }
    .sankey-tag-text {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      fill: #0E7F5E;
      transition: fill 0.3s ease;
    }
    .sankey-mode-energy .sankey-tag-text {
      fill: #0284C7;
    }
    .sankey-tag-text.highlight {
      fill: #FFFFFF;
    }

    .case-canvas-nodes-layer {
      position: absolute;
      top: 0;
      left: 0;
      width: 1260px;
      height: 680px;
      z-index: 2;
    }

    /* Process Node Card in Canvas - Generous & Polished */
    .studio-node-card {
      position: absolute;
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.12);
      border-radius: 12px;
      padding: 11px 13px;
      box-shadow: 0 4px 14px rgba(24, 35, 44, 0.05);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
    }

    .studio-node-card:hover {
      transform: translateY(-2px);
      border-color: #0E7F5E;
      box-shadow: 0 10px 28px rgba(14, 127, 94, 0.15);
    }

    .studio-node-card.highlight-node {
      border: 2px solid #0E7F5E;
      box-shadow: 0 6px 22px rgba(14, 127, 94, 0.18);
    }

    .snode-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 3px;
    }

    .snode-title {
      font-size: 12.5px;
      font-weight: 700;
      color: #18232C;
    }

    .snode-code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 9.5px;
      font-weight: 600;
      background: #ECE9DF;
      color: #55606B;
      padding: 1.5px 7px;
      border-radius: 4px;
    }

    .snode-sub {
      font-size: 10.5px;
      color: #7A8691;
      margin-bottom: 6px;
    }

    .snode-flow-bar {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      font-weight: 600;
      background: #EBF7EE;
      color: #0E7F5E;
      border: 1px solid rgba(14, 127, 94, 0.25);
      border-radius: 5px;
      padding: 3px 8px;
      margin-bottom: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      transition: all 0.2s ease;
    }

    .snode-inputs {
      font-size: 9.5px;
      color: #55606B;
      display: flex;
      flex-direction: column;
      gap: 3px;
      line-height: 1.4;
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
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2.5px solid #0E7F5E;
      box-shadow: 0 1px 4px rgba(0,0,0,0.18);
    }

    .snode-port-in {
      position: absolute;
      left: -6px;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2.5px solid #2563EB;
      box-shadow: 0 1px 4px rgba(0,0,0,0.18);
    }

    .case-canvas-footer {
      background: #FAF6ED;
      border-top: 1px solid rgba(0, 0, 0, 0.08);
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .case-canvas-legend-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .case-canvas-legend-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #0E7F5E;
      display: inline-block;
      transition: background 0.3s ease;
    }

    .case-canvas-legend-txt {
      font-size: 12.5px;
      color: #55606B;
    }

    .case-canvas-open-link {
      font-size: 13px;
      font-weight: 600;
      color: #0E7F5E;
      text-decoration: none;
      transition: transform 0.2s ease;
    }

    .case-canvas-open-link:hover {
      text-decoration: underline;
      transform: translateX(3px);
    }
'''

# 2. Update JS
js_new = '''
    function highlightWire(wireClass) {
      document.querySelectorAll('.canvas-wire').forEach(w => w.classList.remove('active'));
      const activeWire = document.querySelector('.' + wireClass);
      if (activeWire) activeWire.classList.add('active');
    }

    function resetWires() {
      document.querySelectorAll('.canvas-wire').forEach(w => w.classList.remove('active'));
    }

    function setCanvasMode(mode) {
      const board = document.querySelector('.case-canvas-board');
      const tagGroup = document.getElementById('sankeyTagGroup');
      const legendDot = document.getElementById('canvasLegendDot');
      const legendText = document.getElementById('canvasLegendText');
      const balanceBadge = document.getElementById('canvasBalanceBadge');
      const modeTag = document.getElementById('canvasModeTag');

      if (!board) return;

      board.classList.remove('sankey-mode-mass', 'sankey-mode-energy');
      document.querySelectorAll('.case-canvas-mode-btn').forEach(b => b.classList.remove('active'));

      if (mode === 'std') {
        document.getElementById('btnModeStd').classList.add('active');
        if (tagGroup) tagGroup.style.opacity = '0';
        if (balanceBadge) {
          balanceBadge.innerHTML = '&radic; Balance de Masa: 100% OK';
          balanceBadge.style.color = '#0E7F5E';
          balanceBadge.style.background = '#E8F5E9';
        }
        if (modeTag) modeTag.textContent = 'Modo Ingenier\u00eda de Procesos';
        if (legendDot) legendDot.style.background = '#0E7F5E';
        if (legendText) {
          legendText.innerHTML = 'Modo Est&aacute;ndar: Topolog&iacute;a de 10 procesos unitarios con l&iacute;neas de conexi&oacute;n de flujos de producto hacia ensamble central.';
        }
        document.querySelectorAll('.snode-flow-bar').forEach(el => {
          if (el.dataset.std) el.innerHTML = el.dataset.std;
        });
      } else if (mode === 'mass') {
        document.getElementById('btnModeMass').classList.add('active');
        board.classList.add('sankey-mode-mass');
        if (tagGroup) tagGroup.style.opacity = '1';
        if (balanceBadge) {
          balanceBadge.innerHTML = '&radic; Masa Entrante = Saliente (2.315 kg)';
          balanceBadge.style.color = '#059669';
          balanceBadge.style.background = '#ECFDF5';
        }
        if (modeTag) modeTag.textContent = 'Sankey de Masa F\u00edsica';
        if (legendDot) legendDot.style.background = '#059669';
        if (legendText) {
          legendText.innerHTML = '<strong>Sankey de Masa</strong>: El grosor de cada l&iacute;nea de flujo es proporcional a la masa f&iacute;sica (kg) que alimenta al ensamble (total 2.315 kg).';
        }

        const tagCuerpo = document.getElementById('tagValCuerpo');
        const tagJarra = document.getElementById('tagValJarra');
        const tagCable = document.getElementById('tagValCable');
        const tagPartes = document.getElementById('tagValPartes');
        const tagEmpaque = document.getElementById('tagValEmpaque');
        const tagTransporte = document.getElementById('tagValTransporte');
        const tagEnsamble = document.getElementById('tagValEnsamble');
        const tagEol = document.getElementById('tagValEol');

        if (tagCuerpo) tagCuerpo.textContent = '1.040 kg';
        if (tagJarra) tagJarra.textContent = '0.600 kg';
        if (tagCable) tagCable.textContent = '0.165 kg';
        if (tagPartes) tagPartes.textContent = '0.170 kg';
        if (tagEmpaque) tagEmpaque.textContent = '0.340 kg';
        if (tagTransporte) tagTransporte.textContent = '0.35 t*km';
        if (tagEnsamble) tagEnsamble.textContent = '2.315 kg';
        if (tagEol) tagEol.textContent = '2.315 kg';

        document.querySelectorAll('.snode-flow-bar').forEach(el => {
          if (el.dataset.mass) el.innerHTML = el.dataset.mass;
        });
      } else if (mode === 'energy') {
        document.getElementById('btnModeEnergy').classList.add('active');
        board.classList.add('sankey-mode-energy');
        if (tagGroup) tagGroup.style.opacity = '1';
        if (balanceBadge) {
          balanceBadge.innerHTML = '&#9889; Hotspot: 3,285 MJ (Fase de Uso)';
          balanceBadge.style.color = '#0284C7';
          balanceBadge.style.background = '#F0F9FF';
        }
        if (modeTag) modeTag.textContent = 'Sankey de Energ\u00eda Primaria';
        if (legendDot) legendDot.style.background = '#0284C7';
        if (legendText) {
          legendText.innerHTML = '<strong>Sankey de Energ&iacute;a</strong>: El grosor representa la energ&iacute;a acumulada (MJ). La fase de uso domina con el 98.6% del consumo total del ciclo de vida.';
        }

        const tagCuerpo = document.getElementById('tagValCuerpo');
        const tagJarra = document.getElementById('tagValJarra');
        const tagCable = document.getElementById('tagValCable');
        const tagPartes = document.getElementById('tagValPartes');
        const tagEmpaque = document.getElementById('tagValEmpaque');
        const tagTransporte = document.getElementById('tagValTransporte');
        const tagEnsamble = document.getElementById('tagValEnsamble');
        const tagEol = document.getElementById('tagValEol');

        if (tagCuerpo) tagCuerpo.textContent = '12.4 MJ';
        if (tagJarra) tagJarra.textContent = '8.2 MJ';
        if (tagCable) tagCable.textContent = '3.1 MJ';
        if (tagPartes) tagPartes.textContent = '4.8 MJ';
        if (tagEmpaque) tagEmpaque.textContent = '1.9 MJ';
        if (tagTransporte) tagTransporte.textContent = '14.5 MJ';
        if (tagEnsamble) tagEnsamble.textContent = '44.9 MJ';
        if (tagEol) tagEol.textContent = '0.5 MJ';

        document.querySelectorAll('.snode-flow-bar').forEach(el => {
          if (el.dataset.energy) el.innerHTML = el.dataset.energy;
        });
      }
    }
'''

# Import canvas_board_html
from new_canvas_html import canvas_board_html

# Replace CSS block
css_start = html.find('/* =============================================================\n       STUDIO CANVAS REPLICA IN CASE STUDY')
css_end = html.find('</style>')
if css_start != -1 and css_end != -1:
    html = html[:css_start] + css_new.strip() + '\n  ' + html[css_end:]
    print("Replaced CSS successfully!")
else:
    print("Could not find CSS start, css_start:", css_start)

# Replace HTML block
board_pattern = r'<div class="case-canvas-board">.*?<!-- Bottom Canvas Footer -->\s*<div class="case-canvas-footer">.*?</div>\s*</div>'
match = re.search(board_pattern, html, re.DOTALL)
if match:
    html = html[:match.start()] + canvas_board_html.strip() + html[match.end():]
    print("Replaced Canvas Board HTML successfully!")
else:
    print("Could not find case-canvas-board match with regex")

# Replace JS block
js_start = html.find('function highlightWire(wireClass)')
js_end = html.find('function loadAndOpenStudio(e)')
if js_start != -1 and js_end != -1:
    html = html[:js_start] + js_new.strip() + '\n\n    ' + html[js_end:]
    print("Replaced JS successfully!")
else:
    print("Could not find JS start or end, js_start:", js_start, "js_end:", js_end)

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated case_cafetera.html with spacious Sankey board!")

