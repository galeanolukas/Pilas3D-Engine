# -*- encoding: utf-8 -*-
"""Carga de imágenes: ``pilas.imagenes``.

Busca el archivo en el cwd, en ``pilas3d/data/`` y en el paquete —
mismo criterio que ``sonidos.cargar`` y ``actor.imagen``::

    img = pilas.imagenes.cargar('fondo.png')      # ImageData pyglet
    tex = pilas.imagenes.textura('fondo.png')     # Texture para GL
    tex = pilas.imagenes.textura('cielo.hdr')     # float GL_RGBA16F

Sirve para sprites/etiquetas pyglet, fondos de menú, heightmaps…
Los ``.hdr`` Radiance (equirectangulares, p. ej. Poly Haven) se
suben como textura float — ver ``pilas3d.hdr`` y ``Cielo``.
"""

import os


def resolver(ruta):
    """Resuelve la ruta de una imagen como hace ``actor.imagen``."""
    base = os.path.dirname(os.path.abspath(__file__))
    for cand in (ruta,
                 os.path.join(base, 'data', ruta),
                 os.path.join(base, 'data', 'hdr', ruta),
                 os.path.join(base, ruta)):
        if os.path.exists(cand):
            return cand
    raise IOError("No se encuentra la imagen '%s'" % ruta)


class TexturaHDR(object):
    """Textura float ``GL_RGBA16F`` — compatible con ``tex.id``."""

    def __init__(self, tex_id, ancho, alto):
        self.id = tex_id
        self.width = ancho
        self.height = alto


def textura_hdr(ruta):
    """Sube un ``.hdr`` como textura float ``GL_RGBA16F``."""
    import ctypes
    from pyglet.gl import (GL_CLAMP_TO_EDGE, GL_FLOAT, GL_LINEAR,
                           GL_REPEAT, GL_RGBA, GL_RGBA16F,
                           GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                           GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S,
                           GL_TEXTURE_WRAP_T, GLuint, glBindTexture,
                           glGenTextures, glTexImage2D, glTexParameteri)

    from pilas3d import hdr

    ancho, alto, datos = hdr.cargar(ruta)
    tex_id = GLuint()
    glGenTextures(1, ctypes.byref(tex_id))
    glBindTexture(GL_TEXTURE_2D, tex_id.value)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    buf = (ctypes.c_float * len(datos)).from_buffer_copy(datos)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, ancho, alto, 0,
                 GL_RGBA, GL_FLOAT, buf)
    return TexturaHDR(tex_id.value, ancho, alto)


class Imagenes(object):
    """Punto de acceso de ``pilas.imagenes``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def cargar(self, ruta):
        """Carga la imagen y devuelve su ``ImageData`` de pyglet."""
        from pyglet.image import load
        return load(resolver(ruta))

    def textura(self, ruta):
        """Carga la imagen ya convertida en ``Texture`` OpenGL.

        Los ``.hdr`` se suben como ``GL_RGBA16F`` (float, valores
        mayores que 1.0) — el shader los muestra con tone mapping.
        """
        ruta = resolver(ruta)
        if ruta.lower().endswith('.hdr'):
            return textura_hdr(ruta)
        from pyglet.image import load
        return load(ruta).get_texture()
