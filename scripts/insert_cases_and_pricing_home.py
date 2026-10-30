with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Hero floating case study link
old_floating_link = 'href="#homeCapabilities" target="_blank" class="palladio-case-card-link" id="btnOpenCaseStudy"'
new_floating_link = 'href="case_cafetera.html" class="palladio-case-card-link" id="btnOpenCaseStudy"'
html = html.replace(old_floating_link, new_floating_link)

# 2. Update Hero "Ver Planes y Casos" button
old_btn_pricing = '<button class="palladio-btn-pricing" id="btnHomeViewExamples" data-alias="heroBtnEjemplosNOM" name="heroBtnEjemplosNOM">'
new_btn_pricing = '<button class="palladio-btn-pricing" id="btnHomeViewExamples" data-alias="heroBtnEjemplosNOM" name="heroBtnEjemplosNOM" onclick="document.getElementById(\'homeCases\').scrollIntoView({behavior:\'smooth\'})">'
html = html.replace(old_btn_pricing, new_btn_pricing)

# 3. Update Navbar Links
old_nav_block = '''    <!-- Navigation Links (Visible in Landing Mode) -->
    <nav class="nav-links" id="landingNavLinks">
      <a href="#homeArchitecture" class="landing-nav-link" id="lnkWhyUs" data-i18n="home.nav_why">Por qu&eacute; ECONODE</a>
      <a href="#homeFaq" class="landing-nav-link" id="lnkFaq" data-i18n="home.nav_faq">Pilares T&eacute;cnicos</a>
      <a href="#homeProfiles" class="landing-nav-link" id="lnkProfiles" data-i18n="home.nav_profiles">Perfiles de Usuario</a>
    </nav>'''

new_nav_block = '''    <!-- Navigation Links (Visible in Landing Mode) -->
    <nav class="nav-links" id="landingNavLinks">
      <a href="#homeArchitecture" class="landing-nav-link" id="lnkWhyUs" data-i18n="home.nav_why">Por qu&eacute; ECONODE</a>
      <a href="#homeFaq" class="landing-nav-link" id="lnkFaq" data-i18n="home.nav_faq">Pilares T&eacute;cnicos</a>
      <a href="#homeProfiles" class="landing-nav-link" id="lnkProfiles" data-i18n="home.nav_profiles">Perfiles</a>
      <a href="#homeCases" class="landing-nav-link" id="lnkCases" data-i18n="home.nav_cases">Casos</a>
      <a href="#homePricing" class="landing-nav-link" id="lnkPricing" data-i18n="home.nav_pricing">Planes</a>
    </nav>'''

html = html.replace(old_nav_block, new_nav_block)

# 4. Insert Sections #homeCases and #homePricing before final CTA
target_cta = '    <!-- BOTTOM HIGH-IMPACT CTA BANNER -->'

cases_and_pricing_html = '''    <!-- PALLADIO CASOS DE ESTUDIO (#homeCases) -->
    <section class="palladio-cases-wrapper" id="homeCases">
      <div class="palladio-cases-container">
        <!-- Header -->
        <div class="palladio-cases-header">
          <div>
            <div class="palladio-cases-tag">
              <span class="tag-dot">+</span> CASOS DE ESTUDIO &middot; RIGOR APLICADO
            </div>
            <h2 class="palladio-cases-title">Ingenier&iacute;a probada en casos reales</h2>
          </div>
          <div>
            <p class="palladio-cases-lead">
              Modelos de ciclo de vida completos, balances de masa multi-escala y escenarios de eco-dise&ntilde;o documentados con trazabilidad forense bajo ISO 14044.
            </p>
          </div>
        </div>

        <!-- Featured Case Hero Card: Cafetera Domestica -->
        <div class="palladio-featured-case-card">
          <div class="palladio-featured-case-content">
            <div class="palladio-case-badge-row">
              <span class="palladio-case-pill-dark">Caso Insignia</span>
              <span class="palladio-case-pill-green">-24.3% CO2 eq Validado</span>
            </div>
            <h3 class="palladio-featured-case-title">
              Cafetera Dom&eacute;stica: Descarbonizaci&oacute;n Cradle-to-Grave
            </h3>
            <p class="palladio-featured-case-desc">
              Modelado integral de 10 procesos unitarios con resoluci&oacute;n matricial Leontief sobre 26,533 procesos de ecoinvent 3.12. Descubrimiento del punto cr&iacute;tico en la fase de uso y simulaci&oacute;n de eco-dise&ntilde;o con 30% de polipropileno reciclado (rPP).
            </p>
            <div class="palladio-featured-stats-row">
              <div class="palladio-feat-stat">
                <span class="stat-num">84.2 kg</span>
                <span class="stat-lbl">CO2 eq unitario</span>
              </div>
              <div class="palladio-feat-stat">
                <span class="stat-num">10</span>
                <span class="stat-lbl">Procesos nodales</span>
              </div>
              <div class="palladio-feat-stat">
                <span class="stat-num">1,200</span>
                <span class="stat-lbl">Ciclos de infusi&oacute;n</span>
              </div>
              <div class="palladio-feat-stat">
                <span class="stat-num">18 / 18</span>
                <span class="stat-lbl">Cl&aacute;usulas ISO 14044</span>
              </div>
            </div>
            <div class="palladio-featured-action-row">
              <a href="case_cafetera.html" class="palladio-btn-case-cta">
                <span>Ver Caso de Estudio Completo</span>
                <span class="btn-arrow">&rarr;</span>
              </a>
              <span class="palladio-case-hint">Incluye &aacute;rbol de ensamble y gr&aacute;ficas de impacto interactivas</span>
            </div>
          </div>
          <div class="palladio-featured-case-media">
            <img src="images/candidates/slate/cand_01_slate.jpg" alt="Manufactura de Cafetera" class="palladio-featured-case-img">
          </div>
        </div>

        <!-- 2 Secondary Cases -->
        <div class="palladio-secondary-cases-grid">
          <div class="palladio-sec-case-card">
            <div class="palladio-sec-case-thumb-wrap">
              <img src="images/candidates/slate/cand_07_slate.jpg" alt="Botella PET" class="palladio-sec-case-thumb">
              <span class="palladio-sec-case-badge">Pol&iacute;meros Circulares</span>
            </div>
            <div class="palladio-sec-case-body">
              <h4 class="palladio-sec-case-title">Cadena de Reciclaje y Soplado de Botella PET</h4>
              <p class="palladio-sec-case-desc">
                Comparativa de pellets de PET virgen frente a resina rPET grado alimenticio con balance estequiom&eacute;trico de extrusi&oacute;n y preformas.
              </p>
              <div class="palladio-sec-case-footer">
                <span class="case-metric-highlight">0.042 kg CO2 / unidad</span>
                <a href="case_cafetera.html" class="palladio-circle-arrow-btn">&rarr;</a>
              </div>
            </div>
          </div>

          <div class="palladio-sec-case-card">
            <div class="palladio-sec-case-thumb-wrap">
              <img src="images/candidates/slate/cand_02_slate.jpg" alt="Red El&eacute;ctrica" class="palladio-sec-case-thumb">
              <span class="palladio-sec-case-badge">Infraestructura &amp; Red</span>
            </div>
            <div class="palladio-sec-case-body">
              <h4 class="palladio-sec-case-title">Red de Transmisi&oacute;n El&eacute;ctrica de Alta Tensi&oacute;n</h4>
              <p class="palladio-sec-case-desc">
                C&aacute;lculo de factores de emisi&oacute;n horario de la matriz el&eacute;ctrica nacional (CFE/CENACE) para modelado din&aacute;mico de Alcance 2.
              </p>
              <div class="palladio-sec-case-footer">
                <span class="case-metric-highlight">0.450 kg CO2 / kWh</span>
                <a href="case_cafetera.html" class="palladio-circle-arrow-btn">&rarr;</a>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- PALLADIO PLANES Y PRECIOS (#homePricing) -->
    <section class="palladio-pricing-wrapper" id="homePricing">
      <div class="palladio-pricing-container">
        <!-- Header -->
        <div class="palladio-pricing-header">
          <div>
            <div class="palladio-pricing-tag">
              <span class="tag-dot">+</span> PLANES &middot; LICENCIAMIENTO TRANSPARENTE
            </div>
            <h2 class="palladio-pricing-title">Precios transparentes para decisiones reales</h2>
          </div>
          <div>
            <p class="palladio-pricing-lead">
              Tarifa fija, sin costos ocultos ni sorpresas en facturaci&oacute;n. Custodia soberana de tus datos directamente en tu propia cuenta de Google Drive desde el primer d&iacute;a.
            </p>
          </div>
        </div>

        <!-- Apple Segmented Control Billing Toggle -->
        <div class="palladio-pricing-toggle-wrap">
          <div class="apple-segmented-control" role="tablist" aria-label="Periodo de facturación">
            <button class="segmented-btn active" id="btnBillMonthly" onclick="setHomeBilling('monthly')">Facturaci&oacute;n Mensual</button>
            <button class="segmented-btn" id="btnBillYearly" onclick="setHomeBilling('yearly')">Facturaci&oacute;n Anual (2 meses gratis)</button>
          </div>
        </div>

        <!-- 3 Plan Cards Grid -->
        <div class="palladio-pricing-grid">

          <!-- PLAN 1: STARTER -->
          <div class="palladio-plan-card">
            <div class="palladio-plan-header">
              <div class="palladio-plan-name">Starter</div>
              <p class="palladio-plan-desc">Para estudiantes, docentes y analistas independientes que inician en el modelado nodal.</p>
              <div class="palladio-plan-price-row">
                <span class="palladio-price-currency">$</span>
                <span class="palladio-price-amount" id="priceStarterVal">0</span>
                <span class="palladio-price-period">/ mes</span>
              </div>
              <div class="palladio-price-subtext">Gratuito para siempre</div>
            </div>
            <div class="palladio-plan-features">
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Hasta 3 sistemas producto activos</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Modelado en lienzo nodal drag &amp; drop</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Bases de datos de biosfera abiertas</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Exportaci&oacute;n de datos a CSV y JSON</span>
              </div>
            </div>
            <div class="palladio-plan-cta">
              <button class="palladio-plan-btn outline" onclick="window.EconodeApp && window.EconodeApp.showView('signup')">
                Comenzar Gratis &rarr;
              </button>
            </div>
          </div>

          <!-- PLAN 2: PROFESIONAL STUDIO (RECOMENDADO) -->
          <div class="palladio-plan-card featured">
            <div class="palladio-featured-pill">M&Aacute;S POPULAR</div>
            <div class="palladio-plan-header">
              <div class="palladio-plan-name">Profesional Studio</div>
              <p class="palladio-plan-desc">Para consultores de sostenibilidad, ingenieros y empresas que requieren rigor normativo.</p>
              <div class="palladio-plan-price-row">
                <span class="palladio-price-currency">$</span>
                <span class="palladio-price-amount" id="priceProVal">79</span>
                <span class="palladio-price-period">USD / mes</span>
              </div>
              <div class="palladio-price-subtext" id="subtextProVal">Facturado mensualmente</div>
            </div>
            <div class="palladio-plan-features">
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Cat&aacute;logo oficial de 26,533 procesos ecoinvent 3.12</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Custodia soberana Bring Your Own Storage (BYOS)</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>C&aacute;lculo matricial Leontief ilimitado en milisegundos</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Exportaci&oacute;n openLCA v2, ILCD XML y SimaPro CSV</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Generaci&oacute;n autom&aacute;tica de informes ejecutivos EPD</span>
              </div>
            </div>
            <div class="palladio-plan-cta">
              <button class="palladio-plan-btn solid" onclick="window.EconodeApp && window.EconodeApp.showView('studio')">
                Ingresar al Studio &rarr;
              </button>
            </div>
          </div>

          <!-- PLAN 3: ENTERPRISE & AUDITORIA -->
          <div class="palladio-plan-card">
            <div class="palladio-plan-header">
              <div class="palladio-plan-name">Enterprise Industrial</div>
              <p class="palladio-plan-desc">Para corporativos multi-planta y organismos certificadores de declaraciones ambientales.</p>
              <div class="palladio-plan-price-row">
                <span class="palladio-price-currency">$</span>
                <span class="palladio-price-amount" id="priceEntVal">249</span>
                <span class="palladio-price-period">USD / mes</span>
              </div>
              <div class="palladio-price-subtext" id="subtextEntVal">Facturado mensualmente</div>
            </div>
            <div class="palladio-plan-features">
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Todo lo incluido en Profesional Studio</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Auditor&iacute;a multi-rol RBAC (Analista, Auditor, Direcci&oacute;n)</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>18 cl&aacute;usulas auditables de NOM-070-SE e ISO 14044</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>Estampado de firma digital criptogr&aacute;fica HMAC-SHA256</span>
              </div>
              <div class="palladio-feature-item">
                <span class="feat-check">&radic;</span>
                <span>API REST dedicada, integraci&oacute;n ERP y SLA del 99.9%</span>
              </div>
            </div>
            <div class="palladio-plan-cta">
              <button class="palladio-plan-btn outline" onclick="window.location.href='mailto:contacto@econode.io?subject=Informacion%20Plan%20Enterprise'">
                Contactar a Direcci&oacute;n &rarr;
              </button>
            </div>
          </div>

        </div>
      </div>
    </section>

'''

html = html.replace(target_cta, cases_and_pricing_html + target_cta)

# 5. Add script for setHomeBilling
billing_script = '''
  <script>
    function setHomeBilling(type) {
      var btnM = document.getElementById('btnBillMonthly');
      var btnY = document.getElementById('btnBillYearly');
      var pPro = document.getElementById('priceProVal');
      var sPro = document.getElementById('subtextProVal');
      var pEnt = document.getElementById('priceEntVal');
      var sEnt = document.getElementById('subtextEntVal');
      
      if (type === 'yearly') {
        if (btnM) btnM.classList.remove('active');
        if (btnY) btnY.classList.add('active');
        if (pPro) pPro.textContent = '65';
        if (sPro) sPro.textContent = 'Facturado anualmente ($780/año - ahorras $168)';
        if (pEnt) pEnt.textContent = '199';
        if (sEnt) sEnt.textContent = 'Facturado anualmente ($2,388/año - ahorras $600)';
      } else {
        if (btnY) btnY.classList.remove('active');
        if (btnM) btnM.classList.add('active');
        if (pPro) pPro.textContent = '79';
        if (sPro) sPro.textContent = 'Facturado mensualmente';
        if (pEnt) pEnt.textContent = '249';
        if (sEnt) sEnt.textContent = 'Facturado mensualmente';
      }
    }
  </script>
</body>'''

html = html.replace('</body>', billing_script)

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Updated index.html with Cases and Pricing sections!')

