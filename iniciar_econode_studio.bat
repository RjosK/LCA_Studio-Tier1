@echo off
title ECONODE Studio (Tier 1) - Modelado ACV y Auditoria NOM-070
echo ============================================================
echo   Iniciando ECONODE Studio (Tier 1: Modelado y Auditoria)
echo   Puerto: 8081 (Independiente del motor legado 8080)
echo   Base de Datos: ecoinvent 3.12 (26,533 procesos)
echo ============================================================
echo.

REM Liberar puerto 8081 si habia una instancia previa colgada en Windows
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8081" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Iniciar navegador automaticamente tras 1 segundo
start "" http://localhost:8081

REM Ejecutar servidor en el entorno virtual
if exist .\venv\Scripts\python.exe (
    .\venv\Scripts\python.exe econode_studio/server.py --port 8081
) else (
    python econode_studio/server.py --port 8081
)

pause

