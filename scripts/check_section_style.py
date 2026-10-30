with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('.case-section-label')
if idx != -1:
    print(text[idx-50:idx+600])

