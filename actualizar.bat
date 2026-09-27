@echo off
REM Actualiza pilas3d: baja los ultimos cambios (con tags de version)
REM y reinstala dependencias.
cd /d "%~dp0"

git pull --tags

if exist .venv (
    call .venv\Scripts\pip.exe install -q -r requirements.txt
    call .venv\Scripts\pip.exe install -q -e .
)

echo.
set /p VER=<VERSION
echo Actualizado a la version %VER%
for /f %%i in ('git describe --tags --abbrev=0 2^>nul') do echo Ultimo tag: %%i
pause
