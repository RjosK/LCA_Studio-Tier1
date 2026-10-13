# Arquitectura de ECONODE Studio (Tier 1) & Separación de Módulos

## 1. Visión General del Sistema & Separación Comercial

**ECONODE Studio** es la plataforma de análisis de ciclo de vida (ACV) y declaraciones ambientales de producto (EPD) diseñada conforme a las normas ISO 14040/14044 y NOM-070-SE-2024.

Para estructurar una oferta comercial clara y escalable, la arquitectura se divide en dos niveles de servicio:

1. **Tier 1 — ECONODE Studio (Suscripción Base)**:
   - **Autenticación Corporativa**: Integración oficial con Google Identity Services (OAuth 2.0 / JWT) y perfiles RBAC (Auditor Líder ACV vs Cliente Productor).
   - **Gestión de Portafolio ACV**: Dashboard de proyectos, métricas ejecutivas de huella consolidada y estados de auditoría.
   - **Modelado en Lienzo Visual**: Diseño interactivo de procesos unitarios, inspección de insumos/productos, y vinculación con la base de datos de 26,533 procesos ecoinvent 3.12 y Sphera Managed.
   - **Centro de Importación Multiformato**: Importación masiva por lotes desde plantillas CSV parametrizadas, paquetes openLCA (JSON-LD), matrices de auditoría y evidencias documentales NOM-070.
   - **Auditoría Colaborativa**: Hilos de discusión estilo Google Docs / Notion entre auditor y cliente para resolver objeciones técnicas.
   - **Checklist Normativo NOM-070 / ISO 14044**: Verificación cláusula por cláusula (§4.2 a §4.5) con cálculo dinámico de conformidad y firma digital de dictámenes.
   - **Modo sin cálculo numérico**: En esta versión de Tier 1 **no se ejecuta resolución matricial lineal ni simulación estocástica**; se enfoca en el inventario, balance de masa de ingeniería, estructuración de modelos y trazabilidad documental.

2. **Tier 2 — Pro Matrix Engine (Módulo Add-on Opcional)**:
   - Inversión de matrices tecnológicas Leontief: $s = A^{-1}f$ en < 5 ms.
   - Simulación estocástica de Monte Carlo con 1,000 iteraciones y matrices Pedigree de incertidumbre.
   - Exportadores industriales especializados (openLCA JSON-LD, GaBi ILCD XML, SimaPro CSV).

---

## 2. Diagrama Interactivo de Flujos de Datos

La arquitectura cuenta con un visor interactivo autónomo paso a paso:
- **Visor Interactivo**: [econode_studio_architecture.html](file:///c:/Users/Josue/Documents/Espacio/Brigthway/econode_studio_architecture.html) (y en [Artifacts](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/econode_studio_architecture.html)).

Permite seleccionar los 7 flujos de datos principales y alternar entre los modos **Tier 1** y **Tier 2**:

| Flujo | Origen | Destino | Protocolo / Payload |
| :--- | :--- | :--- | :--- |
| **1. Autenticación Google & RBAC** | `Cliente Web` ➔ `Google OAuth` ➔ `API Gateway` | `SQLite Session` | JWT Token RS256, verificación con `tokeninfo`, asignación de rol (`auditor` vs `user`). |
| **2. Creación Wizard (3 Pasos)** | `Modal Wizard` ➔ `API Gateway` | `ProductSystem Repository` | Metadatos, SKU único, UF de referencia cuantitativa (ej: `1.000 u`) y base ecoinvent 3.12. |
| **3. Importación Masiva CSV/openLCA** | `Dropzone UI` ➔ `API Gateway` | `LCI Database` & `SQLite` | Parsing de `plantilla_sistemas_parametrizados.csv`, autoconexión semántica e inserción de grafos DAG. |
| **4. Modelado en Lienzo & LCI** | `Canvas Studio` ➔ `Catálogo LCI` | `SQLite Graph` | Búsqueda predictiva en 26,533 procesos ecoinvent 3.12, inserción nodal y serialización en `Roboto Mono`. |
| **5. Auditoría Colaborativa & Hilos** | `Auditor (JA)` ➔ `Cliente (ER)` | `Cripto Ledger` | Hilos de discusión, respuestas con cartas porte, resolución de observaciones y sello SHA-256. |
| **6. Checklist NOM-070 / ISO 14044** | `Matriz Cláusulas` ➔ `Auditor Líder` | `Snapshot Criptográfico` | Evaluación 18 cláusulas, balance de masa al 100%, dictamen conforme (94.4%) y firma digital inmutable. |
| **7. Motor Matricial (Tier 2 Add-on)** | `Motor Matricial Leontief` | `Resultados Pro` | Inversión $s = A^{-1}f$ y 1,000 iteraciones Monte Carlo (activo solo con suscripción Pro). |

---

## 3. Topología de Componentes (Clean Architecture)

```
econode_studio/
├── domain/                      # Entidades puras y reglas de negocio inmutables
│   ├── product_system.py        # Grafo acíclico dirigido (DAG), nodos y flujos
│   ├── lci_exchange.py          # Intercambios tecnosféricos y elementales
│   ├── audit_checklist.py       # 18 Cláusulas NOM-070 / ISO 14044 y dictámenes
│   └── user_account.py          # Cuentas, roles RBAC y tokens de sesión
├── application/                 # Casos de uso de la aplicación
│   ├── auth_service.py          # Verificación Google GSI y conmutación de cuentas
│   ├── product_systems.py       # Creación, guardado e importación de sistemas
│   ├── lci_catalog.py           # Búsqueda y correspondencia semántica bilingüe
│   ├── collaborative_audit.py   # Gestión de hilos de comentarios
│   └── normative_audit.py       # Evaluación del checklist y firma digital SHA-256
├── infrastructure/              # Adaptadores a bases de datos y servicios
│   ├── sqlite_repository.py     # Repositorio SQLite (product_systems, comments, audit)
│   ├── ecoinvent_adapter.py     # Conexión solo lectura a ecoinvent_312.db
│   ├── google_oauth_adapter.py  # Conexión nativa con urllib a Google TokenInfo
│   └── crypto_signer.py         # Generación de sellos SHA-256 y libros mayores
├── api/                         # REST API Gateway (Python http.server estándar)
│   └── server.py                # Endpoints RESTful y servidor de archivos estáticos
└── web/                         # Aplicación Web Frontend (Vanilla ES Modules / Apple HIG)
    ├── index.html               # SPA unificada con todas las vistas de Penpot
    ├── css/                     # Tokens de diseño Apple HIG, 0% emojis, modo claro/oscuro
    └── js/                      # Lógica reactiva modular sin frameworks pesados
```

---

## 4. Tableros Diseñados en Penpot

Conforme a las instrucciones, todas las vistas se han diseñado primero en **Penpot** y exportado como artefactos PNG:

1. **`00 Iniciar Sesión & Google Sign-In`**: [penpot_econode_login_google.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_login_google.png)
2. **`00b Registro de Cuenta & Organización`**: [penpot_econode_signup_organization.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_signup_organization.png)
3. **`Modal Wizard: + Nuevo Sistema Producto`**: [penpot_econode_wizard_nuevo_sistema.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_wizard_nuevo_sistema.png)
4. **`Modal: Centro de Importación de Archivos`**: [penpot_econode_modal_importacion_archivos.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_modal_importacion_archivos.png)
5. **`Dashboard de Proyectos ACV`**: [penpot_econode_dashboard_proyectos.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_dashboard_proyectos.png)
6. **`Explorador LCI & Procesos`**: [penpot_econode_explorador_lci.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_explorador_lci.png)
7. **`Checklist Normativo NOM-070 / ISO 14044`**: [penpot_econode_checklist_normativo.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_checklist_normativo.png)
8. **`Facturación & Planes (Separación Tier 1 vs Tier 2)`**: [penpot_econode_ajustes_facturacion_planes.png](file:///C:/Users/Josue/.gemini/antigravity/brain/1effe389-9b90-4ace-92bb-9bb36cd623af/penpot_econode_ajustes_facturacion_planes.png)
