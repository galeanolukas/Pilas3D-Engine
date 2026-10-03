# -*- encoding: utf-8 -*-
"""Terreno: rejilla deformable con textura por celda.

A diferencia del ``Mundo`` de voxels (bloques cúbicos), el terreno es
una sola malla suave: cada vértice tiene una altura y cada celda una
baldosa de textura. Ideal para montañas, pozos y lagos::

    t = pilas.actores.Terreno(celdas=20)
    t.montana(4, 4, radio=4, altura=3)      # una colina suave
    t.pozo(12, 10, radio=3, profundidad=2)  # un hoyo
    t.pintar(8, 8, 'agua')                  # baldosa de agua en la celda
    t.agua = 0.4                            # plano de agua: llena los pozos
    jugador.y = t.altura_suelo(jugador.x, jugador.z)

Los tipos de baldosa por defecto son 'pasto', 'piedra' y 'agua';
``tipos={'arena': 'arena.png', ...}`` arma el atlas con tus imágenes.
"""

import math

from pyglet.gl import GL_TRIANGLES

from pilas3d import colores
from pilas3d.actores.actor import Actor
from pilas3d.actores.mundo import armar_atlas


def _baldosa_solido(rgba, lado=16):
    """Baldosa de un color plano para el atlas (agua, etc.)."""
    from pyglet.image import ImageData
    return ImageData(lado, lado, 'RGBA', bytes(rgba) * (lado * lado))


TIPOS_POR_DEFECTO = {
    'pasto': 'pasto.png',
    'piedra': 'piedra_media.png',
    'agua': None,                          # se genera azul plano
}
AGUA_RGBA = (50, 110, 200, 220)


class Terreno(Actor):
    """Malla de ``celdas``x``celdas`` celdas deformable por vértice."""

    def __init__(self, pilas, x=0, y=0, z=0, celdas=20,
                 tamano_celda=1.0, tipos=None, imagen=None, agua=None):
        self.celdas = celdas
        self.tamano_celda = tamano_celda
        # alturas por VÉRTICE de la grilla: (celdas+1) x (celdas+1)
        self.alturas = [[0.0] * (celdas + 1) for _ in range(celdas + 1)]
        self.tipos = dict(tipos or TIPOS_POR_DEFECTO)
        self._tiles = list(self.tipos)             # orden en el atlas
        # celda (i, k) -> índice de baldosa
        self._tex = [[0] * celdas for _ in range(celdas)]
        self._agua = None
        self._nivel_agua = None
        # modo "pack de texturas": baldosas guardadas para restaurar
        self._tipos_baldosas = None
        self._tex_baldosas = None
        self._material_nombre = None
        #: Punto de inicio y props — los llena ``mapas.cargar``.
        self.spawn = None
        self.props = []

        if imagen:                               # una sola textura
            self.tipos = {'unica': imagen}
            self._tiles = ['unica']
        atlas = armar_atlas([
            self._resolver_baldosa(self.tipos[t]) for t in self._tiles])
        self._imagen_atlas = atlas

        super(Terreno, self).__init__(pilas, x=x, y=y, z=z)
        self.imagen = atlas
        self.radio_de_colision = 0.0
        if agua is not None:
            self.agua = agua

    @staticmethod
    def _resolver_baldosa(img):
        if img is None:
            return _baldosa_solido(AGUA_RGBA)
        res = Actor._resolver_imagen(img)
        return res

    # -- geometría ------------------------------------------------------

    def _normal_vertice(self, i, k):
        """Normal suave en el vértice (i, k) por diferencias centrales
        sobre la grilla de alturas."""
        c = self.celdas
        i0, i1 = max(0, i - 1), min(c, i + 1)
        k0, k1 = max(0, k - 1), min(c, k + 1)
        dx = (self.alturas[i1][k] - self.alturas[i0][k]) / \
             ((i1 - i0) * self.tamano_celda)
        dz = (self.alturas[i][k1] - self.alturas[i][k0]) / \
             ((k1 - k0) * self.tamano_celda)
        n = (-dx, 1.0, -dz)
        l = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        return n[0] / l, n[1] / l, n[2] / l

    def _generar_geometria(self):
        """Un quad por celda (vértices duplicados para que cada celda
        pueda mapear su propia baldosa del atlas), indexado."""
        c, tc = self.celdas, self.tamano_celda
        n_tiles = len(self._tiles)
        pos, nor, uv = [], [], []
        indices = []
        for i in range(c):
            for k in range(c):
                x0 = (i - c / 2.0) * tc
                x1 = x0 + tc
                z0 = (k - c / 2.0) * tc
                z1 = z0 + tc
                h00 = self.alturas[i][k]
                h10 = self.alturas[i + 1][k]
                h01 = self.alturas[i][k + 1]
                h11 = self.alturas[i + 1][k + 1]
                base = len(pos) // 3
                pos += [x0, h00, z0, x1, h10, z0,
                        x0, h01, z1, x1, h11, z1]
                for vi, vk in ((i, k), (i + 1, k),
                               (i, k + 1), (i + 1, k + 1)):
                    nor += self._normal_vertice(vi, vk)
                t = self._tex[i][k]
                u0, u1 = t / n_tiles, (t + 1) / n_tiles
                uv += [u0, 0.0, u1, 0.0, u0, 1.0, u1, 1.0]
                indices += [base, base + 1, base + 2,
                            base + 2, base + 1, base + 3]
        # el dibujo indexado evita duplicar vértices: _construir_gl lo
        # lee justo después de llamar a este método
        self._indices = indices
        return pos, nor, GL_TRIANGLES, None, uv

    # -- deformación ------------------------------------------------------

    def subir(self, i, k, cantidad=1.0):
        """Sube el vértice (i, k) — los vértices son de 0 a celdas."""
        self.alturas[i][k] += cantidad
        self._reconstruir_gl()

    def bajar(self, i, k, cantidad=1.0):
        self.alturas[i][k] -= cantidad
        self._reconstruir_gl()

    def nivelar(self, altura=0.0):
        """Deja todo el terreno plano a esa altura."""
        for i in range(self.celdas + 1):
            for k in range(self.celdas + 1):
                self.alturas[i][k] = altura
        self._reconstruir_gl()

    def _forma_circular(self, i, k, radio, delta, suavizar=True):
        """Aplica ``delta`` con decaimiento suave dentro del radio —
        montañas y pozos salen redondos, no escalonados."""
        c = self.celdas
        for vi in range(max(0, i - radio), min(c + 1, i + radio + 1)):
            for vk in range(max(0, k - radio),
                            min(c + 1, k + radio + 1)):
                d = math.hypot(vi - i, vk - k)
                if d <= radio:
                    f = 0.5 + 0.5 * math.cos(d / radio * math.pi) \
                        if suavizar else 1.0
                    self.alturas[vi][vk] += delta * f
        self._reconstruir_gl()

    def montana(self, i, k, radio=3, altura=2.0):
        """Colina suave centrada en el vértice (i, k)."""
        self._forma_circular(i, k, radio, altura)

    def pozo(self, i, k, radio=3, profundidad=2.0):
        """Hoyo suave — con ``agua`` puesta se convierte en lago."""
        self._forma_circular(i, k, radio, -profundidad)

    # -- texturas por celda -------------------------------------------------

    def pintar(self, i, k, tipo):
        """Cambia la baldosa de la celda (i, k) — 0 a celdas-1.

        ``tipo`` es un nombre de ``tipos`` ('pasto', 'agua'…).
        """
        if tipo not in self._tiles:
            raise ValueError("tipo desconocido %r — están: %s" %
                             (tipo, ', '.join(self._tiles)))
        self._tex[i][k] = self._tiles.index(tipo)
        self._reconstruir_gl()

    def pintar_zona(self, i, k, radio, tipo):
        """Pinta un círculo de celdas (para lagos, senderos…)."""
        for ci in range(max(0, i - radio),
                        min(self.celdas, i + radio + 1)):
            for ck in range(max(0, k - radio),
                            min(self.celdas, k + radio + 1)):
                if math.hypot(ci - i, ck - k) <= radio:
                    self._tex[ci][ck] = self._tiles.index(tipo)
        self._reconstruir_gl()

    # -- agua -----------------------------------------------------------------

    @property
    def agua(self):
        """Altura del plano de agua, o None. Los pozos que bajen de
        ese nivel se ven llenos — lago gratis."""
        return self._nivel_agua

    @agua.setter
    def agua(self, nivel):
        if nivel is None:
            if self._agua is not None:
                self._agua.eliminar()
                self._agua = None
            self._nivel_agua = None
            return
        if self._agua is None:
            lado = self.celdas * self.tamano_celda
            self._agua = self.pilas.actores.Plano(
                x=self.x, z=self.z, ancho=lado, profundidad=lado)
            self._agua.color = colores.celeste
            self._agua.transparencia = 40
        self._nivel_agua = nivel
        self._agua.y = self.y + (nivel or 0)
        self._agua.x, self._agua.z = self.x, self.z

    # -- pack de texturas compuestas -------------------------------------------

    def aplicar_material(self, mat):
        """Aplica un pack de ``pilas.materiales`` a todo el terreno —
        por :class:`Material` o por alias (str). El terreno pasa a
        modo "textura única": el ``base`` del pack se repite por
        celda y los mapas normal/AO/rugosidad muestrean UVs
        coherentes (con las UVs de atlas se verían mal).

        Las baldosas por celda quedan guardadas:
        ``aplicar_material(None)`` las restaura tal cual."""
        if isinstance(mat, str):
            self._material_nombre = mat
            mat = self.pilas.materiales[mat]
        else:
            self._material_nombre = None
        if mat is None:
            self.material = None
            if self._tipos_baldosas is not None:
                self.tipos = self._tipos_baldosas
                self._tex = self._tex_baldosas
                self._tipos_baldosas = None
                self._rearmar_tiles()
            return
        self.material = mat
        if self._tipos_baldosas is None:
            self._tipos_baldosas = self.tipos
            self._tex_baldosas = [fila[:] for fila in self._tex]
        if getattr(mat, 'base', None):
            self.tipos = {'unica': mat.base}
            self._tex = [[0] * self.celdas
                         for _ in range(self.celdas)]
            self._rearmar_tiles()

    def _rearmar_tiles(self):
        """Reconstruye ``_tiles``/atlas/imagen tras cambiar
        ``tipos`` — el mismo trabajo que hace ``__init__``."""
        self._tiles = list(self.tipos)
        self._imagen_atlas = armar_atlas([
            self._resolver_baldosa(self.tipos[t])
            for t in self._tiles])
        self.imagen = self._imagen_atlas
        self._reconstruir_gl()

    # -- heightmap desde imagen ------------------------------------------------

    def desde_heightmap(self, ruta, altura=3.0):
        """Carga la rejilla de alturas desde una imagen en grises —
        los ``Displacement``/``Height`` de los packs de texturas
        (PNG/JPG; los ``.tiff`` hay que convertirlos). La columna x de
        la imagen va al eje i y la fila al eje k; blanco = más alto."""
        from pyglet.image import load
        img = load(self._resolver_imagen(ruta)).get_image_data()
        ancho, alto = img.width, img.height
        pix = img.get_data('L', ancho)
        n = self.celdas + 1
        for i in range(n):
            for k in range(n):
                px = min(ancho - 1, int(i * ancho / float(n)))
                pk = min(alto - 1, int(k * alto / float(n)))
                self.alturas[i][k] = \
                    pix[pk * ancho + px] / 255.0 * altura
        self._reconstruir_gl()

    # -- guardar ---------------------------------------------------------------

    def guardar(self, ruta, nombre=None):
        """Escribe el terreno en ``*.terreno.json`` (alturas, baldosas,
        agua, spawn y props). Se carga con ``pilas.mapas.cargar``."""
        props = []
        for p in self.props:
            props.append({'ruta': getattr(p, 'ruta', ''),
                          'x': p.x, 'y': p.y, 'z': p.z,
                          'escala': getattr(p, 'escala', 1.0),
                          'rotacion_y': getattr(p, 'rotacion_y', 0)})
        return self.pilas.mapas.guardar_terreno(
            ruta, self, nombre=nombre, spawn=self.spawn, props=props)

    # -- suelo para caminar -------------------------------------------------

    def altura_suelo(self, x, z):
        """Altura del terreno en el punto (x, z) — interpolación
        bilinear entre los 4 vértices de la celda. Sirve para que un
        actor camine siguiendo las lomas suave."""
        c, tc = self.celdas, self.tamano_celda
        li = (x - self.x) / tc + c / 2.0
        lk = (z - self.z) / tc + c / 2.0
        i = int(math.floor(li)); k = int(math.floor(lk))
        if i < 0 or k < 0 or i >= c or k >= c:
            return None
        fi, fk = li - i, lk - k
        h00 = self.alturas[i][k]; h10 = self.alturas[i + 1][k]
        h01 = self.alturas[i][k + 1]; h11 = self.alturas[i + 1][k + 1]
        h0 = h00 + (h10 - h00) * fi
        h1 = h01 + (h11 - h01) * fi
        return self.y + h0 + (h1 - h0) * fk
