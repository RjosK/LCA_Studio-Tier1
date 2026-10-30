with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_html = text.find('<div class="case-canvas-board')
idx_next = text.find('<p class="case-section-text">\n          La matriz de tecnolog', idx_html)

from apply_final_spacious_canvas import canvas_board_final

text = text[:idx_html] + canvas_board_final.strip() + '\n\n        ' + text[idx_next:]

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Canvas board replaced successfully!")

