@echo off
setlocal enabledelayedexpansion
echo --- INICIANDO ASISTENTE DEL AUDITOR ---

:: Intentar detectar que comando de Python funciona DE VERDAD
:: Comprobamos la version para asegurar que no es el acceso directo de la tienda
set PYTHON_CMD=
for %%P in (python python3 py) do (
    %%P --version >nul 2>nul
    if !errorlevel! equ 0 (
        set PYTHON_CMD=%%P
        goto :found
    )
)

:notfound
echo [ERROR] No se encuentra una instalacion real de Python.
echo Windows esta usando un "acceso directo vacio" a la Tienda (Microsoft Store).
echo.
echo POR FAVOR, HAZ ESTO PARA ARREGLARLO:
echo 1. Ve al menu Inicio y escribe: "Alias de ejecucion de aplicaciones"
echo 2. Busca "Instalador de Python" (python.exe) y DESACTIVALO (ponlo en OFF).
echo 3. Si no tienes Python instalado, bajalo de: https://www.python.org/downloads/
echo    (¡No olvides marcar "Add Python to PATH"!)
echo.
echo Una vez hecho, cierra esta ventana y abrela de nuevo.
pause
exit /b

:found
echo [INFO] Usando comando: %PYTHON_CMD%
echo Instalando dependencias necesarias...
%PYTHON_CMD% -m pip install --upgrade google-generativeai python-dotenv flask

echo Iniciando servidor de Webhooks...
%PYTHON_CMD% server.py

pause

