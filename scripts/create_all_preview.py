import re

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

# Extract Bento
bento_match = re.search(r'(<!-- PALLADIO BENTO.*?<!-- PALLADIO ACCORDION)', index_html, re.DOTALL)
bento_part = bento_match.group(1).replace('<!-- PALLADIO ACCORDION', '') if bento_match else ''

# Extract Accordion
acc_match = re.search(r'(<!-- PALLADIO ACCORDION.*?<!-- PALLADIO 3-PROFILES)', index_html, re.DOTALL)
acc_part = acc_match.group(1).replace('<!-- PALLADIO 3-PROFILES', '') if acc_match else ''

# Extract Profiles
prof_match = re.search(r'(<!-- PALLADIO 3-PROFILES.*?<!-- BOTTOM HIGH-IMPACT)', index_html, re.DOTALL)
prof_part = prof_match.group(1).replace('<!-- BOTTOM HIGH-IMPACT', '') if prof_match else ''

full_preview = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview Completo Palladio Landing &mdash; ECONODE</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <style>
    body {{
      background: #F4F3EE !important;
      color: #18232C !important;
      font-family: 'Plus Jakarta Sans', sans-serif !important;
      margin: 0;
      padding: 40px 0 100px;
    }}
  </style>
</head>
<body>

{bento_part}

{acc_part}

{prof_part}

<script>
function openFaqCard(el) {{
  if (el.classList.contains('active')) return;
  document.querySelectorAll('.palladio-acc-card').forEach(function(c) {{ c.classList.remove('active'); }});
  el.classList.add('active');
}}
</script>
</body>
</html>
'''

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/preview_all_sections.html', 'w', encoding='utf-8') as f:
    f.write(full_preview)

print('preview_all_sections.html created successfully!')

