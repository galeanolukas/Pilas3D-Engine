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

REM Asistente de IA opcional (Ollama local): descarga el binario una
REM sola vez; el modelo (~1 GB) se baja la primera vez que se usa
REM pilas.ayuda("..."). Si falla, el motor funciona igual sin IA.
where ollama >nul 2>nul
if errorlevel 1 (
    if not exist pilas3d\_vendor\ollama mkdir pilas3d\_vendor\ollama
    echo.
    echo Descargando Ollama (asistente de IA)...
    powershell -NoProfile -Command ^
      "try { Invoke-WebRequest 'https://ollama.com/download/ollama-windows-amd64.zip' -OutFile 'pilas3d\_vendor\ollama\ollama.zip'; Expand-Archive 'pilas3d\_vendor\ollama\ollama.zip' 'pilas3d\_vendor\ollama' -Force; Remove-Item 'pilas3d\_vendor\ollama\ollama.zip' } catch { Write-Host 'Aviso: no se pudo descargar Ollama' }"
)

echo.
echo Listo. Para probar:
echo   .venv\Scripts\python.exe ejemplos\hola_cubo.py
echo   .venv\Scripts\python.exe ejemplos\minecraft.py
echo   .venv\Scripts\pilas3d.exe          REM consola interactiva
pause
