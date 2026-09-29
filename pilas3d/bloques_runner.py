# -*- encoding: utf-8 -*-
"""Corre el código de bloques en un proceso nuevo (su ventana propia).

``pilas3d-bloques`` no abre ventana: solo sirve la página Blockly.
Cuando la página manda ``POST /codigo``, el puente lanza este runner
como subproceso — ahí sí se crea la ventana de pilas3d y se ejecuta
el código generado. "Detener" lo mata.

    python bloques_runner.py /tmp/bloques_XXXX.py
"""

import os
import sys
import traceback

import pilas3d


def main(ruta):
    pilas = pilas3d.iniciar(
        titulo="pilas3d - bloques",
        sin_ventana=bool(os.environ.get('PILAS3D_SIN_VENTANA')))
    pilas.escena.fondo = pilas.colores.gris_oscuro
    ns = {'pilas': pilas, 'pilas3d': pilas3d, '__file__': ruta}
    try:
        codigo = open(ruta, encoding='utf-8').read()
        exec(compile(codigo, '<bloques>', 'exec'), ns)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    pilas.ejecutar()


if __name__ == '__main__':
    main(sys.argv[1])
