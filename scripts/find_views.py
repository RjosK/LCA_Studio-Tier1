with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<section[^>]*id="([^"]+)"', text)
print('Section IDs in index.html:', matches)

view_matches = re.findall(r'<div[^>]*id="(view[^"]+)"', text)
print('View IDs in index.html:', view_matches)

