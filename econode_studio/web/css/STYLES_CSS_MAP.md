# Mapa de Estilos y Diseño: `styles.css`

> **Ubicación:** `econode_studio/web/css/styles.css`  
> **Líneas Totales:** ~1,430 líneas  
> **Propósito:** Hoja de estilos central de ECONODE Studio. Implementa el sistema de diseño Apple Human Interface Guidelines (HIG) para aplicaciones desktop compactas (escala tipográfica 11-13px, contraste alto, superficies con relieve sutil y estados táctiles `scale(0.97)`).

---

## Tabla de Módulos y Secciones CSS

| Sección | Rango de Líneas | Contenido y Selectores Clave |
| :--- | :--- | :--- |
| **Variables y Tokens** | `L1 - L58` | `:root` con paleta Apple Slate/Emerald, variables de color de fondo, bordes, radios y sombras |
| **Top Navigation Bar** | `L59 - L241` | `.top-navbar`, `.brand-section`, `.project-title`, `.nav-links`, `.nav-btn`, `.user-pill`, `.lang-toggle` |
| **Botones del Sistema** | `L242 - L300` | `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-emerald`, `.btn-danger`, estados hover y active |
| **Contenedores de Vista** | `L301 - L314` | `.view-container`, `.view-container.active` (control de visibilidad SPA sin recargas) |
| **Autenticación (Auth)** | `L315 - L485` | `.auth-wrapper`, `.auth-card`, inputs, tabs de roles y botón `.btn-google` |
| **Dashboard de Proyectos** | `L486 - L613` | `.dashboard-header`, `.kpi-grid`, `.kpi-card`, tablas `.data-table`, badges de estado y filtros |
| **Lienzo de Modelado (Canvas)** | `L614 - L689` | `.canvas-wrapper`, paneles laterales, paleta `.palette-item`, nodos `.canvas-node`, puertos `.port` |
| **Modales (`modal-overlay`)** | `L690 - L761` | `.modal-overlay`, `.modal-card`, encabezados, inputs `.form-input` y pie de acción de modales |
| **Landing Page de Inicio** | `L762 - L1077` | Hero visual de Penpot, diagramas SVG de árbol dirigido, cards de producto, testimonios y FAQ |
| **Conectores y Sankey** | `L1078 - L1160` | Rutas bezier SVG, flujo volumétrico dinámico con colores de flujo de masa y energía |
| **Reporte Ejecutivo & Print** | `L1161 - L1248` | `#reportDocumentBody`, tablas LCI, hilos de comentarios y encabezados oficiales de impresión |
| **Notas Adhesivas (Post-its)** | `L1249 - L1308` | `.canvas-sticky-note`, anclajes amarillos, botón de cierre y autor de la nota en el lienzo |
| **Editor de Procesos (Penpot V1)** | `L1309 - L1334` | `.flow-item-card`, columnas de insumos vs emisiones, badges de flujos unitarios |
| **Toolbar Flotante (Notion)** | `L1335 - L1355` | `#reportBubbleToolbar`, `#reportHighlightTooltip`, botones flotantes con efecto backdrop blur |
| **Responsividad Desktop** | `L1356 - L1430` | `@media screen (max-width: 1200px / 1024px)` para ergonomía desktop y `@media print` para exportación PDF |

---

## Paleta de Variables Globales (`:root`)

```css
--bg-app: #F8FAFC;                 /* Fondo principal de la aplicación */
--bg-card: #FFFFFF;                /* Superficie de tarjetas y modales */
--bg-muted: #F1F5F9;               /* Fondo sutil de controles y badges */
--text-primary: #0F172A;           /* Texto principal (alto contraste) */
--text-secondary: #475569;         /* Texto secundario y etiquetas */
--text-muted: #64748B;             /* Subtextos y metadatos */
--accent-emerald: #059669;         /* Acento principal de conformidad NOM-070 */
--accent-blue: #0284C7;            /* Acento para perfiles de Analista */
--accent-purple: #7C3AED;          /* Acento para perfiles de Cliente */
```

