# Mapa de Estructura y Navegación Rápida: `index.html`

> **Ubicación:** `econode_studio/web/index.html`  
> **Líneas Totales:** ~1,810 líneas  
> **Propósito:** Plantilla HTML única de la aplicación web (SPA) de ECONODE Studio. Contiene el encabezado superior adaptable, las 8 vistas de pantalla completas (`<main class="view-container">`) y los 11 modales interactivos (`<div class="modal-overlay">`).

---

## Tabla de Vistas y Componentes Principales

| Tipo | ID del Elemento | Rango de Líneas | Descripción / Contenido |
| :--- | :--- | :--- | :--- |
| **Top Nav** | `#topNavbar` | `L18 - L91` | Barra superior unificada, logo ECONODE, pestañas de navegación y píldora de usuario |
| **Vista 0** | `#viewHome` | `L94 - L479` | Landing Page de bienvenida (Hero, features, arquitectura, testimonios y FAQ) |
| **Vista 1** | `#viewLogin` | `L482 - L560` | Pantalla de inicio de sesión, Google Workspace y accesos directos por perfil |
| **Vista 2** | `#viewSignup` | `L563 - L627` | Registro de cuenta corporativa y selección de perfil (Analista / Auditor / Cliente) |
| **Vista 3** | `#viewDashboard` | `L630 - L701` | Portafolio de proyectos, KPIs de modelos, filtros por categoría y tabla de proyectos |
| **Vista 4** | `#viewCanvas` | `L704 - L806` | Lienzo interactivo de modelado 2D, paleta de procesos, Sankey y balance de masa |
| **Vista 5** | `#viewCatalog` | `L809 - L886` | Explorador del catálogo ecoinvent 3.12 (26,533 procesos) y ficha técnica |
| **Vista 6** | `#viewReport` | `L889 - L1039` | Reporte técnico de ACV, edición tipo Notion, LCI consolidado e hilos de comentarios |
| **Vista 7** | `#viewAudit` | `L1042 - L1118` | Checklist normativo multi-norma (NOM-070, ISO 14044), cláusulas y dictamen |

---

## Tabla de Modales Contextuales (`modal-overlay`)

| Modal ID | Rango de Líneas | Título / Propósito |
| :--- | :--- | :--- |
| `#modalDocuments` | `L1121 - L1181` | **Bóveda de Documentos**: Archivos custodiados por proyecto (SQL, Excel, PDF, JSON) con subida y eliminación |
| `#modalConnectNodes` | `L1184 - L1223` | **Conectar Procesos**: Asistente para enlazar flujo de salida con proceso de entrada en el lienzo |
| `#modalWizard` | `L1226 - L1329` | **Nuevo Sistema Producto**: Wizard con autogeneración de SKU derivado del nombre |
| `#modalImport` | `L1332 - L1389` | **Centro de Importación**: Importador de archivos CSV parametrizados |
| `#modalInviteCollaborator`| `L1392 - L1442` | **Invitar Colaborador**: Invitación de Auditores o Clientes al equipo del proyecto |
| `#modalSettings` | `L1445 - L1476` | **Ajustes & Facturación**: Perfil, configuración regional, planes y suscripción |
| `#modalAddProcessComment` | `L1479 - L1514` | **Nota Técnica en Proceso**: Creación de notas adhesivas ancladas a nodos del lienzo |
| `#modalProcessEditor` | `L1517 - L1628` | **Editor Visual de Proceso**: Edición detallada de insumos, flujos de referencia, residuos y emisiones |
| `#modalSelectDbFlow` | `L1631 - L1665` | **Selector de Flujos LCI**: Búsqueda en vivo de flujos oficiales en ecoinvent 3.12 |
| `#modalSelectProvider` | `L1668 - L1697` | **Selector de Proveedor**: Selección de proceso unitario que abastece un insumo (estilo openLCA) |
| `#modalSubscription` | `L1700 - L1780` | **Suscripción Studio**: Planes Profesional, Enterprise y Auditoría NOM-070 |

---

## Elementos Globales Flotantes y Scripts
- **Toolbars Flotantes (`L1783 - L1801`)**:
  - `#reportHighlightTooltip`: Tooltip para subrayar y crear observaciones en el reporte.
  - `#reportBubbleToolbar`: Barra flotante estilo Notion / Medium para negrita, cursiva, subrayado y resaltado.
- **Scripts y Anti-Caché (`L1802 - L1806`)**:
  - `js/i18n.js`: Diccionario bilingüe sin recarga.
  - `js/app.js`: Controlador reactivo SPA.

