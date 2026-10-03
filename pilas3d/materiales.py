# -*- encoding: utf-8 -*-
"""Materiales compuestos: base + normal + AO + rugosidad.

El motor es Lambert educativo, no PBR completo — pero soporta los
mapas que más se notan de un pack de texturas (Poliigon, ambientCG,
Quixel):

- ``base``: la textura difusa (igual que ``actor.imagen``)
- ``normal``: relieve por normal map (por derivadas de pantalla —
  sirve para .obj, Terreno y glTF sin tangentes)
- ``ao``: oclusión ambiental — oscurece la luz ambiente
- ``rugosidad``: controla el brillo especular (Blinn-Phong)
- ``metalico``/``heightmap``: se detectan pero el metal no se usa
  (sin env map no se ve) y el heightmap va a ``Terreno.desde_heightmap``

::

    mat = pilas.materiales.desde_carpeta(
        'modelos/Poliigon_GrassPatchyGround_4585/2K')
    terreno.material = mat          # pisa/imagen sigue siendo la base

Cualquier mapa puede quedar en ``None`` — el shader se adapta.
"""

import os

from pilas3d.actores.actor import Actor


class Material(object):
    """Conjunto de mapas de un actor. Todos opcionales."""

    def __init__(self, base=None, normal=None, ao=None,
                 rugosidad=None, metalico=None, heightmap=None):
        self.base = base
        self.normal = normal
        self.ao = ao
        self.rugosidad = rugosidad
        self.metalico = metalico      # detectado, no usado todavía
        self.heightmap = heightmap    # para Terreno.desde_heightmap
        self._tex = {}
        self._desactivados = {}       # mapas apagados por apagar()

    def apagar(self, slot):
        """Desactiva un mapa sin perderlo — ``mat.apagar('normal')``
        para comparar con y sin. Se restaura con ``prender``."""
        if getattr(self, slot) is not None:
            self._desactivados[slot] = getattr(self, slot)
            setattr(self, slot, None)

    def prender(self, slot):
        """Reactiva el mapa apagado con ``apagar``."""
        if slot in self._desactivados:
            setattr(self, slot, self._desactivados.pop(slot))

    def textura(self, slot):
        """Carga perezosa del mapa ``slot`` (ruta, ImageData o
        Texture de pyglet)."""
        obj = getattr(self, slot)
        if obj is None:
            return None
        if slot not in self._tex:
            if hasattr(obj, 'get_texture'):
                self._tex[slot] = obj.get_texture()
            else:
                from pyglet.image import load
                self._tex[slot] = load(
                    Actor._resolver_imagen(obj)).get_texture()
        return self._tex[slot]

    def __repr__(self):
        usados = [s for s in ('base', 'normal', 'ao', 'rugosidad')
                  if getattr(self, s)]
        return '<Material %s>' % ('+'.join(usados) or 'vacío')


# -- autodetección por nombre de archivo ----------------------------------

_PATRONES = [
    ('base', ('basecolor', 'albedo', 'diffuse', 'colormap', 'color')),
    ('normal', ('normal', '_nrm')),
    ('ao', ('ambientocclusion', 'occlusion', '_ao')),
    ('rugosidad', ('roughness', 'rugosidad', 'rough')),
    ('metalico', ('metallic', 'metalness', 'metal')),
    ('heightmap', ('displacement', 'heightmap', 'disp', 'bump')),
]
_EXT = ('.png', '.jpg', '.jpeg', '.bmp')


class Materiales(object):
    """Fábrica de materiales (``pilas.materiales``)."""

    def __init__(self, pilas):
        self.pilas = pilas

    def cargar(self, base=None, normal=None, ao=None,
               rugosidad=None):
        """Arma un material nombrando los mapas a mano."""
        return Material(base=base, normal=normal, ao=ao,
                        rugosidad=rugosidad)

    def desde_carpeta(self, directorio):
        """Detecta los mapas de un directorio por su nombre —
        sirve para packs de Poliigon/ambientCG/Quixel (y para el
        ``.mtlx`` de Poliigon, que no hace falta parsear: los nombres
        de archivo ya dicen qué son)."""
        mat = Material()
        try:
            archivos = os.listdir(directorio)
        except OSError:
            return mat
        candidatos = {}
        for nombre in sorted(archivos):
            bajo = nombre.lower()
            if not bajo.endswith(_EXT) or 'preview' in bajo:
                continue
            ruta = os.path.join(directorio, nombre)
            for slot, patrones in _PATRONES:
                if any(p in bajo for p in patrones):
                    candidatos.setdefault(slot, []).append(ruta)
                    break
        for slot, rutas in candidatos.items():
            elegida = rutas[0]
            if slot == 'normal':
                # OpenGL quiere la variante Y+ (NormalGL); si el pack
                # trae ambas se evita la DX, y si solo hay DX se usa
                # igual — las derivadas absorben casi toda la diferencia
                gl = [r for r in rutas if 'normaldx' not in r.lower()]
                elegida = (gl or rutas)[0]
            setattr(mat, slot, elegida)
        return mat
