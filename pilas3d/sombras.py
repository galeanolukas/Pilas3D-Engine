# -*- encoding: utf-8 -*-
"""Shadow mapping de la luz direccional (el "sol").

La técnica estándar: se dibuja la escena desde la perspectiva de la
luz a una textura de profundidad (FBO) y en la pasada normal el
fragment shader compara su profundidad en espacio de luz contra ese
mapa — si está más lejos que lo que ve la luz, hay sombra.

Se reutiliza el programa principal como shader de profundidad (la
rasterización de profundidad no depende del color del fragmento), así
``actor.dibujar()`` funciona sin cambios en ambas pasadas.

Toggle: ``escena.sombras = False``. El tamaño del mapa (``tamano``,
default 2048²) y el área que cubre el sol (``radio``, ortográfica
centrada en el origen) se ajustan en ``pilas.sombras``.
"""

import math

from pyglet.gl import *
from pyglet.math import Mat4, Vec3

#: actores que no proyectan sombra (domo del cielo, helpers, puntos)
_SIN_SOMBRA = ('Cielo', 'Ejes', 'Particulas', 'Sombra', 'Zona')


class MapaSombras(object):
    """FBO de profundidad + pasada desde la luz direccional."""

    def __init__(self, tamano=2048, radio=50.0):
        self.tamano = tamano
        self.radio = radio
        self.activas = True
        self._fbo = None
        self._tex = None
        self.id_textura = 0

    # -- recursos GL -------------------------------------------------

    def _crear(self):
        """Crea el FBO + textura de profundidad (requiere contexto)."""
        t = self.tamano
        tex = GLuint()
        glGenTextures(1, tex)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, t, t, 0,
                     GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                        GL_NEAREST)
        # fuera del frustum de luz -> iluminado (borde en 1.0)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,
                        GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,
                        GL_CLAMP_TO_BORDER)
        borde = (GLfloat * 4)(1.0, 1.0, 1.0, 1.0)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, borde)

        fbo = GLuint()
        glGenFramebuffers(1, fbo)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                             GL_TEXTURE_2D, tex, 0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        ok = glCheckFramebufferStatus(GL_FRAMEBUFFER) \
            == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        if not ok:
            return False
        self._fbo, self._tex = fbo, tex
        self.id_textura = tex.value
        return True

    # -- la luz como cámara --------------------------------------------

    def matriz_luz(self, escena):
        """Ortográfica mirando al centro desde la dirección del sol."""
        d = escena.luces.direccional.direccion
        largo = math.sqrt(sum(c * c for c in d)) or 1.0
        dx, dy, dz = (c / largo for c in d)
        centro = Vec3(*escena.camara.objetivo)   # sigue a la escena
        ojo = centro - Vec3(dx, dy, dz) * (self.radio * 2)
        vista = Mat4.look_at(ojo, centro, Vec3(0, 1, 0))
        proy = Mat4.orthogonal_projection(
            -self.radio, self.radio, -self.radio, self.radio,
            0.1, self.radio * 4)
        return proy @ vista

    def pasada(self, escena, programa):
        """Render de profundidad: dibuja los actores al FBO con la
        matriz de la luz. Devuelve False si el FBO no se pudo crear."""
        if self._fbo is None and not self._crear():
            return False
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)
        glViewport(0, 0, self.tamano, self.tamano)
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(2.0, 4.0)          # ayuda al bias del shader
        # el mapa está siendo escrito: nadie puede muestrearlo aquí
        programa['usar_sombras'] = False
        glActiveTexture(GL_TEXTURE0 + 7)
        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
        programa['proyeccion'] = Mat4()    # proy@vista ya integrada
        programa['vista'] = self.matriz_luz(escena)
        for actor in list(escena.actores):
            if getattr(actor, 'es_overlay', False) \
                    or getattr(actor, 'sin_luz', False) \
                    or not getattr(actor, 'visible', True) \
                    or type(actor).__name__ in _SIN_SOMBRA:
                continue
            if getattr(actor, '_modo', 4) not in (None, 4):
                continue                     # puntos/líneas
            actor.dibujar()
        glDisable(GL_POLYGON_OFFSET_FILL)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return True

    def usar_en(self, programa, matriz, unidad=7):
        """Liga la textura de profundidad para la pasada normal."""
        glActiveTexture(GL_TEXTURE0 + unidad)
        glBindTexture(GL_TEXTURE_2D, self._tex)
        programa['mapa_sombras'] = unidad
        programa['matriz_luz'] = matriz
        programa['usar_sombras'] = True
