css_cases_pricing = '''

/* ==========================================================================
   PALLADIO CASOS DE ESTUDIO (#homeCases)
   ========================================================================== */
.palladio-cases-wrapper {
  background: #F4F3EE;
  padding: 80px 24px 70px;
  position: relative;
  z-index: 10;
}

.palladio-cases-container {
  max-width: 1360px;
  margin: 0 auto;
}

.palladio-cases-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 36px;
  flex-wrap: wrap;
  gap: 24px;
}

.palladio-cases-tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #18232C;
  margin-bottom: 12px;
}

.palladio-cases-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 46px;
  font-weight: 400;
  color: #18232C;
  line-height: 1.08;
  letter-spacing: -0.015em;
  margin: 0;
}

.palladio-cases-lead {
  font-size: 15px;
  color: #55606B;
  max-width: 480px;
  line-height: 1.55;
  margin: 0;
}

/* Featured Hero Case Card */
.palladio-featured-case-card {
  background: #FAF6ED;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 24px;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.palladio-featured-case-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(24, 35, 44, 0.07);
}

.palladio-featured-case-content {
  padding: 40px 44px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.palladio-case-badge-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.palladio-case-pill-dark {
  background: #18232C;
  color: #F4F3EE;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  padding: 4px 12px;
  border-radius: 999px;
  text-transform: uppercase;
}

.palladio-case-pill-green {
  background: #E8F5E9;
  color: #0E7F5E;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 4px 12px;
  border-radius: 999px;
}

.palladio-featured-case-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 34px;
  font-weight: 400;
  line-height: 1.15;
  color: #18232C;
  margin-bottom: 14px;
}

.palladio-featured-case-desc {
  font-size: 14px;
  line-height: 1.6;
  color: #55606B;
  margin-bottom: 24px;
}

.palladio-featured-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 28px;
  padding: 16px 0;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.palladio-feat-stat .stat-num {
  display: block;
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 26px;
  font-weight: 400;
  color: #18232C;
  line-height: 1;
}

.palladio-feat-stat .stat-lbl {
  font-size: 11.5px;
  font-weight: 600;
  color: #7A8691;
}

.palladio-featured-action-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.palladio-btn-case-cta {
  background: #18232C;
  color: #FAF9F5;
  font-size: 13.5px;
  font-weight: 600;
  padding: 10px 22px;
  border-radius: 999px;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.palladio-btn-case-cta:hover {
  background: #0E7F5E;
  transform: translateX(2px);
}

.palladio-case-hint {
  font-size: 12px;
  color: #7A8691;
}

.palladio-featured-case-media {
  background: #E5E2D8;
  position: relative;
  overflow: hidden;
}

.palladio-featured-case-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  display: block;
  transition: transform 0.4s ease;
}

.palladio-featured-case-card:hover .palladio-featured-case-img {
  transform: scale(1.025);
}

/* Secondary Cases Grid */
.palladio-secondary-cases-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.palladio-sec-case-card {
  background: #ECE9DF;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 16px;
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 20px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  text-decoration: none;
  color: inherit;
}

.palladio-sec-case-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(24, 35, 44, 0.06);
}

.palladio-sec-case-thumb-wrap {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  height: 140px;
  background: #DDD9CE;
}

.palladio-sec-case-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.palladio-sec-case-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(24, 35, 44, 0.85);
  color: #F4F3EE;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
  backdrop-filter: blur(4px);
}

.palladio-sec-case-body {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.palladio-sec-case-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 21px;
  font-weight: 400;
  color: #18232C;
  line-height: 1.2;
  margin-bottom: 6px;
}

.palladio-sec-case-desc {
  font-size: 12.5px;
  color: #55606B;
  line-height: 1.45;
  margin-bottom: 10px;
}

.palladio-sec-case-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.case-metric-highlight {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  font-weight: 700;
  color: #0E7F5E;
}

.palladio-circle-arrow-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #FAF9F5;
  border: 1px solid rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #18232C;
  text-decoration: none;
  transition: all 0.2s ease;
}

.palladio-sec-case-card:hover .palladio-circle-arrow-btn {
  background: #18232C;
  color: #FAF9F5;
  transform: translateX(2px);
}

/* ==========================================================================
   PALLADIO PLANES Y PRECIOS (#homePricing)
   ========================================================================== */
.palladio-pricing-wrapper {
  background: #F4F3EE;
  padding: 80px 24px 100px;
  position: relative;
  z-index: 10;
}

.palladio-pricing-container {
  max-width: 1360px;
  margin: 0 auto;
}

.palladio-pricing-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 24px;
}

.palladio-pricing-tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #18232C;
  margin-bottom: 12px;
}

.palladio-pricing-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 46px;
  font-weight: 400;
  color: #18232C;
  line-height: 1.08;
  letter-spacing: -0.015em;
  margin: 0;
}

.palladio-pricing-lead {
  font-size: 15px;
  color: #55606B;
  max-width: 480px;
  line-height: 1.55;
  margin: 0;
}

.palladio-pricing-toggle-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
}

.palladio-pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  align-items: stretch;
}

.palladio-plan-card {
  background: #FAF6ED;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 22px;
  padding: 36px 32px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.palladio-plan-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px rgba(24, 35, 44, 0.08);
  border-color: rgba(24, 35, 44, 0.2);
}

.palladio-plan-card.featured {
  background: #FFFFFF;
  border-color: rgba(14, 127, 94, 0.35);
  box-shadow: 0 8px 28px rgba(14, 127, 94, 0.08);
}

.palladio-featured-pill {
  position: absolute;
  top: -12px;
  left: 32px;
  background: #0E7F5E;
  color: #FAF9F5;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 4px 14px;
  border-radius: 999px;
  box-shadow: 0 2px 8px rgba(14, 127, 94, 0.3);
}

.palladio-plan-name {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 30px;
  font-weight: 400;
  color: #18232C;
  margin-bottom: 8px;
}

.palladio-plan-desc {
  font-size: 13.5px;
  color: #55606B;
  line-height: 1.5;
  min-height: 42px;
  margin-bottom: 20px;
}

.palladio-plan-price-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 4px;
}

.palladio-price-currency {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 28px;
  color: #18232C;
}

.palladio-price-amount {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 52px;
  color: #18232C;
  font-weight: 400;
  line-height: 1;
}

.palladio-price-period {
  font-size: 13px;
  font-weight: 600;
  color: #7A8691;
  margin-left: 4px;
}

.palladio-price-subtext {
  font-size: 11.5px;
  color: #7A8691;
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 24px;
}

.palladio-plan-features {
  border-top: 1px solid rgba(0, 0, 0, 0.07);
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.palladio-feature-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #38424B;
  line-height: 1.45;
}

.palladio-feature-item .feat-check {
  color: #0E7F5E;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.2;
}

.palladio-plan-cta {
  margin-top: 20px;
}

.palladio-plan-btn {
  width: 100%;
  padding: 12px 20px;
  border-radius: 999px;
  font-size: 13.5px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  text-decoration: none;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.palladio-plan-btn.outline {
  background: transparent;
  border: 1px solid rgba(24, 35, 44, 0.2);
  color: #18232C;
}

.palladio-plan-btn.outline:hover {
  background: #18232C;
  color: #FAF9F5;
}

.palladio-plan-btn.solid {
  background: #18232C;
  border: 1px solid #18232C;
  color: #FAF9F5;
  box-shadow: 0 4px 14px rgba(24, 35, 44, 0.15);
}

.palladio-plan-btn.solid:hover {
  background: #0E7F5E;
  border-color: #0E7F5E;
  transform: translateY(-1px);
}

@media (max-width: 1024px) {
  .palladio-featured-case-card {
    grid-template-columns: 1fr;
  }
  .palladio-featured-case-media {
    height: 240px;
  }
  .palladio-secondary-cases-grid {
    grid-template-columns: 1fr;
  }
  .palladio-pricing-grid {
    grid-template-columns: 1fr;
  }
}
'''

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/css/styles.css', 'a', encoding='utf-8') as f:
    f.write(css_cases_pricing)

print('CSS for cases and pricing appended successfully')

