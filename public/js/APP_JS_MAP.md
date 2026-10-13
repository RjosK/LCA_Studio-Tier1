# Mapa de Arquitectura y Referencia Rápida: `app.js`

> **Ubicación:** `econode_studio/web/js/app.js`  
> **Líneas Totales:** ~4,490 líneas  
> **Propósito:** Controlador frontend principal (Single Page Application - SPA) de ECONODE Studio. Gestiona estado reactivo, cliente API, enrutador de vistas, modelado en lienzo (canvas), catálogo ecoinvent 3.12, reportes dinámicos, checklist normativo y modales contextuales.

---

## Tabla Resumen de Secciones

| Sección | Rango de Líneas | Módulo / Responsabilidad Principal |
| :--- | :--- | :--- |
| [1. Estado Global](#1-estado-global-reactivo) | `L7 - L39` | `state` centralizado (usuario, vistas, nodos, filtros, paleta) |
| [2. Cliente API REST](#2-cliente-de-api-rest) | `L40 - L180` | Métodos `api.get`, `api.post`, endpoints de backend y exportaciones |
| [3. Enrutador & Vistas](#3-enrutador--gestión-de-vistas) | `L181 - L269` | `showView()`, protección de rutas y adaptación de Top Navbar |
| [4. Autenticación & RBAC](#4-autenticación--rbac) | `L270 - L479` | Login, Signup, sesión activa, roles (`analyst`, `auditor`, `client`) |
| [5. Dashboard de Proyectos](#5-dashboard-de-proyectos--sistemas) | `L480 - L788` | `loadDashboard()`, filtros por categoría/estado, KPIs, `openSystem()` |
| [6. Lienzo Interactivo](#6-lienzo-interactivo-de-modelado) | `L789 - L1605` | Canvas 2D, renderizado de nodos, Sankey, puertos, conexiones, drag & drop |
| [6.1 Editor de Proceso](#61-editor-visual-de-proceso) | `L1606 - L1803` | Modal de edición de proceso (#modalProcessEditor), balance de masas |
| [6.2 Selector Flujos DB](#62-selector-modal-de-flujos-lci) | `L1804 - L1937` | Modal de búsqueda de flujos ecoinvent (#modalSelectDbFlow) |
| [6.3 Selector Proveedor](#63-selector-de-proveedor-openlca) | `L1938 - L2060` | Búsqueda de proveedores unitarios (#modalSelectProvider) |
| [6.4 Notas por Proceso](#64-comentarios-por-proceso-en-lienzo) | `L2061 - L2330` | Notas adhesivas sobre nodos del lienzo (#modalAddProcessComment) |
| [7. Catálogo LCI 3.12](#7-explorador--catálogo-lci-ecoinvent-312) | `L2331 - L2528` | Explorador ecoinvent 3.12, 26,533 procesos, ficha técnica |
| [8. Reporte Técnico](#8-reporte-dinámico-hilos-y-exportaciones) | `L2529 - L2796` | Tablas de procesos, LCI consolidado, hilos de observaciones |
| [9. Checklist Normativo](#9-checklist-normativo-multi-norma) | `L2797 - L3009` | NOM-070, ISO 14044, cláusulas, estados, edición de evidencias, firma |
| [10. Bóveda de Documentos](#10-bóveda-de-documentos-vault) | `L3010 - L3166` | Custodia de evidencias por proyecto, carga y eliminación segura |
| [11. Modales de Interacción](#11-modales-del-sistema) | `L3167 - L3823` | Conexión nodos, Wizard SKU, Invitar Colaborador, Import CSV, Ajustes |
| [12. Notificaciones Toast](#12-notificaciones-flotantes-toast) | `L3824 - L3856` | Sistema flotante de alertas y confirmaciones (`showNotification`) |
| [13. Inicialización Global](#13-inicialización-global--listeners) | `L3857 - L4490` | `initApp()`, suscripción de eventos DOM, `window.EconodeApp` API |

---

## Detalle Módulo por Módulo

### 1. Estado Global Reactivo (`L7 - L39`)
Objeto singleton `state`:
- `currentUser`, `activeUser`, `isAuthenticated`: Sesión del usuario.
- `currentView`: Vista activa (`dashboard`, `canvas`, `catalog`, `report`, `audit`, etc.).
- `activeSystem`: Sistema producto actualmente cargado en memoria.
- `canvasNodes`, `canvasEdges`: Colección de procesos y conexiones en el lienzo.
- `paletteProcesses`: Procesos en la paleta lateral arrastrable.
- `selectedNode`, `activeConnectingPort`: Control de interacciones gráficas.

### 2. Cliente de API REST (`L40 - L180`)
Módulo `api` con envoltorio `fetch` con cabeceras JSON automáticas:
- **Auth**: `login`, `signup`, `getMe`, `logout`.
- **Sistemas**: `getDashboardSystems`, `getSystemCanvas`, `saveSystemCanvas`, `deleteSystem`.
- **Colaboración**: `inviteCollaborator`, `getComments`, `postComment`, `resolveComment`.
- **LCI**: `searchCatalog`, `getProcessSheet`, `getCategories`, `getDbFlows`, `getDbProviders`.
- **Auditoría**: `getAvailableStandards`, `getAuditChecklist`, `toggleClause`, `updateEvidence`, `signAudit`.
- **Bóveda**: `getDocuments`, `uploadDocument`, `deleteDocument`.

### 3. Enrutador & Gestión de Vistas (`L181 - L269`)
- `showView(viewName)`:
  - Protege rutas que requieren inicio de sesión (`isStudioRoute`).
  - Protege rutas que requieren proyecto abierto (`requiresOpenSystem`: canvas, reporte, auditoría).
  - Alterna entre el Navbar de Landing (`landingNavLinks`) y el de Studio (`studioNavLinks`).
  - Aplica permisos por rol con `applyRolePermissions()`.

### 4. Autenticación & RBAC (`L270 - L479`)
- `applyRolePermissions()`: Oculta o habilita botones según el rol (`analyst`, `auditor`, `client`).
- `initAuth()`: Valida sesión persistida en backend vía `/api/auth/me`.
- `handleLogin(e)`, `handleSignup(e)`, `handleLogout()`: Control de acceso con formulario y validaciones.

### 5. Dashboard de Proyectos & Sistemas (`L480 - L788`)
- `loadDashboard()`: Consulta la lista de sistemas y calcula KPIs reactivos:
  - Modelos Activos, Conformidad Normativa promedio, Documentos en Bóveda.
- `renderSystemsTable()`: Renderiza tabla de proyectos con:
  - Nombre, SKU, unidad, cantidad de procesos, equipo de trabajo con chips, estatus.
  - Botones contextuales: `📁 Bóveda`, `Abrir Lienzo ➔`, `🗑️ Eliminar`.
- `openSystem(sysId, navigateToCanvas)`:
  - Descarga nodos y aristas del sistema vía `/api/systems/<id>/canvas`.
  - Carga dinámicamente el equipo de trabajo en el lienzo (`#canvasProjectTeam`).
  - Asigna estado activo y redirige al lienzo o reporte.

### 6. Lienzo Interactivo de Modelado (`L789 - L1605`)
- Motor gráfico 2D sin librerías pesadas:
  - Transformaciones CSS (`pan` y `zoom` con rueda de ratón y arrastre de fondo).
  - Renderizado de aristas cúbicas bezier entre puertos de salida y entrada.
  - **Sankey Visualizer**: Modos `none`, `mass` y `energy` con grosores proporcionales.
  - **Drag & Drop**: Arrastre de procesos desde la paleta lateral al lienzo.
  - Selección e inspección de nodo (`inspectNode`).

### 6.1 a 6.4 Modales Auxiliares del Canvas (`L1606 - L2330`)
- **`openProcessEditor(targetId)`**: Editor de intercambios (insumos tecnosféricos, productos, residuos y emisiones).
- **`openSelectDbFlowModal(targetType)`**: Búsqueda en vivo de flujos oficiales ecoinvent 3.12.
- **`openSelectProviderModal(inputIndex)`**: Conexión de insumos con procesos proveedores reales.
- **`openNodeCommentModal(node)`**: Publicación de notas técnicas / adhesivas ancladas a procesos.

### 7. Explorador & Catálogo LCI (`L2331 - L2528`)
- Búsqueda en 26,533 procesos ecoinvent 3.12 con filtro por categoría.
- Visualización de la ficha técnica oficial (`renderProcessSheet`):
  - Unidad funcional, geografía, entradas tecnosféricas, salidas y emisiones.
  - Botón para insertar proceso directamente al sistema activo.

### 8. Reporte Técnico & Observaciones (`L2529 - L2796`)
- `loadReport()`:
  - `renderReportProcessesTable()`: Genera tabla dinámica de procesos y balances del sistema.
  - LCI Consolidado: Agrupa todos los flujos elementales y tecnosféricos de los nodos.
  - Hilo de Observaciones Colaborativas: Comentarios de analista, auditor y cliente.

### 9. Checklist Normativo Multi-Norma (`L2797 - L3009`)
- `loadAvailableStandards()`: Carga normas disponibles con selector inicial limpio.
- `loadAuditChecklist(standardId)`: Despliega las cláusulas de la norma elegida.
- `toggleClause(clauseId, isCompliant)`: Alterna estado entre Pendiente y Conforme.
- `editClauseEvidence(clauseId, currentEvidence)`: Permite al auditor modificar los requisitos de evidencia.
- `signAuditDictamen()`: Sellado digital SHA-256 de dictamen formal.

### 10. Bóveda de Documentos (`L3010 - L3166`)
- `loadDocumentsList()`: Consulta documentos vinculados al proyecto (`system_id`).
- `renderDocumentsTable()`: Renderiza archivos con nombre, tipo, tamaño y fecha.
- `deleteVaultDocument(docId, title)`: Eliminación de archivos custodiados con confirmación.
- Subida de archivos con drag & drop o selector de archivos.

### 11. Modales del Sistema (`L3167 - L3823`)
- `setupConnectNodesModal()`: Creación manual de conexiones entre procesos.
- `setupWizardModal()`: Creación de sistemas producto con **generación automática de SKU** a partir del nombre.
- `setupInviteCollaboratorModal()`: Invitación de Auditores y Clientes a proyectos específicos.
- `setupImportModal()`: Importación desde CSV de sistemas parametrizados.
- `setupSettingsModal()`: Configuración de cuenta, idioma y preferencias.
- `setupReportEditorToolbar()`: Barra de formato de texto (Word / Notion) para el reporte.

### 12. Notificaciones Toast (`L3824 - L3856`)
- `showNotification(msg, duration)`: Feedback visual flotante accesible para todas las acciones.

### 13. Inicialización Global (`L3857 - L4490`)
- `initApp()`: Bootstrap al cargar el DOM.
- `window.EconodeApp`: Expone métodos públicos para llamadas desde atributos HTML `onclick`.

