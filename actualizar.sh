#!/usr/bin/env bash
# Actualiza pilas3d: baja los últimos cambios (con tags de versión)
# y reinstala dependencias.
set -e
cd "$(dirname "$0")"

git pull
# --force: los tags pueden haberse movido (reescritura de historia)
git fetch --tags --force

if [ -d .venv ]; then
    .venv/bin/pip install -q -r requirements.txt
    .venv/bin/pip install -q -e .
fi

echo ""
echo "Actualizado a la version $(cat VERSION)"
echo "Ultimo tag: $(git describe --tags --abbrev=0 2>/dev/null || echo 'ninguno')"
