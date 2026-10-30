with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_nav = text.find('class="landing-nav-center"')
if idx_nav != -1:
    print(text[idx_nav:idx_nav+600])
