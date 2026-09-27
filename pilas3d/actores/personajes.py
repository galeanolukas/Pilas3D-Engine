# -*- encoding: utf-8 -*-
"""Personajes predefinidos, como los actores de pilas original
(Mono, Aceituna...) pero en 3D y cada uno con un método de dibujo
distinto — sirven de juego y de ejemplo de cómo construir actores:

- ``Robot``/``Humanoide``/``Mono``/``Arania``: primitivas combinadas
  con ``mallas.combinar`` y color por vértice.
- ``Espectro``: esferas alambradas (GL_LINES), sin superficie.

El origen de cada personaje está a la altura del torso (~cintura):
los pies quedan cerca de ``y - 0.8``.

Para darles comportamiento de NPC a cualquiera de estos (o a un
actor propio heredado de ``Actor``) está la habilidad
``pilas.habilidades.SerBot`` — ver ``pilas.actores.Bot``.
"""

from pyglet.gl import GL_TRIANGLES, GL_LINES

from pilas3d import colores, mallas
from pilas3d.actores.actor import Actor


class Personaje(Actor):
    """Base de los personajes predefinidos."""

    def __init__(self, pilas, x=0, y=0, z=0):
        super(Personaje, self).__init__(pilas, x=x, y=y, z=z)
        self.radio_de_colision = 0.7


class Robot(Personaje):
    """Robot de cuboides: torso, cabeza, brazos, piernas y antena."""

    def _generar_geometria(self):
        return mallas.combinar([
            (mallas.cuboide(0.55, 0.7, 0.32), (0, 0.0, 0),
             colores.gris),                          # torso
            (mallas.cubo(0.42), (0, 0.62, 0),
             colores.gris_claro),                    # cabeza
            (mallas.cuboide(0.16, 0.5, 0.16), (-0.42, -0.05, 0),
             colores.gris_oscuro),                   # brazo izq
            (mallas.cuboide(0.16, 0.5, 0.16), (0.42, -0.05, 0),
             colores.gris_oscuro),                   # brazo der
            (mallas.cuboide(0.2, 0.45, 0.2), (-0.16, -0.57, 0),
             colores.azul_oscuro),                   # pierna izq
            (mallas.cuboide(0.2, 0.45, 0.2), (0.16, -0.57, 0),
             colores.azul_oscuro),                   # pierna der
            (mallas.esfera(0.07, 8, 6), (0, 0.9, 0),
             colores.rojo),                          # antena
        ])


class Humanoide(Personaje):
    """Muñeco tipo bipedo: cabeza, torso, brazos y piernas."""

    def _generar_geometria(self):
        piel = (230, 190, 150)
        remera = (60, 120, 200)
        pantalon = (60, 60, 160)
        return mallas.combinar([
            (mallas.cubo(0.42), (0, 0.65, 0), piel),           # cabeza
            (mallas.cuboide(0.5, 0.62, 0.26), (0, 0.06, 0),
             remera),                                        # torso
            (mallas.cuboide(0.14, 0.55, 0.14), (-0.36, 0.02, 0),
             remera),                                        # brazo izq
            (mallas.cuboide(0.14, 0.55, 0.14), (0.36, 0.02, 0),
             remera),                                        # brazo der
            (mallas.cuboide(0.18, 0.5, 0.18), (-0.13, -0.5, 0),
             pantalon),                                      # pierna izq
            (mallas.cuboide(0.18, 0.5, 0.18), (0.13, -0.5, 0),
             pantalon),                                      # pierna der
        ])


class Mono(Personaje):
    """Mono de esferas y cuboides: panza, cabeza, orejas y cola."""

    def _generar_geometria(self):
        pelaje = colores.marron
        cara = (230, 190, 150)
        return mallas.combinar([
            (mallas.esfera(0.35, 16, 12), (0, -0.2, 0),
             pelaje),                                        # panza
            (mallas.esfera(0.26, 16, 12), (0, 0.32, 0),
             pelaje),                                        # cabeza
            (mallas.esfera(0.16, 12, 8), (0, 0.26, 0.2),
             cara),                                          # hocico
            (mallas.esfera(0.1, 10, 8), (-0.26, 0.4, 0),
             cara),                                          # oreja izq
            (mallas.esfera(0.1, 10, 8), (0.26, 0.4, 0),
             cara),                                          # oreja der
            (mallas.cuboide(0.08, 0.7, 0.08), (0.3, -0.55, -0.25),
             pelaje),                                        # cola
        ])


class Arania(Personaje):
    """Araña de primitivas: abdomen y cefalotórax de esferas, ocho
    patas de cuboides finos (dibujada sin recursos externos)."""

    def _generar_geometria(self):
        oscuro = (45, 35, 30)
        partes = [
            (mallas.esfera(0.4, 16, 12), (0, 0.1, -0.35), oscuro),
            (mallas.esfera(0.24, 14, 10), (0, 0.05, 0.15), oscuro),
        ]
        for lado in (-1, 1):              # cuatro patas por lado
            for j, z in enumerate((-0.35, -0.1, 0.15, 0.4)):
                partes.append(
                    (mallas.cuboide(0.7, 0.05, 0.05),
                     (lado * 0.4, -0.15 + 0.06 * j, z), oscuro))
        return mallas.combinar(partes)


class Espectro(Personaje):
    """Personaje alambrado: dos esferas GL_LINES flotando (sin
    superficie — atraviesa la niebla y las sombras)."""

    def _generar_geometria(self):
        cuerpo = mallas.esfera_alambrada(0.5, 12, 8)
        cabeza = mallas.esfera_alambrada(0.28, 10, 6)
        pos = list(cuerpo[0])
        for i in range(0, len(cabeza[0]), 3):
            pos += [cabeza[0][i], cabeza[0][i + 1] + 0.75,
                    cabeza[0][i + 2]]
        return pos, [0.0] * (len(pos)), GL_LINES, None, \
            [0.0] * (len(pos) // 3 * 2)
