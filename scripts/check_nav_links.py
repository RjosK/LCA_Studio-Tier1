with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
links = re.findall(r'<a[^>]*href=\"#home[^\"]*\"[^>]*>(.*?)</a>', text)
print('Anchor links to home sections:', links)
