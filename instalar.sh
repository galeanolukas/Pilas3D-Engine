#!/usr/bin/env bash
# Instalador de pilas3d para Linux/macOS.
# Crea un entorno virtual .venv, instala dependencias y deja
# disponible el comando pilas3d (consola interactiva).
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
    echo "ERROR: no se encontro python3. Instalalo primero."
    exit 1
fi

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# Asistente de IA opcional (Ollama local): descarga el binario una
# sola vez; el modelo (~1 GB) se baja la primera vez que se usa
# pilas.ayuda("..."). Si falla, el motor funciona igual sin IA.
if command -v curl >/dev/null && ! command -v ollama >/dev/null; then
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    case "$(uname -m)" in aarch64|arm64) ARCH=arm64 ;; *) ARCH=amd64 ;; esac
    mkdir -p pilas3d/_vendor/ollama
    echo ""
    echo "Descargando Ollama (asistente de IA, ~200 MB)..."
    curl -L "https://ollama.com/download/ollama-${OS}-${ARCH}" \
         -o pilas3d/_vendor/ollama/ollama \
    && chmod +x pilas3d/_vendor/ollama/ollama \
    || echo "Aviso: no se pudo descargar Ollama; " \
            "pilas.ayuda(\"...\") no estara disponible."
fi

echo ""
echo "Listo. Para probar:"
echo "  .venv/bin/python ejemplos/hola_cubo.py"
echo "  .venv/bin/python ejemplos/minecraft.py"
echo "  .venv/bin/pilas3d          # consola interactiva"
