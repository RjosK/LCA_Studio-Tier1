with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\public\js\app.js', 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

idx = text.find('const isSankeyMass = state.sankeyMode === "mass"')
if idx != -1:
    print(text[idx+1800:idx+3800])

