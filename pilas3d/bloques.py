# -*- encoding: utf-8 -*-
"""pilas3d-bloques: programación por bloques sobre el motor.

Arranca SOLO el servidor y abre la página Blockly en el navegador —
sin ventana de pilas. La ventana 3D aparece cuando el usuario pulsa
"Ejecutar" (el código generado corre en un subproceso propio) y el
botón pasa a "Detener" para matarlo.

    pilas3d-bloques            # comando (pip install -e .)

    >>> import pilas3d.bloques
    >>> pilas3d.bloques.main()          # desde Python/IPython
"""

import os
import webbrowser

from pilas3d.puente import PUERTO, PuenteBloques

DIR_WEB = os.path.join(os.path.dirname(__file__), 'bloques_web')


def main(abrir_navegador=True, servir=True):
    """Levanta el puente HTTP (sin ventana) y abre la página de
    bloques. Con ``servir=False`` devuelve ``(puente, url)`` sin
    bloquear — útil para tests o para integrarlo en otro programa."""
    puente = PuenteBloques(None, DIR_WEB)   # sin ventana: subprocesos
    url = puente.iniciar(PUERTO)

    print("pilas3d-bloques listo en", url)
    print("armá bloques en el navegador; 'Ejecutar' abre la ventana")

    if abrir_navegador:
        webbrowser.open(url)
    if servir:
        try:
            while True:                   # el hilo HTTP sirve solo
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            puente.detener()
    return puente, url


def cli():
    """Punto de entrada del comando ``pilas3d-bloques``."""
    main()
