case_html = '''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Caso de Estudio: Cafetera Dom&eacute;stica &mdash; ECONODE Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #F4F3EE;
      color: #18232C;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    /* Sticky Navigation */
    .case-nav {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(244, 243, 238, 0.92);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(0, 0, 0, 0.07);
      padding: 14px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .case-nav-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .case-back-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #18232C;
      text-decoration: none;
      padding: 6px 14px;
      background: #ECE9DF;
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 999px;
      transition: all 0.2s ease;
    }

    .case-back-btn:hover {
      background: #18232C;
      color: #F4F3EE;
      transform: translateX(-2px);
    }

    .case-breadcrumbs {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #7A8691;
      letter-spacing: 0.04em;
    }

    .case-nav-action {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #18232C;
      color: #FAF9F5;
      font-size: 13px;
      font-weight: 600;
      padding: 8px 18px;
      border-radius: 999px;
      text-decoration: none;
      transition: all 0.2s ease;
    }

    .case-nav-action:hover {
      background: #0E7F5E;
      transform: translateY(-1px);
    }

    /* Main Container */
    .case-container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px 24px 120px;
    }

    /* Hero Banner */
    .case-hero {
      position: relative;
      border-radius: 24px;
      overflow: hidden;
      min-height: 480px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 48px;
      color: #FAF9F5;
      margin-bottom: 72px;
      background: #111A22;
      box-shadow: 0 20px 40px rgba(24, 35, 44, 0.12);
    }

    .case-hero-bg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
      opacity: 0.42;
      filter: saturate(0.85);
    }

    .case-hero-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, rgba(17, 26, 34, 0.92) 0%, rgba(17, 26, 34, 0.5) 60%, rgba(17, 26, 34, 0.85) 100%);
    }

    .case-hero-top {
      position: relative;
      z-index: 2;
    }

    .case-hero-tag {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.14);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.18);
      border-radius: 999px;
      padding: 6px 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #FAF9F5;
      margin-bottom: 24px;
    }

    .case-hero-tag-sym {
      color: #55D6A9;
    }

    .case-hero-title {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 58px;
      font-weight: 400;
      line-height: 1.05;
      letter-spacing: -0.02em;
      max-width: 880px;
      color: #FFFFFF;
      margin: 0;
    }

    .case-hero-bottom {
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: flex-end;
      margin-top: 40px;
    }

    .case-hero-lead {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 24px;
      font-style: italic;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.88);
      max-width: 520px;
      text-align: right;
    }

    /* Editorial Narrative Grid */
    .case-narrative-section {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 56px;
      padding: 48px 0;
      border-top: 1px solid rgba(0, 0, 0, 0.08);
    }

    .case-section-label {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #7A8691;
      padding-top: 8px;
    }

    .case-section-body {
      color: #18232C;
    }

    .case-section-headline {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 32px;
      font-weight: 400;
      line-height: 1.25;
      color: #18232C;
      margin-bottom: 20px;
      letter-spacing: -0.01em;
    }

    .case-section-text {
      font-size: 15.5px;
      line-height: 1.7;
      color: #434E58;
      margin-bottom: 24px;
    }

    /* Big Numbers Grid (The Results) */
    .case-metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin: 16px 0 32px;
    }

    .case-metric-card {
      background: #FAF6ED;
      border: 1px solid rgba(0, 0, 0, 0.07);
      border-radius: 18px;
      padding: 24px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .case-metric-value {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 46px;
      font-weight: 400;
      color: #18232C;
      line-height: 1.05;
      margin-bottom: 12px;
    }

    .case-metric-label {
      font-size: 12.5px;
      font-weight: 600;
      color: #55606B;
      line-height: 1.35;
    }

    /* Interactive Nodal Architecture Diagram */
    .case-system-arch {
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 18px;
      padding: 28px;
      margin: 28px 0;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
    }

    .case-arch-title {
      font-size: 13px;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #18232C;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .case-arch-badge {
      font-size: 11px;
      background: #E8F5E9;
      color: #0E7F5E;
      padding: 3px 10px;
      border-radius: 999px;
      font-weight: 600;
    }

    .case-arch-flow {
      display: flex;
      align-items: center;
      gap: 12px;
      overflow-x: auto;
      padding-bottom: 12px;
    }

    .case-node-box {
      background: #FAF6ED;
      border: 1px solid rgba(0, 0, 0, 0.1);
      border-radius: 12px;
      padding: 14px 16px;
      min-width: 180px;
      flex-shrink: 0;
    }

    .case-node-step {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      color: #0E7F5E;
      text-transform: uppercase;
      margin-bottom: 4px;
    }

    .case-node-name {
      font-size: 13px;
      font-weight: 700;
      color: #18232C;
      line-height: 1.25;
      margin-bottom: 4px;
    }

    .case-node-meta {
      font-size: 11px;
      color: #6C7985;
    }

    .case-flow-arrow {
      font-size: 16px;
      color: #A0ACB6;
      flex-shrink: 0;
    }

    /* Breakdown Bar Charts */
    .case-chart-card {
      background: #FAF6ED;
      border: 1px solid rgba(0, 0, 0, 0.07);
      border-radius: 18px;
      padding: 28px;
      margin: 28px 0;
    }

    .case-chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 22px;
    }

    .case-chart-heading {
      font-size: 14px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #18232C;
    }

    .case-bar-row {
      margin-bottom: 16px;
    }

    .case-bar-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      margin-bottom: 6px;
    }

    .case-bar-name {
      font-weight: 600;
      color: #18232C;
    }

    .case-bar-num {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      color: #55606B;
    }

    .case-bar-track {
      width: 100%;
      height: 10px;
      background: #E5E2D8;
      border-radius: 999px;
      overflow: hidden;
    }

    .case-bar-fill {
      height: 100%;
      border-radius: 999px;
      transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Eco-design Comparison Table */
    .case-compare-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin: 24px 0;
    }

    .case-compare-col {
      background: #FFFFFF;
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 16px;
      padding: 24px;
    }

    .case-compare-col.highlight {
      background: #F2FAF5;
      border-color: rgba(14, 127, 94, 0.3);
    }

    .case-col-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #7A8691;
      margin-bottom: 8px;
    }

    .case-compare-col.highlight .case-col-tag {
      color: #0E7F5E;
    }

    .case-col-title {
      font-size: 20px;
      font-weight: 700;
      color: #18232C;
      margin-bottom: 16px;
    }

    .case-col-stat {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 38px;
      color: #18232C;
      line-height: 1;
      margin-bottom: 14px;
    }

    .case-compare-col.highlight .case-col-stat {
      color: #0E7F5E;
    }

    .case-spec-list {
      list-style: none;
      font-size: 13px;
      color: #55606B;
    }

    .case-spec-list li {
      padding: 6px 0;
      border-top: 1px solid rgba(0, 0, 0, 0.05);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Bottom Interactive Studio CTA */
    .case-studio-cta {
      background: #18232C;
      color: #FAF9F5;
      border-radius: 22px;
      padding: 44px 48px;
      margin-top: 56px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 28px;
    }

    .case-studio-cta-title {
      font-family: 'Instrument Serif', Georgia, serif;
      font-size: 34px;
      font-weight: 400;
      line-height: 1.15;
      margin-bottom: 8px;
    }

    .case-studio-cta-desc {
      font-size: 14px;
      color: #A0ACB6;
      max-width: 600px;
      line-height: 1.5;
    }

    .case-btn-open-studio {
      background: #55D6A9;
      color: #111A22;
      font-size: 14px;
      font-weight: 700;
      padding: 14px 28px;
      border-radius: 999px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 4px 16px rgba(85, 214, 169, 0.25);
    }

    .case-btn-open-studio:hover {
      background: #FFFFFF;
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(85, 214, 169, 0.4);
    }

    /* Responsive */
    @media (max-width: 960px) {
      .case-narrative-section {
        grid-template-columns: 1fr;
        gap: 20px;
      }
      .case-metrics-grid {
        grid-template-columns: 1fr 1fr;
      }
      .case-compare-grid {
        grid-template-columns: 1fr;
      }
      .case-hero {
        padding: 28px;
      }
      .case-hero-title {
        font-size: 40px;
      }
      .case-hero-lead {
        text-align: left;
        font-size: 20px;
      }
    }
  </style>
</head>
<body>

  <!-- Sticky Top Bar -->
  <header class="case-nav">
    <div class="case-nav-left">
      <a href="index.html#homeCases" class="case-back-btn">&larr; Volver al inicio</a>
      <span class="case-breadcrumbs">CASOS DE ESTUDIO / MANUFACTURA &amp; CONSUMO</span>
    </div>
    <div>
      <a href="index.html#viewStudio" class="case-nav-action" onclick="loadAndOpenStudio(event)">
        Abrir en Studio &rarr;
      </a>
    </div>
  </header>

  <main class="case-container">

    <!-- Hero Banner -->
    <section class="case-hero">
      <img src="images/candidates/slate/cand_01_slate.jpg" alt="Manufactura de Cafetera Dom&eacute;stica" class="case-hero-bg">
      <div class="case-hero-overlay"></div>

      <div class="case-hero-top">
        <div class="case-hero-tag">
          <span class="case-hero-tag-sym">&bull;</span> CASO DE ESTUDIO &middot; ACV DE PRODUCTO
        </div>
        <h1 class="case-hero-title">
          Cafetera Dom&eacute;stica: An&aacute;lisis de Ciclo de Vida Cradle-to-Grave
        </h1>
      </div>

      <div class="case-hero-bottom">
        <p class="case-hero-lead">
          10 procesos unitarios, 1,200 ciclos de uso y balance Leontief sobre 26,533 procesos de ecoinvent 3.12 conforme a ISO 14044.
        </p>
      </div>
    </section>

    <!-- Section 1: The Challenge -->
    <article class="case-narrative-section">
      <div class="case-section-label">THE CHALLENGE</div>
      <div class="case-section-body">
        <h2 class="case-section-headline">
          La opacidad de ensambles multi-material en cadenas de suministro dispersas.
        </h2>
        <p class="case-section-text">
          Modelar el impacto de un electrodom&eacute;stico de consumo convencional suele fracasar por la fragmentaci&oacute;n de datos: termopl&aacute;sticos inyectados de proveedores petroqu&iacute;micos, perfiles de aluminio extruido, jarras de borosilicato, cableado de cobre con aislante de PVC y electr&oacute;nica interna operando con factores de emisi&oacute;n desactualizados en hojas de c&aacute;lculo manuales.
        </p>
        <p class="case-section-text">
          El fabricante requería una declaraci&oacute;n ambiental auditable conforme a NOM-070-SE-2024 e ISO 14044 para certificar su huella de carbono unitaria, identificar con precisi&oacute;n cient&iacute;fica los puntos cr&iacute;ticos (hotspots) y evaluar escenarios de eco-dise&ntilde;o con materiales reciclados antes de ordenar moldes industriales de inyecci&oacute;n.
        </p>
      </div>
    </article>

    <!-- Section 2: What We Built (System Architecture) -->
    <article class="case-narrative-section">
      <div class="case-section-label">WHAT WE BUILT</div>
      <div class="case-section-body">
        <h2 class="case-section-headline">
          Topolog&iacute;a nodal completa de 10 procesos unitarios con resoluci&oacute;n Leontief.
        </h2>
        <p class="case-section-text">
          En ECONODE Studio se estructur&oacute; el sistema producto completo dividiendo el ciclo de vida en 5 etapas secuenciales: adquisici&oacute;n de resina virgen, manufactura de 6 componentes individuales, ensamble integral del electrodom&eacute;stico (1000W), transporte intermodal (400 km por cami&oacute;n) y fase de uso modelada a 5 a&ntilde;os (1,200 ciclos de preparaci&oacute;n de caf&eacute;).
        </p>

        <!-- Visual Nodal Flow Diagram -->
        <div class="case-system-arch">
          <div class="case-arch-title">
            <span>Arquitectura Nodal del Sistema de Producto</span>
            <span class="case-arch-badge">10 Nodos Conectados</span>
          </div>
          <div class="case-arch-flow">
            <div class="case-node-box">
              <div class="case-node-step">Etapa 1</div>
              <div class="case-node-name">PP Virgen</div>
              <div class="case-node-meta">0.94 kg resina base</div>
            </div>
            <div class="case-flow-arrow">&rarr;</div>
            <div class="case-node-box">
              <div class="case-node-step">Etapa 2</div>
              <div class="case-node-name">Cuerpo Inyectado</div>
              <div class="case-node-meta">Moldeo por inyecci&oacute;n</div>
            </div>
            <div class="case-flow-arrow">&rarr;</div>
            <div class="case-node-box">
              <div class="case-node-step">Etapa 2</div>
              <div class="case-node-name">5 Componentes</div>
              <div class="case-node-meta">Jarra, Al, Cable, Placa</div>
            </div>
            <div class="case-flow-arrow">&rarr;</div>
            <div class="case-node-box">
              <div class="case-node-step">Etapa 3</div>
              <div class="case-node-name">Ensamble Cafetera</div>
              <div class="case-node-meta">Unidad 1000W completa</div>
            </div>
            <div class="case-flow-arrow">&rarr;</div>
            <div class="case-node-box">
              <div class="case-node-step">Etapa 4</div>
              <div class="case-node-name">Distribuci&oacute;n</div>
              <div class="case-node-meta">400 km flete log&iacute;stico</div>
            </div>
            <div class="case-flow-arrow">&rarr;</div>
            <div class="case-node-box" style="border-color: #0E7F5E; background: #F2FAF5;">
              <div class="case-node-step" style="color: #0E7F5E;">Etapa 5 (Referencia)</div>
              <div class="case-node-name">Fase de Uso</div>
              <div class="case-node-meta">5 a&ntilde;os &middot; 1,200 tazas</div>
            </div>
          </div>
        </div>

        <p class="case-section-text">
          La matriz de tecnolog&iacute;a $A$ de $10 \\times 10$ se vincul&oacute; autom&aacute;ticamente a los procesos de fondo de ecoinvent 3.12 Cut-off para caracterizar los intercambios elementales de biosfera, resolviendo el vector de escalamiento de demanda final $s = (I - A)^{-1} f$ en menos de 12 milisegundos en el navegador.
        </p>
      </div>
    </article>

    <!-- Section 3: The Outcome & Graphs -->
    <article class="case-narrative-section">
      <div class="case-section-label">THE OUTCOME</div>
      <div class="case-section-body">
        <h2 class="case-section-headline">
          Identificaci&oacute;n del hotspot en uso y reducci&oacute;n del 24.3% con eco-dise&ntilde;o.
        </h2>
        <p class="case-section-text">
          El c&aacute;lculo revel&oacute; que el <strong>68.1%</strong> del impacto de calentamiento global no ocurre en la f&aacute;brica sino en la cocina del consumidor durante el calentamiento del agua. Como respuesta, el equipo de ingenier&iacute;a simul&oacute; un escenario optimizado en ECONODE Studio sustituyendo el 30% del polipropileno virgen por rPP reciclado y programando apagado autom&aacute;tico a los 15 minutos, reduciendo la huella de <strong>84.2 kg a 63.7 kg CO2 eq</strong>.
        </p>

        <!-- Impact Breakdown Bar Chart -->
        <div class="case-chart-card">
          <div class="case-chart-header">
            <span class="case-chart-heading">Huella de Carbono por Etapa de Ciclo de Vida (84.2 kg CO2 eq Total)</span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #7A8691;">IPCC 2021 GWP100</span>
          </div>

          <div class="case-bar-row">
            <div class="case-bar-meta">
              <span class="case-bar-name">Fase de Uso (1,200 ciclos &middot; Electricidad 1000W)</span>
              <span class="case-bar-num">57.34 kg CO2 eq &middot; 68.1%</span>
            </div>
            <div class="case-bar-track">
              <div class="case-bar-fill" style="width: 68.1%; background: #E06D53;"></div>
            </div>
          </div>

          <div class="case-bar-row">
            <div class="case-bar-meta">
              <span class="case-bar-name">Pol&iacute;meros &amp; Moldeo (PP virgen 0.94 kg)</span>
              <span class="case-bar-num">18.52 kg CO2 eq &middot; 22.0%</span>
            </div>
            <div class="case-bar-track">
              <div class="case-bar-fill" style="width: 22.0%; background: #4B6B82;"></div>
            </div>
          </div>

          <div class="case-bar-row">
            <div class="case-bar-meta">
              <span class="case-bar-name">Componentes Met&aacute;licos &amp; Jarra Vidrio (Al, Cu, Acero, Vidrio)</span>
              <span class="case-bar-num">5.14 kg CO2 eq &middot; 6.1%</span>
            </div>
            <div class="case-bar-track">
              <div class="case-bar-fill" style="width: 6.1%; background: #7C93A4;"></div>
            </div>
          </div>

          <div class="case-bar-row">
            <div class="case-bar-meta">
              <span class="case-bar-name">Transporte &amp; Distribuci&oacute;n (400 km cami&oacute;n)</span>
              <span class="case-bar-num">2.11 kg CO2 eq &middot; 2.5%</span>
            </div>
            <div class="case-bar-track">
              <div class="case-bar-fill" style="width: 2.5%; background: #A7B6C2;"></div>
            </div>
          </div>

          <div class="case-bar-row" style="margin-bottom: 0;">
            <div class="case-bar-meta">
              <span class="case-bar-name">Empaque de Cart&oacute;n &amp; Manual de Usuario</span>
              <span class="case-bar-num">1.09 kg CO2 eq &middot; 1.3%</span>
            </div>
            <div class="case-bar-track">
              <div class="case-bar-fill" style="width: 1.3%; background: #CAD3DA;"></div>
            </div>
          </div>
        </div>

        <!-- Comparative Eco-design Columns -->
        <div class="case-compare-grid">
          <div class="case-compare-col">
            <div class="case-col-tag">Dise&ntilde;o Convencional (L&iacute;nea Base)</div>
            <div class="case-col-title">Cafetera Est&aacute;ndar 1000W</div>
            <div class="case-col-stat">84.2 kg <span style="font-size: 16px; font-family: 'Plus Jakarta Sans', sans-serif; color: #7A8691;">CO2 eq</span></div>
            <ul class="case-spec-list">
              <li>&bull; 100% Polipropileno virgen f&oacute;sil (0.94 kg)</li>
              <li>&bull; Placa calefactora encendida continuo (40 min)</li>
              <li>&bull; Empaque no optimizado de 350g</li>
              <li>&bull; Sin trazabilidad forense digital</li>
            </ul>
          </div>

          <div class="case-compare-col highlight">
            <div class="case-col-tag">&radic; Eco-dise&ntilde;o Simulado en ECONODE</div>
            <div class="case-col-title">Cafetera Optimizada con rPP</div>
            <div class="case-col-stat">63.7 kg <span style="font-size: 16px; font-family: 'Plus Jakarta Sans', sans-serif; color: #0E7F5E;">CO2 eq (-24.3%)</span></div>
            <ul class="case-spec-list">
              <li>&bull; 30% Polipropileno reciclado post-consumo (rPP)</li>
              <li>&bull; Auto-apagado inteligente a los 15 minutos</li>
              <li>&bull; Reducci&oacute;n de 20.5 kg CO2 eq por aparato</li>
              <li>&bull; Certificado NOM-070 con firma HMAC-SHA256</li>
            </ul>
          </div>
        </div>

      </div>
    </article>

    <!-- Section 4: The Results -->
    <article class="case-narrative-section">
      <div class="case-section-label">THE RESULTS</div>
      <div class="case-section-body">
        <div class="case-metrics-grid">
          <div class="case-metric-card">
            <div class="case-metric-value">84.2 kg</div>
            <div class="case-metric-label">CO2 eq por unidad (Cradle-to-Grave)</div>
          </div>
          <div class="case-metric-card">
            <div class="case-metric-value">68.1 %</div>
            <div class="case-metric-label">Concentrado en calentamiento de agua</div>
          </div>
          <div class="case-metric-card" style="background: #F2FAF5; border-color: rgba(14, 127, 94, 0.2);">
            <div class="case-metric-value" style="color: #0E7F5E;">-24.3 %</div>
            <div class="case-metric-label" style="color: #0E7F5E;">Ahorro neto con Eco-dise&ntilde;o</div>
          </div>
          <div class="case-metric-card">
            <div class="case-metric-value">18 / 18</div>
            <div class="case-metric-label">Cl&aacute;usulas auditadas ISO 14044 / NOM-070</div>
          </div>
        </div>
      </div>
    </article>

    <!-- Section 5: Interactive Studio CTA Card -->
    <div class="case-studio-cta">
      <div>
        <h3 class="case-studio-cta-title">Explora este sistema producto en tiempo real</h3>
        <p class="case-studio-cta-desc">
          Abre el modelo interactivo de la cafetera directamente en el lienzo nodal de ECONODE Studio. Puedes inspeccionar las entradas y salidas de los 10 procesos, recalcular el balance Leontief y simular tus propios escenarios de eco-dise&ntilde;o.
        </p>
      </div>
      <div>
        <a href="index.html#viewStudio" class="case-btn-open-studio" onclick="loadAndOpenStudio(event)">
          Cargar en ECONODE Studio &rarr;
        </a>
      </div>
    </div>

  </main>

  <script>
    function loadAndOpenStudio(e) {
      if (e) e.preventDefault();
      // Store flag in sessionStorage so index.html knows to load the cafetera system upon opening
      sessionStorage.setItem('econode_autoload_case', 'cafetera');
      window.location.href = 'index.html#viewStudio';
    }
  </script>
</body>
</html>
'''

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(case_html)
print('case_cafetera.html created successfully!')

