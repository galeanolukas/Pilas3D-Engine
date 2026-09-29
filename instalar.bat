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
REM sola vez. Si falla, el motor funciona igual sin IA.
set OLLAMA_BIN=
where ollama >nul 2>nul && set OLLAMA_BIN=ollama
if not defined OLLAMA_BIN (
    if exist pilas3d\_vendor\ollama\ollama.exe (
        set OLLAMA_BIN=pilas3d\_vendor\ollama\ollama.exe
    ) else (
        if not exist pilas3d\_vendor\ollama mkdir pilas3d\_vendor\ollama
        echo.
        echo Descargando Ollama (asistente de IA)...
        powershell -NoProfile -Command ^
          "try { Invoke-WebRequest 'https://ollama.com/download/ollama-windows-amd64.zip' -OutFile 'pilas3d\_vendor\ollama\ollama.zip'; Expand-Archive 'pilas3d\_vendor\ollama\ollama.zip' 'pilas3d\_vendor\ollama' -Force; Remove-Item 'pilas3d\_vendor\ollama\ollama.zip' } catch { Write-Host 'Aviso: no se pudo descargar Ollama' }"
        if exist pilas3d\_vendor\ollama\ollama.exe set OLLAMA_BIN=pilas3d\_vendor\ollama\ollama.exe
    )
)

REM Modelo del asistente: elegible ahora o despues con
REM `python -m pilas3d.ia <modelo>` / PILAS3D_IA_MODELO.
if defined OLLAMA_BIN (
    echo.
    echo Modelo del asistente de IA (tambien se baja solo al usarlo):
    echo   1) qwen2.5-coder:0.5b  (~500 MB, recomendado, CPU)
    echo   2) qwen2.5-coder:1.5b  (~1 GB, CPU)
    echo   3) qwen2.5-coder:7b    (~4.7 GB, con GPU)
    echo   4) ninguno ahora
    set /p IA_OP="Elegi [1]: "
    if "%IA_OP%"=="" set IA_OP=1
    set IA_MODELO=qwen2.5-coder:0.5b
    if "%IA_OP%"=="2" set IA_MODELO=qwen2.5-coder:1.5b
    if "%IA_OP%"=="3" set IA_MODELO=qwen2.5-coder:7b
    if "%IA_OP%"=="4" set IA_MODELO=
    if defined IA_MODELO (
        powershell -NoProfile -Command ^
          "try { Invoke-RestMethod 'http://localhost:11434/api/tags' | Out-Null; exit 0 } catch { exit 1 }"
        if errorlevel 1 (
            start /b "" %OLLAMA_BIN% serve
            timeout /t 3 /nobreak >nul
            %OLLAMA_BIN% pull %IA_MODELO% || echo Aviso: no se pudo bajar el modelo.
            taskkill /f /im ollama.exe >nul 2>nul
        ) else (
            %OLLAMA_BIN% pull %IA_MODELO% || echo Aviso: no se pudo bajar el modelo.
        )
        REM El motor recuerda el modelo elegido (~/.pilas3d/config.json)
        .venv\Scripts\python.exe -c "from pilas3d import config; config.guardar('ia_modelo', '%IA_MODELO%')" 2>nul
    )
)

REM Voces del asistente (Piper, ~20 MB): NPCs que hablan en espanol.
echo.
set /p VOZ_OP="Descargar voces en espanol (mujer+hombre) para los NPC? [s/N]: "
if /i "%VOZ_OP%"=="s" (
    .venv\Scripts\python.exe -c "from pilas3d.ia import voz; voz.descargar_voces()" || echo Aviso: no se pudieron bajar las voces.
)

echo.
echo Listo. Para probar:
echo   .venv\Scripts\python.exe ejemplos\hola_cubo.py
echo   .venv\Scripts\python.exe ejemplos\minecraft.py
echo   .venv\Scripts\pilas3d.exe          REM consola interactiva
pause
