# -*- encoding: utf-8 -*-
"""Mapas de bloques para juegos: formato ``*.mapa.json``.

Un mapa es una lista de bloques del :class:`Mundo` (voxels), más un
punto de inicio (``spawn``) y props opcionales (modelos estáticos
encima del terreno: árboles, farolas...). Es el contrato entre el
editor ``pilas3d-mapas`` y los juegos::

    # en el editor se guarda con G → mapas/nivel.mapa.json
    mundo = pilas.mapas.cargar('mapas/nivel.mapa.json')
    jugador.posicion = mundo.spawn          # donde empieza
    for prop in mundo.props: ...            # modelos estáticos

Formato del archivo::

    {
      "version": 1, "nombre": "nivel",
      "spawn": [0.5, 1.0, 0.5],
      "bloques": [[i, j, k, "tipo"], ...],
      "props":  [{"ruta": "modelos/props/arbol.glb",
                  "x": 0, "y": 1, "z": 0, "escala": 1.0,
                  "rotacion_y": 0}]
    }
"""

import json
import os


class Mapas(object):
    """Carga y guarda mapas de bloques (``pilas.mapas``)."""

    def __init__(self, pilas):
        self.pilas = pilas

    def cargar(self, ruta):
        """Crea un :class:`Mundo` con los bloques del archivo y sus
        props. Devuelve el mundo con ``mundo.spawn`` (tupla x, y, z o
        None) y ``mundo.props`` (lista de actores estáticos)."""
        with open(ruta) as f:
            datos = json.load(f)
        mundo = self.pilas.actores.Mundo()
        for i, j, k, tipo in datos.get('bloques', []):
            mundo.poner_bloque(int(i), int(j), int(k), tipo)
        mundo._sucio = True

        dir_mapa = os.path.dirname(os.path.abspath(ruta))
        mundo.props = []
        for p in datos.get('props', []):
            ruta_prop = p.get('ruta', '')
            # relativa: primero tal cual (cwd), luego junto al .mapa.json
            ruta_real = ruta_prop
            if not os.path.isabs(ruta_real) \
                    and not os.path.exists(ruta_real):
                ruta_real = os.path.join(dir_mapa, ruta_prop)
            if not os.path.exists(ruta_real):
                continue
            if ruta_real.lower().endswith(('.glb', '.gltf')):
                actor = self.pilas.actores.ModeloGLTF(ruta_real)
            else:
                actor = self.pilas.actores.Modelo(ruta_real)
            actor.ruta = ruta_prop     # conserva la ruta original al re-guardar
            actor.posicion = (p.get('x', 0), p.get('y', 0),
                              p.get('z', 0))
            actor.escala = p.get('escala', 1.0)
            actor.rotacion_x = p.get('rotacion_x', 0)
            actor.rotacion_y = p.get('rotacion_y', 0)
            actor.rotacion_z = p.get('rotacion_z', 0)
            mundo.props.append(actor)

        spawn = datos.get('spawn')
        mundo.spawn = tuple(spawn) if spawn else None
        mundo.nombre = datos.get('nombre') or \
            os.path.splitext(os.path.basename(ruta))[0]
        return mundo

    def guardar(self, ruta, mundo, nombre=None, spawn=None,
                props=None):
        """Serializa los bloques del mundo a ``*.mapa.json``.

        ``props`` es una lista de dicts ``{'ruta', 'x', 'y', 'z',
        'escala'}``; ``spawn`` una tupla ``(x, y, z)``."""
        bloques = [[i, j, k, tipo]
                   for (i, j, k), tipo in sorted(mundo.bloques.items())]
        datos = {
            'version': 1,
            'nombre': nombre or getattr(mundo, 'nombre', None)
                      or 'mapa',
            'spawn': list(spawn) if spawn else None,
            'bloques': bloques,
            'props': props or [],
        }
        os.makedirs(os.path.dirname(os.path.abspath(ruta)),
                    exist_ok=True)
        with open(ruta, 'w') as f:
            json.dump(datos, f, indent=1)
        return ruta
