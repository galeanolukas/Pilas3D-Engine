# -*- encoding: utf-8 -*-
"""pilas3d-bloques: programación por bloques sobre el motor.

Abre una ventana de pilas3d y una página web con Blockly (estilo
Scratch): los bloques generan código Python real que se ejecuta en la
escena vía :mod:`pilas3d.puente`.

    pilas3d-bloques            # comando (pip install -e .)

    >>> import pilas3d.bloques
    >>> pilas3d.bloques.main()          # desde Python/IPython
"""

import os
import webbrowser

import pilas3d
from pilas3d.puente import PUERTO, PuenteBloques

DIR_WEB = os.path.join(os.path.dirname(__file__), 'bloques_web')


def main(ejecutar=True, abrir_navegador=True):
    """Inicia pilas, levanta el puente HTTP y abre la página de
    bloques en el navegador. Devuelve ``(pilas, url)``."""
    pilas = pilas3d.iniciar(titulo="pilas3d - bloques")
    pilas.escena.fondo = pilas.colores.gris_oscuro
    pilas.luces.direccional.ambiente = 0.6

    puente = PuenteBloques(pilas, DIR_WEB)
    puente.enganchar()                    # drena la cola cada frame
    url = puente.iniciar(PUERTO)
    pilas.puente_bloques = puente         # acceso desde consola/tests

    print("pilas3d-bloques listo en", url)
    print("los bloques generan Python y se ejecutan en esta ventana")

    if abrir_navegador:
        webbrowser.open(url)
    if ejecutar:
        try:
            pilas.ejecutar()
        finally:
            puente.detener()
    return pilas, url


def cli():
    """Punto de entrada del comando ``pilas3d-bloques``."""
    main()
