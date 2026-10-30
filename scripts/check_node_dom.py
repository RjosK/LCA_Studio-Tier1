with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\js\app.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('el.className = "process-node-card"')
if idx != -1:
    print(text[idx-100:idx+2000])

