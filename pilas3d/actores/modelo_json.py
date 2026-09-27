# -*- encoding: utf-8 -*-
"""Actor que dibuja un modelo de bloque estilo Minecraft (.json).

>>> escalera = pilas.actores.ModeloJSON('assets/.../ladder.json')

La textura se resuelve sola desde el dict "textures" del modelo
(buscando el directorio ``textures`` hermano de ``models``). Modelos
con varias texturas usan la primera — es el límite de una sola
textura por actor.
"""

from pyglet.gl import GL_TRIANGLES

from pilas3d import modelos
from pilas3d.actores.actor import Actor


class ModeloJSON(Actor):
    """Un modelo de bloque Minecraft; se transforma como todo actor."""

    def __init__(self, pilas, ruta, x=0, y=0, z=0, escala=1.0):
        self.ruta = ruta
        self._datos = modelos.cargar_json_mc(ruta)
        super(ModeloJSON, self).__init__(pilas, x=x, y=y, z=z)
        self.escala = escala
        self.radio_de_colision = self._datos['radio'] * escala
        if self._datos.get('imagen'):
            self.imagen = self._datos['imagen']

    def _generar_geometria(self):
        d = self._datos
        return d['posiciones'], d['normales'], GL_TRIANGLES, \
            d['colores'], d['uvs']
