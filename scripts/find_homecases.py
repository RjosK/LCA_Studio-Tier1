with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="homeCases"')
print('homeCases at:', idx)
print(text[idx-100:idx+400])

