import sys

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '    <!-- BOTTOM HIGH-IMPACT CTA BANNER -->'

profiles_html = '''    <!-- PALLADIO 3-PROFILES: TRES ROLES, UNA SOLA VERDAD -->
    <section class="palladio-profiles-wrapper" id="homeProfiles">
      <div class="palladio-profiles-container">
        <!-- Header -->
        <div class="palladio-profiles-header">
          <div>
            <div class="palladio-profiles-tag">
              <span class="tag-dot">+</span> PERFILES DE USUARIO
            </div>
            <h2 class="palladio-profiles-title">Tres roles, una sola verdad</h2>
          </div>
          <div>
            <p class="palladio-profiles-lead">
              Dise&ntilde;ado para alinear a los tres actores clave de la sostenibilidad industrial: el analista que modela, el auditor que certifica y el directivo que toma decisiones de inversi&oacute;n.
            </p>
          </div>
        </div>

        <!-- 3 Profiles Grid (Palladio Style) -->
        <div class="palladio-profiles-grid">

          <!-- PROFILE 1: ANALISTA DE CICLO DE VIDA -->
          <a href="#viewStudio" class="palladio-profile-card" onclick="if(window.EconodeApp) window.EconodeApp.showView('studio')">
            <div class="palladio-profile-thumb-wrap">
              <img src="images/case_studies/thumbs/small_01_watermill.jpg" alt="Analista de Ciclo de Vida" class="palladio-profile-thumb">
              <div class="palladio-profile-badge">
                <svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                Modelado &amp; C&aacute;lculo
              </div>
            </div>
            <div class="palladio-profile-body">
              <div>
                <h3 class="palladio-profile-name">Analista de Ciclo de Vida</h3>
                <p class="palladio-profile-desc">
                  Modela topolog&iacute;as nodales arrastrando procesos unitarios, resuelve matrices tecnol&oacute;gicas Leontief sobre 14,000 procesos de ecoinvent 3.12 y caracteriza impactos CML e IPCC sin latencia.
                </p>
              </div>
              <div class="palladio-profile-footer">
                <span class="palladio-profile-action-lbl">Ver flujo de an&aacute;lisis</span>
                <div class="palladio-profile-circle-btn">&rarr;</div>
              </div>
            </div>
          </a>

          <!-- PROFILE 2: AUDITOR NORMATIVO & CERTIFICADOR -->
          <a href="#viewStudio" class="palladio-profile-card" onclick="if(window.EconodeApp) window.EconodeApp.showView('studio')">
            <div class="palladio-profile-thumb-wrap">
              <img src="images/case_studies/thumbs/small_04_press.jpg" alt="Auditor Normativo" class="palladio-profile-thumb">
              <div class="palladio-profile-badge">
                <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
                Auditor&iacute;a &amp; Sellado
              </div>
            </div>
            <div class="palladio-profile-body">
              <div>
                <h3 class="palladio-profile-name">Auditor y Organismo de Certificaci&oacute;n</h3>
                <p class="palladio-profile-desc">
                  Examina balances de masa con trazabilidad forense, coteja evidencias documentales contra las 18 cl&aacute;usulas de NOM-070 e ISO 14044 y estampa firmas digitales HMAC-SHA256 para emisi&oacute;n de EPDs.
                </p>
              </div>
              <div class="palladio-profile-footer">
                <span class="palladio-profile-action-lbl">Ver protocolo de auditor&iacute;a</span>
                <div class="palladio-profile-circle-btn">&rarr;</div>
              </div>
            </div>
          </a>

          <!-- PROFILE 3: LIDER INDUSTRIAL & DIRECCION -->
          <a href="#viewStudio" class="palladio-profile-card" onclick="if(window.EconodeApp) window.EconodeApp.showView('studio')">
            <div class="palladio-profile-thumb-wrap">
              <img src="images/case_studies/thumbs/small_02_architecture.jpg" alt="L&iacute;der Industrial" class="palladio-profile-thumb">
              <div class="palladio-profile-badge">
                <svg viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/></svg>
                Estrategia &amp; Custodia
              </div>
            </div>
            <div class="palladio-profile-body">
              <div>
                <h3 class="palladio-profile-name">L&iacute;der Industrial y Direcci&oacute;n</h3>
                <p class="palladio-profile-desc">
                  Monitorea la huella de carbono de cartera, aprueba proyectos de descarbonizaci&oacute;n con ROI transparente y custodia todas las facturas y expedientes de planta en su propio Google Drive corporativo.
                </p>
              </div>
              <div class="palladio-profile-footer">
                <span class="palladio-profile-action-lbl">Ver gesti&oacute;n ejecutiva</span>
                <div class="palladio-profile-circle-btn">&rarr;</div>
              </div>
            </div>
          </a>

        </div>
      </div>
    </section>

'''

if target in content:
    new_content = content.replace(target, profiles_html + target)
    with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Inserted profiles successfully')
else:
    print('Target not found')

