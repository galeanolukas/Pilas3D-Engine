@echo off
REM Instalador de pilas3d para Windows.
REM Crea un entorno virtual .venv, instala dependencias y deja
REM disponible el comando pilas3d (consola interactiva).
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: no se encontro python. Instalalo desde python.org
    echo marcando "Add python.exe to PATH".
    pause
    exit /b 1
)

python -m venv .venv
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\pip.exe install -r requirements.txt
call .venv\Scripts\pip.exe install -e .

echo.
echo Listo. Para probar:
echo   .venv\Scripts\python.exe ejemplos\hola_cubo.py
echo   .venv\Scripts\python.exe ejemplos\minecraft.py
echo   .venv\Scripts\pilas3d.exe          REM consola interactiva
pause
