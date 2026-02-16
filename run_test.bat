@echo off
setlocal enabledelayedexpansion
echo --- EJECUTANDO PRUEBA DE LEAD ---

:: Detectar comando de Python DE VERDAD
set PYTHON_CMD=
for %%P in (python python3 py) do (
    %%P --version >nul 2>nul
    if !errorlevel! equ 0 (
        set PYTHON_CMD=%%P
        goto :found
    )
)

:notfound
echo [ERROR] No se encuentra Python. 
echo Si has instalado Python hace un momento, recuerda cerrar esta ventana y abrirla de nuevo.
echo Si sigue fallando, revisa el archivo run_server.bat para ver instrucciones de ayuda.
pause
exit /b

:found
echo [INFO] Simulando envío de lead...
%PYTHON_CMD% test_webhook.py

pause
