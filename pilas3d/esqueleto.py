# -*- encoding: utf-8 -*-
"""Mapeo semántico de huesos y animación procedural.

La idea: los modelos vienen con nombres de huesos arbitrarios
(inglés, alemán, jerga de cada rig). ``mapear_huesos`` clasifica cada
articulación en grupos semánticos (brazo/pierna/cabeza/cola...) con
heurísticas de nombres; ``animacion_procedural`` genera keyframes
con esos grupos — caminatas, sentarse, mover la cola — sin datos de
animación en el archivo.

Si los nombres no se reconocen, ``mapear_huesos_ia`` le pasa la lista
al asistente local (Ollama) para que haga el mapeo.
"""

import math
import re

from pilas3d import gltf

# lado izquierdo/derecho: 'l_4', 'Left', 'izq', 'leftfoot' /
# 'r_2', 'Right', 'der', 'rightarm' (left/right valen como
# subcadena; las siglas l/r/der/rech exigen bordes)
_IZQ = re.compile(r'left|izq|(?:^|[^a-z])l(?:[^a-z\d]|$)')
_DER = re.compile(r'right|(?:^|[^a-z])(?:r|der|rech)(?:[^a-z\d]|$)')

# orden importa: el primer grupo que matchea gana
_GRUPOS = [
    ('cola',    r'tail|schwanz|cola'),
    ('oreja',   r'ohr|(?:^|[^a-z])ear|oreja'),
    ('cabeza',  r'head|kopf|cabeza|neck|hals|cuello'),
    ('cara',    r'eye|aug|braun|brow|lied|kiefer|jaw|maul|mund|mouth'),
    ('brazo',   r'arm|shoulder|clavicle|hand|wrist|brazo|mano|hombro|'
                r'schalter|vorder|front|fore'),
    ('pierna',  r'leg|thigh|calf|shin|foot|toe|pierna|rodilla|pie|'
                r'schenkel|pfote|hinter|hind|back'),
    ('columna', r'spine|torso|chest|brust|bauch|pelvis|hip|becken|belly'),
]

#: partes que el generador puede animar
PARTES = ('brazo_izq', 'brazo_der', 'pierna_izq', 'pierna_der',
          'cola', 'cabeza', 'columna', 'oreja_izq', 'oreja_der')


def _lado(nombre):
    if _IZQ.search(nombre):
        return 'izq'
    if _DER.search(nombre):
        return 'der'
    return None


def _grupo(nombre):
    for g, patron in _GRUPOS:
        if re.search(patron, nombre):
            return g
    return None


def mapear_huesos(huesos):
    """Clasifica articulaciones por nombre.

    ``huesos`` es la lista ``(indice, nombre)`` de
    ``ModeloGLTF.huesos()``. Devuelve ``{parte: [indices]}`` donde
    cada lista guarda la cadena en orden (proximal→distal). Los
    huesos de cara (ojos, mandíbula) quedan fuera a propósito.
    """
    mapa = {p: [] for p in PARTES}
    for i, nombre in huesos:
        g = _grupo(nombre.lower())
        lado = _lado(nombre.lower())
        if g in ('brazo', 'pierna', 'oreja') and lado:
            mapa[g + '_' + lado].append(i)
        elif g in ('cola', 'cabeza', 'columna'):
            mapa[g].append(i)
    return {p: v for p, v in mapa.items() if v}


# -- generación de keyframes -------------------------------------------------

def _cadena_atenuada(n):
    """Factores por hueso en la cadena: el proximal rota más."""
    return [1.0 / (1.0 + k * 0.5) for k in range(n)]


def _rotar_pose(pose, i, eje, grados):
    d = pose.setdefault(str(i), {'r': [0, 0, 0, 1]})
    d['r'] = list(gltf.qmul(tuple(d['r']), gltf.quat_eje(eje, grados)))


def _base(modelo):
    import copy
    return copy.deepcopy(modelo._pose_actual())


def _anim_seno(modelo, nombre, ondas, duracion, eje='x', keyframes=8):
    """Arma keyframes sinusoidales: ``ondas`` = [(indices, amplitud,
    fase), ...]; cada hueso de una cadena recibe amplitud atenuada."""
    poses = []
    for k in range(keyframes):
        pose = _base(modelo)
        fase = 2 * math.pi * k / keyframes
        for indices, amp, desfase in ondas:
            for j, i in enumerate(indices):
                a = amp * math.sin(fase + desfase) * \
                    _cadena_atenuada(len(indices))[j]
                if a:
                    _rotar_pose(pose, i, eje, a)
        poses.append(pose)
    return modelo.crear_animacion(nombre, poses, duracion=duracion)


def _estatico(modelo, nombre, doblado, duracion=0.6, eje='x'):
    """Dos/tres keyframes: base → pose doblada → hold (ej. sentarse)."""
    pose = _base(modelo)
    for indices, grados in doblado:
        for j, i in enumerate(indices):
            _rotar_pose(pose, i, eje, grados *
                        _cadena_atenuada(len(indices))[j])
    base = _base(modelo)
    return modelo.crear_animacion(nombre, [base, pose, pose],
                                  duracion=duracion)


_TIPOS = ('caminar', 'correr', 'sentarse', 'cola', 'saludar', 'asentir')


def animacion_procedural(modelo, tipo='caminar', mapa=None, eje='x',
                         amplitud=30.0, usar_ia=False):
    """Genera y registra una animación por keyframes sobre ``modelo``.

    ``tipo``: 'caminar', 'correr', 'sentarse', 'cola', 'saludar',
    'asentir'. ``mapa`` es opcional (resultado de ``mapear_huesos``);
    por defecto se calcula de los nombres de hueso. Devuelve el
    nombre del clip, listo para ``modelo.animar(nombre)``.

    ``eje`` es el eje local de balanceo de las extremidades — si la
    animación sale "de costado", probá 'z'.
    """
    if tipo not in _TIPOS:
        raise ValueError("tipo desconocido '%s' (hay: %s)"
                         % (tipo, list(_TIPOS)))
    if mapa is None:
        mapa = mapear_huesos(modelo.huesos())
        if not mapa and usar_ia:
            mapa = mapear_huesos_ia(modelo)
    a = amplitud
    if tipo == 'caminar':
        ondas = [(mapa.get('pierna_izq', []), a, 0),
                 (mapa.get('brazo_der', []), a, 0),
                 (mapa.get('pierna_der', []), a, math.pi),
                 (mapa.get('brazo_izq', []), a, math.pi),
                 (mapa.get('columna', []), a * 0.12, 0)]
        return _anim_seno(modelo, tipo, ondas, duracion=0.35, eje=eje)
    if tipo == 'correr':
        ondas = [(mapa.get('pierna_izq', []), a * 1.7, 0),
                 (mapa.get('brazo_der', []), a * 1.7, 0),
                 (mapa.get('pierna_der', []), a * 1.7, math.pi),
                 (mapa.get('brazo_izq', []), a * 1.7, math.pi)]
        return _anim_seno(modelo, tipo, ondas, duracion=0.18, eje=eje)
    if tipo == 'cola':
        # ola que viaja a lo largo de la cola: cada hueso desfasado
        cola = mapa.get('cola', [])
        ondas = [(cola[k:k + 1], a, k * 0.9) for k in range(len(cola))]
        return _anim_seno(modelo, tipo, ondas, duracion=0.4, eje='y')
    if tipo == 'sentarse':
        return _estatico(modelo, tipo,
                         [(mapa.get('pierna_izq', []), 70),
                          (mapa.get('pierna_der', []), 70),
                          (mapa.get('columna', []), -15)], eje=eje)
    if tipo == 'saludar':
        # brazo arriba sostenido + la mano ondeando
        brazo = mapa.get('brazo_der', [])
        poses = []
        for k in range(8):
            pose = _base(modelo)
            if brazo:
                _rotar_pose(pose, brazo[0], 'z', -80)
            if len(brazo) > 1:
                _rotar_pose(pose, brazo[-1], 'x',
                            a * math.sin(2 * math.pi * k / 8))
            poses.append(pose)
        return modelo.crear_animacion(tipo, poses, duracion=0.5)
    # asentir: cabeza arriba/abajo
    ondas = [(mapa.get('cabeza', []), a * 0.6, 0)]
    return _anim_seno(modelo, tipo, ondas, duracion=0.6, eje=eje)


# -- mapeo asistido por IA (nombres no reconocidos) ---------------------------

def mapear_huesos_ia(modelo):
    """Pide al asistente local (Ollama) que clasifique los huesos.

    Devuelve el mismo formato que ``mapear_huesos``. Si Ollama no
    está disponible o la respuesta no se entiende, devuelve ``{}``.
    """
    huesos = modelo.huesos()
    nombres = '\n'.join('%d: %s' % (i, n) for i, n in huesos)
    prompt = (
        "Estos son los nombres de los huesos de un modelo 3D:\n%s\n\n"
        "Clasificá cada número de hueso en una de estas partes: %s.\n"
        "Respondé SOLO un JSON así: {\"brazo_izq\": [3,4], "
        "\"cola\": [7,8,9]} — los números, en orden de la cadena. "
        "Si un hueso no corresponde a ninguna parte, omitilo."
        % (nombres, ', '.join(PARTES)))
    try:
        from pilas3d.ia import asistente
        texto = asistente.preguntar(prompt)
    except Exception:
        return {}
    m = re.search(r'\{.*\}', texto, re.S)
    if not m:
        return {}
    import json
    try:
        datos = json.loads(m.group(0))
    except ValueError:
        return {}
    validos = {i for i, _ in huesos}
    mapa = {}
    for parte, indices in datos.items():
        if parte in PARTES:
            mapa[parte] = [int(i) for i in indices
                           if int(i) in validos]
    return {p: v for p, v in mapa.items() if v}
