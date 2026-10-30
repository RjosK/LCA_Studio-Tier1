with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\ECONODE_VAULT\Bitacora_Cambios_2026_10_29.md', 'r', encoding='utf-8') as f:
    log = f.read()

entry = '''
### 02:53 AM - Corrección de Separación y Solapamiento de Tarjetas en Columna de Componentes
- **Problema reportado**: Las tarjetas de la columna izquierda (Cuerpo, Jarra, Cable, Partes, Empaque, Transporte) se montaban unas sobre otras debido a que la altura física de las tarjetas excedía el paso de separación vertical.
- **Solución implementada**:
  - Se incrementó el alto total del lienzo a 750 px.
  - Se aumentó el espaciado vertical entre tarjetas a 120 px (`top: 20px, 140px, 260px, 380px, 500px, 620px`).
  - Se ajustó el contenido interno de insumos a 2 líneas concisas por tarjeta, garantizando una altura uniforme de ~85 px y una separación libre real de ~35 px de espacio en blanco entre cada tarjeta.
  - Se recalcularon los puntos de origen Bézier y las etiquetas de Sankey para alinearse perfectamente con la nueva distribución vertical.
  - Se centró verticalmente el conjunto Ensamble (top: 275px), Uso Cafetera (top: 285px) y Disposición (top: 315px) en el eje y = 360 px.
  - Verificado visualmente mediante capturas completas en Chrome headless.
'''

log += entry

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\ECONODE_VAULT\Bitacora_Cambios_2026_10_29.md', 'w', encoding='utf-8') as f:
    f.write(log)

print("Bitacora updated successfully.")

