# -*- encoding: utf-8 -*-
"""Configuración persistente de pilas3d.

Un pequeño JSON en ``~/.pilas3d/config.json`` (o el archivo indicado
por ``PILAS3D_CONFIG``) donde el motor recuerda decisiones del
usuario — por ahora el modelo del asistente de IA elegido al
instalar::

    >>> config.leer('ia_modelo')
    'qwen2.5-coder:1.5b'
    >>> config.guardar('ia_modelo', 'smollm2:135m')
"""

import json
import os


def _archivo():
    return os.environ.get('PILAS3D_CONFIG') or os.path.join(
        os.path.expanduser('~'), '.pilas3d', 'config.json')


def leer(clave, defecto=None):
    """Lee una clave de la config; ``defecto`` si falta el archivo."""
    try:
        with open(_archivo(), encoding='utf-8') as f:
            return json.load(f).get(clave, defecto)
    except Exception:
        return defecto


def guardar(clave, valor):
    """Persiste ``clave = valor`` sin tocar el resto de la config."""
    datos = {}
    try:
        with open(_archivo(), encoding='utf-8') as f:
            datos = json.load(f)
    except Exception:
        pass
    datos[clave] = valor
    ruta = _archivo()
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    except OSError:
        pass        # sin HOME escribible: la config es opcional
    return valor
