# -*- encoding: utf-8 -*-
"""Guardar y cargar partidas en JSON.

    >>> pilas.guardar_partida('partida.json', datos={'puntos': 3})
    >>> datos = pilas.cargar_partida('partida.json')

``guardar_partida`` serializa los actores simples de la escena (los
que la fábrica ``pilas.actores`` sabe crear con ``x, y, z``): clase,
posición, rotación y ``vida``/``vida_maxima`` si los tienen. Los
actores especiales (Globo, Menu, overlays…) se omiten.

``cargar_partida`` recrea esos actores en la escena actual y devuelve
el dict ``datos`` que se guardó — ahí va el puntaje, nivel, etc.
"""

import json


def guardar(pilas, ruta, datos=None):
    """Vuelca la escena a ``ruta``. Retorna el dict guardado."""
    escena = pilas.escena_actual()
    actores = []
    for a in escena.actores:
        clase = type(a).__name__
        if getattr(pilas.actores, clase, None) is None:
            continue                        # actor no recreable
        actores.append({
            'clase': clase,
            'x': a.x, 'y': a.y, 'z': a.z,
            'rotacion_y': a.rotacion_y,
            'vida': getattr(a, 'vida', None),
            'vida_maxima': getattr(a, 'vida_maxima', None),
        })
    estado = {'actores': actores, 'datos': datos or {}}
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=1)
    return estado


def cargar(pilas, ruta, limpiar=True):
    """Recrea los actores guardados. Retorna el dict ``datos``.

    Con ``limpiar=False`` no borra nada: restaura posición, rotación
    y vida sobre los actores vivos de la misma clase (conserva sus
    habilidades, callbacks y conexiones — ideal para "cargar" dentro
    del mismo juego), y crea solo los que falten."""
    with open(ruta, encoding='utf-8') as f:
        estado = json.load(f)
    escena = pilas.escena_actual()
    if limpiar:
        for a in list(escena.actores):
            a.eliminar()
    disponibles = list(escena.actores) if not limpiar else []
    for spec in estado.get('actores', []):
        a = None
        if disponibles is not None:
            for candidato in disponibles:
                if type(candidato).__name__ == spec.get('clase'):
                    a = candidato
                    disponibles.remove(candidato)
                    break
        if a is None:
            ctor = getattr(pilas.actores, spec.get('clase', ''), None)
            if ctor is None:
                continue
            try:
                a = ctor(x=spec['x'], y=spec['y'], z=spec['z'])
            except TypeError:
                continue                    # ctor sin x,y,z: se omite
        a.x, a.y, a.z = spec['x'], spec['y'], spec['z']
        a.rotacion_y = spec.get('rotacion_y', 0)
        if spec.get('vida_maxima') is not None:
            a.vida_maxima = spec['vida_maxima']
        if spec.get('vida') is not None:
            a.vida = spec['vida']
            a.vivo = a.vida > 0
    return estado.get('datos', {})
