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
        """Carga un archivo de mapa: ``*.mapa.json`` → :class:`Mundo`,
        ``*.terreno.json`` → :class:`Terreno`. Devuelve el actor con
        ``.spawn`` (tupla x, y, z o None) y ``.props`` (lista de
        actores estáticos)."""
        with open(ruta) as f:
            datos = json.load(f)
        if datos.get('tipo') == 'terreno':
            return self._cargar_terreno_datos(ruta, datos)
        return self._cargar_mundo_datos(ruta, datos)

    def _cargar_props(self, datos, dir_mapa):
        """Instancia los props del archivo (modelos estáticos)."""
        props = []
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
            props.append(actor)
        return props

    def _nombre_spawn(self, actor, datos, ruta):
        spawn = datos.get('spawn')
        actor.spawn = tuple(spawn) if spawn else None
        actor.nombre = datos.get('nombre') or \
            os.path.splitext(os.path.basename(ruta))[0]
        actor.props = self._cargar_props(
            datos, os.path.dirname(os.path.abspath(ruta)))

    def _cargar_mundo_datos(self, ruta, datos):
        mundo = self.pilas.actores.Mundo()
        for i, j, k, tipo in datos.get('bloques', []):
            mundo.poner_bloque(int(i), int(j), int(k), tipo)
        mundo._sucio = True
        self._nombre_spawn(mundo, datos, ruta)
        return mundo

    def _cargar_terreno_datos(self, ruta, datos):
        terreno = self.pilas.actores.Terreno(
            celdas=datos.get('celdas', 20),
            tamano_celda=datos.get('tamano_celda', 1.0),
            tipos=datos.get('tipos'))
        terreno.posicion = (datos.get('x', 0), datos.get('y', 0),
                            datos.get('z', 0))
        alturas = datos.get('alturas')
        if alturas:
            terreno.alturas = [[float(h) for h in fila]
                               for fila in alturas]
        celdas_tex = datos.get('celdas_tex')
        if celdas_tex:
            for i, fila in enumerate(celdas_tex):
                for k, nombre in enumerate(fila):
                    if nombre in terreno._tiles:
                        terreno._tex[i][k] = terreno._tiles.index(nombre)
        if datos.get('agua') is not None:
            terreno.agua = datos['agua']
        terreno._reconstruir_gl()
        self._nombre_spawn(terreno, datos, ruta)
        if datos.get('material'):
            # alias de pack en texturas/ — si la máquina no lo tiene
            # queda un Material vacío y se ven solo las baldosas
            terreno.aplicar_material(datos['material'])
        return terreno

    def guardar_terreno(self, ruta, terreno, nombre=None, spawn=None,
                        props=None):
        """Serializa un :class:`Terreno` a ``*.terreno.json``: alturas
        por vértice, baldosa por celda, nivel de agua, spawn y props.

        Si el terreno tiene un pack aplicado (``aplicar_material``)
        se guarda el alias en ``material`` y las baldosas originales,
        para que al cargar se re-aplique por nombre."""
        if terreno._tipos_baldosas is not None:
            tipos = terreno._tipos_baldosas
            tex = terreno._tex_baldosas
        else:
            tipos = terreno.tipos
            tex = terreno._tex
        tiles = list(tipos)
        datos = {
            'version': 1,
            'tipo': 'terreno',
            'nombre': nombre or getattr(terreno, 'nombre', None)
                      or 'terreno',
            'celdas': terreno.celdas,
            'tamano_celda': terreno.tamano_celda,
            'x': terreno.x, 'y': terreno.y, 'z': terreno.z,
            'alturas': terreno.alturas,
            'celdas_tex': [[tiles[t] for t in fila] for fila in tex],
            'tipos': tipos,
            'material': terreno._material_nombre,
            'agua': terreno.agua,
            'spawn': list(spawn) if spawn else None,
            'props': props or [],
        }
        os.makedirs(os.path.dirname(os.path.abspath(ruta)),
                    exist_ok=True)
        with open(ruta, 'w') as f:
            json.dump(datos, f, indent=1)
        return ruta

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
