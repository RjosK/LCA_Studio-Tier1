with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div class="studio-node-card[^"]*"[^>]*>', text)
print('Found studio-node-card in HTML:', len(matches))
for m in matches:
    print(m)

# Also let's print the first card HTML
idx = text.find('class="studio-node-card"')
if idx != -1:
    print("\nFirst card:")
    print(text[idx:idx+800])

