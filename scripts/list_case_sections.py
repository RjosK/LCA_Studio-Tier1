with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
sections = re.findall(r'<div class="case-section-tag">(.*?)</div>', text)
print('Sections tags:', sections)

