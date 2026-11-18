# Recursos para el Cruce de Versiones de ecoinvent (3.12 <-> 3.11) y Multi-Base de Datos

Este directorio centraliza la documentacion tecnica, esquemas relacionales, consultas SQL de alto rendimiento y guias de arquitectura para la correspondencia (*matching*), validacion de compatibilidad y conmutacion en caliente (*hot-swap*) entre versiones de **ecoinvent (3.12 y 3.11)** y bases de datos complementarias (**SimaPro, OEKOBAUDAT, GLAD Network, Base Carbone ADEME y Procesos Propios**) en el ecosistema **ECONODE Studio**.

---

## Documentos en este Directorio

* [**`ECOINVENT_ESQUEMA_Y_CRUCE_VERSIONES.md`**](file:///C:/Users/Josue/Documents/Espacio/ECONODE/recursos_cruce_versiones/ECOINVENT_ESQUEMA_Y_CRUCE_VERSIONES.md):
  * **Esquema relacional unificado**: Modelado de `TBL_PROCESSES`, `TBL_LOCATIONS`, `TBL_FLOWS`, `TBL_EXCHANGES` y tablas cloud `lci_processes`, `lci_processes_311`, `lci_flows`, `lci_flows_311`.
  * **Regla canonica de identidad**: Identificacion biunivoca mediante `(NAME, LOCATION)` evitando colisiones de UUIDs volatiles.
  * **Balance estadistico oficial**: 24,032 procesos 100% coincidentes, 2,501 procesos nuevos en 3.12, 1,380 procesos especificos de 3.11 y 98.96% de compatibilidad en flujos biosfericos.
  * **Consultas SQL con `ATTACH DATABASE` y PostgreSQL Multi-Tabla**: Algoritmos optimizados para consultas en tiempo real (< 3 ms) sin producto cartesiano multigeografico.
  * **Motor Python `VersionMatcherAdapter`**: Arquitectura del validador de demanda, sugerencias de alternativas regionales, sustitucion interactiva y creacion automatizada de sistemas clonados.
  * **Hot-Swap matricial y API REST**: Especificacion tecnica de los endpoints `/api/version/databases`, `/api/version/match-system`, `/api/version/search-target` y `/api/systems/convert-version`.
  * **Protocolo de Interfaz Apple HIG**: Guia del sistema de alertas semaforicas (Verde, Amarillo, Rojo), modal de confirmacion en Canvas e integracion en el LCI Explorer.

---

## Bases de Datos Disponibles (Entorno Dual Cloud y Local)

| Base de Datos / Version | Sistema / Modelo | Procesos Activos | Flujos Totales | Ubicacion Cloud (Supabase) | Ubicacion Local (SQLite) |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **ecoinvent 3.12** | Cutoff Unit (U) | 26,537 | 14,211 | `lci_processes`, `lci_flows` | `ecoinvent/ecoinvent_312.db` |
| **ecoinvent 3.11** | Cutoff Unit (U) | 25,412 | 14,051 | `lci_processes_311`, `lci_flows_311` | `ecoinvent/ecoinvent_311.db` |
| **SimaPro 9.5** | CSV Importado / LCI | Dinamico | Dinamico | `custom_processes`, `custom_flows` | `ecoinvent/ecoinvent_312.db` |
| **OEKOBAUDAT** | Construccion y EPD | 1,480 | -- | `catalog_processes (oekobaudat_de)` | Cache SQLite local |
| **GLAD Network** | UNEP Global LCA | 3,200 | -- | `catalog_processes (glad_network)` | Cache SQLite local |
| **Base Carbone ADEME** | Factores Franceses | 2,100 | -- | `catalog_processes (ademe_base_carbone)`| Cache SQLite local |

Ambas bases cuentan con indices B-Tree creados en `(name, location)`, `code` e identificadores unicos para garantizar respuestas en submilisegundos en operaciones de union cruzada (*cross-join*).

---

## Resumen del Cruce Estadistico

```
  ecoinvent 3.12 (26,537 procesos)                ecoinvent 3.11 (25,412 procesos)
  +---------------------------------+            +---------------------------------+
  | 2,501 Exclusivos v3.12          |            | 1,380 Exclusivos v3.11          |
  | (Nuevas redes, quimicos, etc.)  |            | (Reestructurados en v3.12)      |
  +---------------------------------+------------+---------------------------------+
  |                 24,032 PROCESOS COINCIDENTES EXACTOS 1-A-1                     |
  |              (Mismo Nombre + Misma Geografia · 90.57% Cobertura)               |
  +--------------------------------------------------------------------------------+
```

* **Flujos coincidentes por `REF_ID` o Nombre**: 13,676 flujos coincidentes de 14,210 (96.24% de correspondencia total, 98.96% en flujos biosfericos activos).
* **Latencia de resolucion SQL**: < 2.5 ms por proceso verificado.
* **Tiempo de conmutacion en caliente (*hot-swap*)**: < 15 ms en memoria al duplicar y recargar el lienzo.

---

## Verificacion y Pruebas

Para ejecutar la suite de pruebas del motor de cruce de versiones:

```bash
# 1. Pruebas Unitarias del Adaptador de Versiones
python -m unittest tests/test_version_matcher_adapter.py

# 2. Pruebas del Modal y Endpoints de Conversion
python -m unittest tests/test_system_info_modal.py
```
