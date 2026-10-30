with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_home = text.find('id="viewHome"')
idx_login = text.find('id="viewLogin"')

home_section = text[idx_home:idx_login]
import re
sections = re.findall(r'<section[^>]*id="([^"]+)"', home_section)
print('Sections inside viewHome in index.html:', sections)
for s in sections:
    print(' - Section ID:', s)
