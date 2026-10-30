import re

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Extract #homeCases
cases_match = re.search(r'(<!-- PALLADIO CASOS DE ESTUDIO.*?<!-- PALLADIO PLANES)', text, re.DOTALL)
cases_part = cases_match.group(1).replace('<!-- PALLADIO PLANES', '') if cases_match else ''

# Extract #homePricing
pricing_match = re.search(r'(<!-- PALLADIO PLANES Y PRECIOS.*?<!-- BOTTOM HIGH-IMPACT)', text, re.DOTALL)
pricing_part = pricing_match.group(1).replace('<!-- BOTTOM HIGH-IMPACT', '') if pricing_match else ''

preview_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Preview Casos y Planes &mdash; ECONODE</title>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&amp;family=JetBrains+Mono:wght@400;500;600;700&amp;family=Plus+Jakarta+Sans:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <style>
    body {{ background: #F4F3EE; padding: 20px 0 100px; font-family: 'Plus Jakarta Sans', sans-serif; }}
  </style>
</head>
<body>

{cases_part}

{pricing_part}

<script>
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

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_cases_and_pricing.html', 'w', encoding='utf-8') as f:
    f.write(preview_html)

print('preview_cases_and_pricing.html created')

