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
# sola vez. Si falla, el motor funciona igual sin IA.
if ! command -v ollama >/dev/null && \
   [ ! -f pilas3d/_vendor/ollama/ollama ]; then
    if command -v curl >/dev/null; then
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
fi

# Modelo del asistente: se puede elegir ahora (si hay terminal) o
# despues con `python -m pilas3d.ia <modelo>` / PILAS3D_IA_MODELO.
OLLAMA_BIN=$(command -v ollama || echo "pilas3d/_vendor/ollama/ollama")
if [ -t 0 ] && [ -x "$OLLAMA_BIN" ]; then
    echo ""
    echo "Modelo del asistente de IA (tambien se baja solo al usarlo):"
    echo "  1) qwen2.5-coder:0.5b  (~500 MB, recomendado, CPU)"
    echo "  2) qwen2.5-coder:1.5b  (~1 GB, CPU)"
    echo "  3) qwen2.5-coder:7b    (~4.7 GB, con GPU)"
    echo "  4) ninguno ahora"
    read -p "Elegi [1]: " op
    case "$op" in
        2) MODELO=qwen2.5-coder:1.5b ;;
        3) MODELO=qwen2.5-coder:7b ;;
        4) MODELO= ;;
        *) MODELO=qwen2.5-coder:0.5b ;;
    esac
    if [ -n "$MODELO" ]; then
        "$OLLAMA_BIN" serve >/dev/null 2>&1 & SRV=$!
        for i in $(seq 1 50); do
            curl -s http://localhost:11434/api/tags >/dev/null && break
            sleep 0.2
        done
        "$OLLAMA_BIN" pull "$MODELO" \
        && echo "Modelo $MODELO instalado." \
        || echo "Aviso: no se pudo bajar el modelo (se bajara al usarlo)."
        kill $SRV 2>/dev/null
        # El motor recuerda el modelo elegido (~/.pilas3d/config.json);
        # PILAS3D_IA_MODELO lo pisa si está definida.
        .venv/bin/python -c \
            "from pilas3d import config; config.guardar('ia_modelo', '$MODELO')" \
            2>/dev/null || true
    fi
fi

# Voz del asistente (Piper, ~20 MB): NPCs que hablan en español.
if [ -t 0 ]; then
    echo ""
    read -p "Descargar voces en español (mujer+hombre) para los NPC? [s/N]: " VOZ_OP
    case "$VOZ_OP" in
        s|S|y|Y)
            .venv/bin/python -c \
                "from pilas3d.ia import voz; voz.descargar_voces()" \
                && echo "Voces instaladas." \
                || echo "Aviso: no se pudieron bajar las voces." ;;
    esac
fi

echo ""
echo "Listo. Para probar:"
echo "  .venv/bin/python ejemplos/hola_cubo.py"
echo "  .venv/bin/python ejemplos/minecraft.py"
echo "  .venv/bin/pilas3d          # consola interactiva"
