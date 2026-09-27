# -*- encoding: utf-8 -*-
"""Gestiona el modelo del asistente::

    python -m pilas3d.ia                          # baja el modelo default
    python -m pilas3d.ia qwen2.5-coder:7b         # baja otro modelo
    python -m pilas3d.ia --lista                  # catálogo sugerido
    python -m pilas3d.ia --instalados             # los que ya bajaste
    python -m pilas3d.ia borrar <modelo>          # elimina un modelo

El modelo elegido se usa poniendo PILAS3D_IA_MODELO=<modelo>.
"""

import sys

from pilas3d.ia.servidor import (MODELO, MODELOS, asegurar_servidor,
                                 asegurar_modelo, borrar_modelo,
                                 listar_modelos)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if '--lista' in sys.argv or '-l' in sys.argv:
        print("Modelos sugeridos (todos Qwen code):")
        for nombre, desc in MODELOS.items():
            marca = '  <-- default' if nombre == MODELO else ''
            print("  %-22s %s%s" % (nombre, desc, marca))
        return 0

    asegurar_servidor()

    if '--instalados' in sys.argv or '-i' in sys.argv:
        instalados = listar_modelos()
        if not instalados:
            print("No hay modelos descargados todavía.")
        for m in instalados:
            marca = '  <-- en uso' if m.split(':')[0] == \
                MODELO.split(':')[0] else ''
            print("  %s%s" % (m, marca))
        return 0

    if args and args[0] == 'borrar':
        if len(args) < 2:
            print("Uso: python -m pilas3d.ia borrar <modelo>")
            return 1
        modelo = args[1]
        if borrar_modelo(modelo):
            print("Modelo '%s' eliminado." % modelo)
            return 0
        print("No se encontró el modelo '%s'." % modelo)
        print("Instalados: %s" % ', '.join(listar_modelos()))
        return 1

    modelo = args[0] if args else MODELO
    asegurar_modelo(modelo)
    print("Listo: '%s' descargado." % modelo)
    if modelo != MODELO:
        print("Para usarlo: PILAS3D_IA_MODELO=%s" % modelo)
    return 0


if __name__ == '__main__':
    sys.exit(main())
