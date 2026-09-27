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

echo ""
echo "Listo. Para probar:"
echo "  .venv/bin/python ejemplos/hola_cubo.py"
echo "  .venv/bin/python ejemplos/minecraft.py"
echo "  .venv/bin/pilas3d          # consola interactiva"
