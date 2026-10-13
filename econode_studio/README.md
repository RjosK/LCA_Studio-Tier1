# ECONODE Studio (Tier 1) · Plataforma de Análisis de Ciclo de Vida & EPD

Plataforma profesional 100% web en la nube para el modelado de sistemas producto, auditoría normativa NOM-070-SE-2024 / ISO 14044, reportes dinámicos de inventario (LCI), bóveda documental y exportaciones industriales.

---

## 🏛️ Arquitectura & Separación de Módulos

El proyecto implementa **Clean Architecture (Puertos y Adaptadores)** desacoplando completamente la capa de negocio y presentación del motor de cálculo matricial pesado:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 ECONODE STUDIO (TIER 1)                 │
                  ├─────────────────────────────────────────────────────────┤
                  │  ● Modelado visual en lienzo con puertos y conectores   │
                  │  ● Modos Sankey de Masa (kg) y Energía (kWh / MJ)       │
                  │  ● Catálogo LCI ecoinvent 3.12 (26,533 procesos unit.)  │
                  │  ● Auditoría NOM-070 / ISO 14044 (18 cláusulas)         │
                  │  ● Bóveda Documental (SQL, Excel, PDF, JSON, ZIP)       │
                  │  ● Exportación: openLCA, ILCD/Sphera, SimaPro, CSV, ZIP │
                  │  ● RBAC con 3 perfiles: Analista, Auditor y Cliente     │
                  └───────────────────────────┬─────────────────────────────┘
                                              │ (API Gateway / Add-on)
                                              ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │                CÓMPUTO MATRICIAL (TIER 2)               │
                  ├─────────────────────────────────────────────────────────┤
                  │  ● Motor de Inversión Matricial Leontief (s = A⁻¹f)     │
                  │  ● Simulación Monte Carlo (1,000 iteraciones Pedigree)   │
                  │  ● Caracterización ReCiPe 2016 / IPCC 2021 GWP 100a     │
                  └─────────────────────────────────────────────────────────┘
```

---

## 👥 Gobernanza de Acceso (Los 3 Perfiles de Trabajo)

La plataforma cuenta con un esquema de autenticación estricto (Google Workspace o credenciales corporativas) sin conmutador al vuelo:

1. **Analista de Ciclo de Vida (`Carla Méndez` - `analyst_carla`)**:
   - **Creadora del Sistema Producto**: Modela en el lienzo, arrastra insumos, enlaza puertos técnicos de entrada/salida, define porcentajes de merma y publica notas técnicas en el reporte.
2. **Auditor Líder NOM-070 (`Josué Arentería` - `auditor_lead`)**:
   - **Verificador Oficial Tercero**: Examina balances de masa, audita las 18 cláusulas del checklist NOM-070/ISO, emite objeciones técnicas y **firma el dictamen con sello digital HMAC-SHA256**.
3. **Cliente / Productor Industrial (`Elena Ramírez` - `client_elena`)**:
   - **Empresa Auditada (*BioPack México*)**: Sube facturas de CFE y hojas de balance en la Bóveda de Documentos, responde observaciones del auditor para marcarlas como resueltas y consulta la declaración EPD final.

---

## 📦 Sistema Producto Oficial de Referencia (`SYS-PET-CIRCULAR-01`)

El sistema precargado en base de datos modela la cadena completa de 3 procesos interconectados:
- **Proceso 1 (Inyección de Preformas PET)**:
  - 3 Entradas: Granulado de PET virgen [GLO] (**Flujo Unitario ecoinvent**), Electricidad CFE 230kV y Agua desmineralizada.
  - 1 Flujo de Referencia: Preforma de PET cristal (1.000 kg).
  - 3 Salidas: Preforma de PET cristal, Scrap plástico de purga (**Residuo / Waste** para reciclaje interno en bucle cerrado) y Emisión CO₂ [Aire].
- **Proceso 2 (Soplado y Moldeo de Envases PET)**:
  - 3 Entradas: Preforma de PET cristal (**Flujo Unitario Conectado desde Inyección**), Aire a 40 bar y Electricidad termoformado CFE.
  - 1 Flujo de Referencia: Botella PET 500ml terminada (1.000 u).
  - 3 Salidas: Botella PET terminada, Merma plástica de recorte (**Residuo / Waste**) y Calor disipado [Aire].
- **Proceso 3 (Logística & Transporte Inter-Estatal)**:
  - 3 Entradas: Botella PET 500ml (**Flujo Unitario Conectado desde Soplado**), Diésel automotriz y Transporte camión 16-32t a 350 km.
  - 1 Flujo de Referencia: Botella distribuida en centro logístico (1.000 u).
  - 3 Salidas: Botella distribuida, Aceite lubricante residual (**Residuo / Waste**) y Emisiones diésel CO₂/NOx [Aire].

---

## 📂 Bóveda de Documentos & Base de Datos Multifuncional

- **Base de datos SQLite WAL**: `econode_studio/data/econode_documents.db`
- **Directorio de custodia física**: `econode_studio/data/documents/`
- **Formatos soportados**:
  - Scripts y volcados SQL (`.sql`)
  - Hojas de cálculo y balances (`.xlsx`, `.xls`, `.csv`)
  - Informes y facturas oficiales (`.pdf`)
  - Modelos y esquemas (`.json`)
  - Expedientes comprimidos (`.zip`)
- **Trazabilidad criptográfica**: Cálculo automático de hash **SHA-256** por cada archivo subido.

---

## 🚀 Exportaciones Industriales Disponibles

En la vista de Reporte Dinámico y en el Checklist NOM-070 se integran los exportadores estándar:
- **openLCA JSON-LD (`.zip`)**: Paquete completo de procesos e intercambios para openLCA v2.x.
- **ILCD / Sphera XML (`.zip`)**: Formato estandarizado de la Comisión Europea / GaBi.
- **SimaPro CSV (`.csv`)**: Matriz estructurada por secciones para importación directa en SimaPro.
- **Inventario LCI CSV (`.csv`)**: Consolidación tabulada de flujos tecnosféricos y elementales.
- **Expediente NOM-070 (`.zip`)**: Paquete normativo con dictamen oficial, firmas SHA-256 y evidencias.
- **PDF Oficial**: Impresión o guardado del reporte formal con maquetación de alta calidad.

---

## 🛠️ Ejecución & Pruebas Automatizadas

### Iniciar el Servidor Autónomo
```powershell
python econode_studio/server.py --port 8081
```

### Ejecutar Suite de Pruebas Automatizadas
```powershell
python econode_studio/tests/test_server_api.py
```
*Cobertura: 33 pruebas de integración con 100% de éxito.*

---
*ECONODE Studio (Tier 1) · Plataforma Acreditada NOM-070-SE-2024 / ISO 14044*
