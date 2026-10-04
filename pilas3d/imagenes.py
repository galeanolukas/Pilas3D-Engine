# -*- encoding: utf-8 -*-
"""Carga de imágenes: ``pilas.imagenes``.

Busca el archivo en el cwd, en ``pilas3d/data/`` y en el paquete —
mismo criterio que ``sonidos.cargar`` y ``actor.imagen``::

    img = pilas.imagenes.cargar('fondo.png')      # ImageData pyglet
    tex = pilas.imagenes.textura('fondo.png')     # Texture para GL

Sirve para sprites/etiquetas pyglet, fondos de menú, heightmaps…
"""

import os


def resolver(ruta):
    """Resuelve la ruta de una imagen como hace ``actor.imagen``."""
    base = os.path.dirname(os.path.abspath(__file__))
    for cand in (ruta,
                 os.path.join(base, 'data', ruta),
                 os.path.join(base, ruta)):
        if os.path.exists(cand):
            return cand
    raise IOError("No se encuentra la imagen '%s'" % ruta)


class Imagenes(object):
    """Punto de acceso de ``pilas.imagenes``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def cargar(self, ruta):
        """Carga la imagen y devuelve su ``ImageData`` de pyglet."""
        from pyglet.image import load
        return load(resolver(ruta))

    def textura(self, ruta):
        """Carga la imagen ya convertida en ``Texture`` OpenGL."""
        return self.cargar(ruta).get_texture()
