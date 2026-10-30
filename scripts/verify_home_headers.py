with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_home = text.find('id="viewHome"')
idx_login = text.find('id="viewLogin"')
home_section = text[idx_home:idx_login]

import re
# Check all major tags or headers inside viewHome
headers = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', home_section)
print('Headers in viewHome:')
for h in headers:
    print('  -', h.strip())
