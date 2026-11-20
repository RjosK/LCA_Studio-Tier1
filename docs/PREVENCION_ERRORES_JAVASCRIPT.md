# Protocolo de Prevención de Errores de Sintaxis en JavaScript y Bloqueo de UI

Este documento describe la causa raíz de los errores recurrentes donde los botones de la interfaz dejan de responder o impiden iniciar sesión, junto con los controles técnicos y el flujo de trabajo obligatorio para evitar que vuelva a ocurrir.

---

## 1. Diagnóstico del Error Recurrente

### ¿Qué ocurre?
El usuario abre ECONODE en su navegador y observa que:
- Los botones de navegación ("Ingresar al Studio", "Iniciar Sesión", "Registrarse") no responden al clic.
- Los botones de exportación, cambio de vistas y modales están inactivos.
- La consola del navegador muestra un error del tipo:
  ```text
  Uncaught SyntaxError: Unexpected token '<' (o Unexpected token ')') en app.js
  ```

### ¿Por qué ocurre?
En JavaScript, los navegadores interpretan los archivos `.js` en dos fases:
1. **Fase de Compilación/Parseo**: El motor de JS valida la sintaxis completa del script. Si encuentra cualquier error de sintaxis (un paréntesis huérfano, un tag HTML introducido por error o una función sin cerrar), **aborta de inmediato** la ejecución de todo el archivo.
2. **Fase de Ejecución**: En esta fase se ejecutan las funciones, se inicializa `window.EconodeApp` y se asignan los escuchadores de eventos (`addEventListener`) a los botones.

Si ocurre un error en la fase 1, la fase 2 **nunca se ejecuta**. En consecuencia, ningún botón recibe su escuchador de eventos y la interfaz queda congelada.

### ¿Por qué se volvía recurrente al editar código con agentes?
`public/js/app.js` es un archivo monolítico de aproximadamente 15,000 líneas. Al realizar reemplazos de texto (`edit_file`) con cadenas de coincidencia cortas o ambiguas:
- Se emparejaba un bloque repetido en otra sección del archivo.
- Se eliminaban inadvertidamente cientos de líneas intermedias (como cierres de funciones o modales completos).
- No existía una prueba automatizada que verificara la sintaxis de JavaScript antes del commit.

---

## 2. Medidas Implementadas para Solución Inmediata

1. **Restauración íntegra de `public/js/app.js`**:
   - Se eliminaron los fragmentos de código truncados y los tags HTML accidentales.
   - La sintaxis de `app.js` y de `i18n.js` se verificó formalmente mediante `node --check`.

2. **Acceso directo en Modo Demostración**:
   - En `public/index.html` (vista `#viewLogin`), se incorporó un botón de acceso directo para analistas (`Carla Méndez`), permitiendo entrar al Studio con 1 solo clic incluso si Google Identity Services está desconectado o bloqueado en `localhost`.
   - En `econode_studio/server.py`, el endpoint `/api/auth/login` ahora acepta autenticación por rol en entornos locales sin exigir contraseña si se solicita acceso de prueba.

3. **Salvaguarda de eventos inline**:
   - Botones críticos como exportación Word (`#btnExportReportDocx` y `#btnExportDocx`) conservan atributos `onclick="window.EconodeApp && window.EconodeApp.exportDocx()"` como fallback directo.

---

## 3. Protocolo Obligatorio para Desarrolladores y Agentes

Para cualquier cambio futuro en `public/js/app.js` o en cualquier archivo JavaScript del proyecto:

### Regla 1: Verificación de Sintaxis Obligatoria
Antes de hacer commit, SIEMPRE se debe ejecutar:
```powershell
node --check public/js/app.js
node --check public/js/i18n.js
```
Si el comando arroja cualquier código de salida distinto de 0 o cualquier advertencia de sintaxis, **está estrictamente prohibido hacer commit o push**.

### Regla 2: Inspección de Volumen de Diff
Antes de hacer commit, verificar la magnitud del cambio:
```powershell
git diff --stat public/js/app.js
```
Si una modificación destinada a agregar unas pocas líneas reporta cientos de líneas eliminadas (`-300 lines`, `-500 lines`), se debe inspeccionar con `git diff` antes de proceder para confirmar que no se haya truncado código adyacente.

### Regla 3: Suite Automatizada de Integridad
El archivo de pruebas [tests/test_iso_acv_report.py](file:///C:/Users/Josue/Documents/Espacio/ECONODE/tests/test_iso_acv_report.py) incluye la prueba unitaria:
```python
def test_javascript_syntax_integrity(self):
    ...
```
Esta prueba invoca automáticamente `node --check` sobre todos los scripts de `public/js/`. Si existe el más mínimo error de sintaxis, la prueba falla inmediatamente impidiendo el pase a producción.

---

## 4. Guía Rápida de Recuperación si la UI se Bloquea

Si en algún momento los botones dejan de responder durante el desarrollo:

1. **Abrir la consola del navegador** (F12 -> Consola) y buscar errores en rojo con el número de línea exacto de `app.js`.
2. **Ejecutar en la terminal**:
   ```powershell
   node --check public/js/app.js
   ```
   Node.js indicará el archivo, número de línea y carácter exacto donde se rompió la sintaxis.
3. Si el archivo fue dañado por un reemplazo defectuoso, revertir al último commit funcional:
   ```powershell
   git checkout HEAD -- public/js/app.js
   ```
4. Volver a aplicar el cambio asegurando al menos 5 líneas de contexto único en los bloques antes y después del reemplazo.
