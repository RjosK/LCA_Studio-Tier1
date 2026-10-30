with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/case_cafetera.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'La matriz de tecnolog&iacute;a $A$ de $10 \\times 10$ se vincul&oacute; autom&aacute;ticamente a los procesos de fondo de ecoinvent 3.12 Cut-off para caracterizar los intercambios elementales de biosfera, resolviendo el vector de escalamiento de demanda final $s = (I - A)^{-1} f$ en menos de 12 milisegundos en el navegador.'
replacement = 'La matriz de tecnolog&iacute;a <em>A</em> de 10 &times; 10 se vincul&oacute; autom&aacute;ticamente a los procesos de fondo de ecoinvent 3.12 Cut-off para caracterizar los intercambios elementales de biosfera, resolviendo el vector de escalamiento de demanda final <em>s</em> = (<em>I</em> &minus; <em>A</em>)<sup>&minus;1</sup> <em>f</em> en menos de 12 milisegundos en el navegador.'

text = text.replace(target, replacement)

with open('C:/Users/Josue/Documents/Espacio/ECONODE/public/case_cafetera.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated math formatting')

