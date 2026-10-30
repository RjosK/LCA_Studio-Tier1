with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_html = text.find('<div class="case-canvas-board')
print('idx_html:', idx_html)
print(text[idx_html-50:idx_html+250])

idx_next = text.find('La matriz de tecnolog', idx_html)
print('idx_next:', idx_next)
print(text[idx_next-250:idx_next])

