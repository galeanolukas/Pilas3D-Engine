# -*- encoding: utf-8 -*-
"""Descarga o cambia el modelo del asistente::

    python -m pilas3d.ia                      # baja el modelo default
    python -m pilas3d.ia qwen2.5-coder:7b     # baja otro modelo
    python -m pilas3d.ia --lista              # catálogo sugerido

El modelo elegido se usa poniendo PILAS3D_IA_MODELO=<modelo>.
"""

import sys

from pilas3d.ia.servidor import (MODELO, MODELOS, asegurar_servidor,
                                 asegurar_modelo)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if '--lista' in sys.argv or '-l' in sys.argv:
        print("Modelos sugeridos (todos Qwen code):")
        for nombre, desc in MODELOS.items():
            marca = '  <-- default' if nombre == MODELO else ''
            print("  %-22s %s%s" % (nombre, desc, marca))
        return 0
    modelo = args[0] if args else MODELO
    asegurar_servidor()
    asegurar_modelo(modelo)
    print("Listo: '%s' descargado." % modelo)
    if modelo != MODELO:
        print("Para usarlo: PILAS3D_IA_MODELO=%s" % modelo)
    return 0


if __name__ == '__main__':
    sys.exit(main())
