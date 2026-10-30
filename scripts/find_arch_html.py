with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<div class="case-system-arch">', text)]
print('HTML occurrences:', matches)
for m in matches:
    print(text[m:m+800])

