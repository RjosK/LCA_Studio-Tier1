import re

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Bento
bento_m = re.search(r'(<!-- PALLADIO BENTO.*?<!-- PALLADIO ACCORDION)', text, re.DOTALL)
bento = bento_m.group(1).replace('<!-- PALLADIO ACCORDION', '') if bento_m else ''

# Accordion
acc_m = re.search(r'(<!-- PALLADIO ACCORDION.*?<!-- PALLADIO 3-PROFILES)', text, re.DOTALL)
acc = acc_m.group(1).replace('<!-- PALLADIO 3-PROFILES', '') if acc_m else ''

# Profiles
prof_m = re.search(r'(<!-- PALLADIO 3-PROFILES.*?<!-- PALLADIO CASOS)', text, re.DOTALL)
prof = prof_m.group(1).replace('<!-- PALLADIO CASOS', '') if prof_m else ''

# Cases
cases_m = re.search(r'(<!-- PALLADIO CASOS.*?<!-- PALLADIO PLANES)', text, re.DOTALL)
cases = cases_m.group(1).replace('<!-- PALLADIO PLANES', '') if cases_m else ''

# Pricing
pricing_m = re.search(r'(<!-- PALLADIO PLANES.*?<!-- BOTTOM HIGH-IMPACT)', text, re.DOTALL)
pricing = pricing_m.group(1).replace('<!-- BOTTOM HIGH-IMPACT', '') if pricing_m else ''

all_sections_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>ECONODE Studio &mdash; Suite Completa Palladio</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&amp;family=JetBrains+Mono:wght@400;500;600;700&amp;family=Plus+Jakarta+Sans:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <style>
    body {{ background: #F4F3EE; margin: 0; padding: 20px 0 100px; font-family: 'Plus Jakarta Sans', sans-serif; }}
  </style>
</head>
<body>

{bento}

{acc}

{prof}

{cases}

{pricing}

<script>
function openFaqCard(el) {{
  if (el.classList.contains('active')) return;
  document.querySelectorAll('.palladio-acc-card').forEach(function(c) {{ c.classList.remove('active'); }});
  el.classList.add('active');
}}

function setHomeBilling(type) {{
  var btnM = document.getElementById('btnBillMonthly');
  var btnY = document.getElementById('btnBillYearly');
  var pPro = document.getElementById('priceProVal');
  var sPro = document.getElementById('subtextProVal');
  var pEnt = document.getElementById('priceEntVal');
  var sEnt = document.getElementById('subtextEntVal');
  
  if (type === 'yearly') {{
    if (btnM) btnM.classList.remove('active');
    if (btnY) btnY.classList.add('active');
    if (pPro) pPro.textContent = '65';
    if (sPro) sPro.textContent = 'Facturado anualmente ($780/año - ahorras $168)';
    if (pEnt) pEnt.textContent = '199';
    if (sEnt) sEnt.textContent = 'Facturado anualmente ($2,388/año - ahorras $600)';
  }} else {{
    if (btnY) btnY.classList.remove('active');
    if (btnM) btnM.classList.add('active');
    if (pPro) pPro.textContent = '79';
    if (sPro) sPro.textContent = 'Facturado mensualmente';
    if (pEnt) pEnt.textContent = '249';
    if (sEnt) sEnt.textContent = 'Facturado mensualmente';
  }}
}}
</script>
</body>
</html>
'''

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_all_sections.html', 'w', encoding='utf-8') as f:
    f.write(all_sections_html)

print('Updated preview_all_sections.html with all 5 sections!')

