with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\ECONODE_VAULT\Bitacora_Cambios_2026_10_29.md', 'r', encoding='utf-8') as f:
    log = f.read()

entry = '''
### 02:50 AM - Ampliación de Espaciado y Líneas Dinámicas de Flujo Sankey
- **Solicitud del usuario**: Dar más espacio al lienzo del caso de estudio (evitar apariencia apretada) y agregar las líneas físicas proporcionales de los Sankeys, no solo los valores numéricos.
- **Implementación**:
  - **Ampliación y Breakout Editorial**:
    - Se aplicó un contenedor expandido a 1040 px de ancho con márgenes negativos compensados (`margin-left: -190px; width: calc(100% + 190px)`), alineando el lienzo con el borde exterior del layout general.
    - Se incrementó la altura del escenario a 680 px y el ancho de las tarjetas de componentes a 195-220 px con 25 px de separación vertical entre ellas.
    - Distribución horizontal holgada con 100-110 px de longitud para las curvas Bézier entre cada columna de procesos, garantizando visibilidad del 100% de los 10 nodos (desde Cuerpo hasta Disposición) sin recorte ni scrollbars en escritorio.
  - **Líneas Reales de Sankey (Ribbons Proporcionales)**:
    - Se agregaron clases dinámicas y estilos CSS con transiciones fluidas de 0.4s para transformar las líneas en cintas de flujo Sankey con grosor (`stroke-width`) estrictamente proporcional a la física del proceso:
      - *Cuerpo*: 16 px (`1.040 kg` / 44.9% de masa).
      - *Jarra*: 11 px (`0.600 kg` / 25.9% de masa).
      - *Empaque*: 7 px (`0.340 kg`).
      - *Transporte*: 6 px (`0.35 t*km`).
      - *Cable* y *Partes*: 4 px y 4.5 px (`0.165 kg` y `0.170 kg`).
      - *Tronco Ensamble a Uso*: 28 px (`2.315 kg` ensamblados).
      - *Tronco Uso a Disposición*: 28 px (`2.315 kg` residuo de fin de vida).
    - Pastillas vectoriales (tags) incrustadas directamente sobre el recorrido de los flujos mostrando la masa y energía.
    - Modos interactivos funcionales: `Estándar` (ingeniería de procesos), `Sankey Masa` (verde esmeralda `#059669`) y `Sankey Energía` (azul primario `#0284C7` con resplandor en la fase de uso).
  - Verificación visual con Chrome headless realizada con éxito.
'''

log += entry

with open(r'C:\Users\Josue\Documents\Espacio\ECONODE\ECONODE_VAULT\Bitacora_Cambios_2026_10_29.md', 'w', encoding='utf-8') as f:
    f.write(log)

print("Bitacora updated successfully.")

