import sys

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\js\app.js', 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

idx = text.find('el.innerHTML = `')
if idx != -1:
    sys.stdout.reconfigure(encoding='utf-8')
    print(text[idx:idx+2500])
