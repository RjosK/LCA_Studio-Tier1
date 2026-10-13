# 🚀 Guía Oficial: Despliegue de ECONODE Studio en Supabase + Vercel (100% Free Tier $0/mes)

Esta guía detalla el proceso paso a paso para desplegar **ECONODE Studio** en la nube con arquitectura de alta disponibilidad, coste cero ($0/mes) y preservando los **26,537 procesos industriales** y **14,211 flujos de inventario** de ecoinvent 3.12.

---

## 📊 Arquitectura en la Nube ($0/mes)

| Componente | Plataforma | Capacidad Gratuita | Uso de ECONODE Studio |
| :--- | :--- | :--- | :--- |
| **Frontend CDN** | **Vercel** (Hobby) | Ancho de banda ilimitado / Edge global | Interfaz visual del lienzo, explorador LCI, auditoría y reportes |
| **Backend REST API** | **Vercel Serverless** | 100,000 ejecuciones/mes | Funciones Python Serverless (`api/index.py`) de respuesta ultrarrápida |
| **Base de Datos Relacional** | **Supabase PostgreSQL** | 500 MB almacenamiento | **~130 MB** (26,537 procesos, 14,211 flujos, 339,067 intercambios, usuarios y proyectos) |
| **Bóveda de Evidencias (Archivos)** | **Supabase Storage** | 1,000 MB (1 GB) almacenamiento | PDFs, reportes, hojas Excel, certificados y evidencias de auditoría |

---

## 🛠️ Paso 1: Crear y Configurar tu Proyecto en Supabase

1. Entra a [https://supabase.com](https://supabase.com) e inicia sesión (o crea cuenta gratuita con GitHub).
2. Haz clic en **"New Project"**:
   - **Name**: `econode-studio` (o el nombre que prefieras).
   - **Database Password**: Genera una contraseña segura y **guárdala** (la necesitarás en el paso 2).
   - **Region**: Selecciona la más cercana (ej. `East US - North Virginia` o `West US`).
   - **Pricing Plan**: Free ($0/month).
   - Haz clic en **"Create new project"** (tarda ~1-2 minutos en aprovisionarse).
3. **Crear el Bucket de Almacenamiento (Bóveda)**:
   - En el menú lateral izquierdo, entra a **Storage** $\rightarrow$ **Buckets**.
   - Haz clic en **"New bucket"**.
   - Nombre del bucket: `econode-vault`.
   - Marca la casilla **"Public bucket"** (para descarga directa de evidencias y reportes).
   - Guarda el bucket.
4. **Obtener tu Cadena de Conexión**:
   - En el menú lateral, ve a **Project Settings** (ícono de engrane) $\rightarrow$ **Database**.
   - En la sección **Connection parameters**, busca **Connection string** $\rightarrow$ pestaña **URI**.
   - Selecciona el modo **Transaction** o **Session** (puerto `6543`, recomendado para Serverless):
     ```text
     postgresql://postgres.[TU_PROYECTO_REF]:[TU_CONTRASEÑA]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
   - *Nota: Reemplaza `[TU_CONTRASEÑA]` con la clave que creaste en el paso 2.*

---

## ⚡ Paso 2: Migrar Esquema y los 26,537 Materiales en 1 Solo Comando

Hemos preparado el script automatizado [`supabase/migrate_to_supabase.py`](file:///c:/Users/Josue/Documents/Espacio/ECONODE/supabase/migrate_to_supabase.py) que se conecta directamente a tu base de datos Supabase y transmite los esquemas y datos en menos de 60 segundos:

Abre tu terminal en la carpeta del proyecto y ejecuta:

```powershell
python supabase/migrate_to_supabase.py "postgresql://postgres.[TU_PROYECTO_REF]:[TU_CONTRASEÑA]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
```

### ¿Qué hace este comando automáticamente?
1. **Paso 1**: Ejecuta [`supabase/01_schema.sql`](file:///c:/Users/Josue/Documents/Espacio/ECONODE/supabase/01_schema.sql), creando las 17 tablas relacionales, vistas de compatibilidad (`processes`, `flows`, `categories`, `exchanges`) y cuentas demo de analista, auditor y cliente.
2. **Paso 2**: Importa las **786 categorías industriales**.
3. **Paso 3**: Importa los **14,211 flujos de inventario** de ciclo de vida.
4. **Paso 4**: Importa los **26,537 procesos unitarios** ecoinvent 3.12 y propios.
5. **Paso 5**: Importa los **339,067 intercambios clave** de tecnósfera y producción.
6. **Verificación final**: Muestra el conteo exacto de filas en pantalla confirmando el 100% de éxito.

---

## 🌐 Paso 3: Desplegar en Vercel

### Opción A: Despliegue con GitHub (Recomendado)
1. Sube tu código a un repositorio en GitHub (`git add .`, `git commit -m "Deploy Supabase + Vercel"`, `git push`).
2. Entra a [https://vercel.com](https://vercel.com) e inicia sesión.
3. Haz clic en **"Add New..."** $\rightarrow$ **"Project"**.
4. Importa tu repositorio de GitHub.
5. En la sección **Environment Variables**, agrega las siguientes variables:
   - `DATABASE_URL`: `postgresql://postgres.[TU_PROYECTO_REF]:[TU_CONTRASEÑA]@aws-0-[REGION].pooler.supabase.com:6543/postgres`
   - `SUPABASE_URL`: `https://[TU_PROYECTO_REF].supabase.co`
   - `SUPABASE_ANON_KEY`: *(Tu anon key de Supabase -> Project Settings -> API)*
   - `SECRET_KEY`: `econode_jwt_super_secret_key_tier1_2026`
   - `STORAGE_BACKEND`: `supabase`
6. Haz clic en **"Deploy"**. En ~45 segundos tu aplicación estará activa en `https://tu-proyecto.vercel.app`.

### Opción B: Despliegue Directo con Vercel CLI
Si tienes instalado Vercel CLI en tu computadora:
```powershell
npm i -g vercel
vercel
```
Sigue las instrucciones en pantalla e ingresa las variables de entorno en la configuración del proyecto.

---

## 🔒 Usuarios Demo Disponibles en la Nube

Una vez desplegado, puedes iniciar sesión inmediatamente con cualquiera de las cuentas preconfiguradas:

| Perfil | Nombre | Correo | Contraseña |
| :--- | :--- | :--- | :--- |
| **Analista Senior** | Carla Méndez | `carla.mendez@econode.io` | `demo1234` |
| **Auditor Líder NOM-070** | Josué Arentería | `josuearenteriaz09@gmail.com` | `demo1234` |
| **Directora de Sostenibilidad** | Elena Ramírez | `elena.ramirez@biopack-mexico.com` | `demo1234` |

---

## 💻 Desarrollo Offline / Local sigue funcionando

Tu entorno local en [`iniciar_econode_studio.bat`](file:///c:/Users/Josue/Documents/Espacio/ECONODE/iniciar_econode_studio.bat) **sigue funcionando al 100% sin conexión a internet**:
- Si no configuras `DATABASE_URL`, el sistema utiliza automáticamente las bases SQLite locales (`ecoinvent_312.db`, `lcia_engine.db`, `econode_auth.db`).
- Si configuras `DATABASE_URL`, el sistema se sincroniza en tiempo real con Supabase en la nube.

