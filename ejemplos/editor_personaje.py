# -*- encoding: utf-8 -*-
"""Editor de personajes articulados (v1).

Carga un modelo glTF riggeado y permite posar sus huesos:

- Flechas ARRIBA/ABAJO: elegir hueso
- X / Y / Z: elegir eje de rotación
- IZQUIERDA/DERECHA: rotar el hueso ±10°
- N: siguiente modelo (recorre los .glb de modelos/)
- G: guardar pose en 'pose-<modelo>.json'   C: cargarla   R: reiniciar
- M: capturar keyframe   W: borrar último   P: reproducir la
  animación formada por los keyframes (interpolada)
- J: guardar la animación en 'anim-<modelo>.json'   L: cargarla
- A: abrir el explorador de archivos para cargar un .glb externo
  (con caja de selección y nombre personalizado para el modelo)
- Botón derecho + drag: orbitar la cámara
- La esfera roja marca la articulación seleccionada
"""

import glob
import os

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - editor de personaje")

pilas.escena.fondo = pilas.colores.gris_oscuro   # fondo de estudio
piso = pilas.actores.Piso(tamano=30, divisiones=30)
piso.color = pilas.colores.gris
pilas.luces.direccional.ambiente = 0.6

# modelos .glb disponibles en el directorio modelos/ (local, no se
# publica): wolf, fox, cesium-man... los que hayas bajado.
DIR_EJ = os.path.dirname(os.path.abspath(__file__))
MODELOS = sorted(
    glob.glob(os.path.join(DIR_EJ, '..', 'modelos', '**', '*.glb'),
              recursive=True) +
    glob.glob(os.path.join(DIR_EJ, '..', 'modelos', '*.glb')))
if not MODELOS:
    raise SystemExit("no hay .glb en modelos/ - bajá alguno de "
                     "KhronosGroup/glTF-Sample-Assets")


def ruta_pose(ruta_modelo):
    base = os.path.splitext(os.path.basename(ruta_modelo))[0]
    return os.path.join(DIR_EJ, 'pose-%s.json' % base)


def ruta_anim(ruta_modelo):
    base = os.path.splitext(os.path.basename(ruta_modelo))[0]
    return os.path.join(DIR_EJ, 'anim-%s.json' % base)


def autoescala(modelo, objetivo=1.8):
    """Normaliza el modelo a ~``objetivo`` unidades de alto
    (los .glb vienen en unidades arbitrarias: el Fox está en cm)."""
    pos = modelo._pos
    if not pos:
        return 1.0
    ys = pos[1::3]
    alto = max(ys) - min(ys) or 1.0
    return objetivo / alto


estado = {'modelo': None, 'huesos': [], 'sel': 0, 'eje': 'y',
          'indice': 0, 'frames': [], 'modo': 'editar'}
nombres = {}   # ruta -> nombre amigable elegido al cargar externo
exp = {'dir': os.path.expanduser('~'), 'sel': 0, 'entradas': []}
nombrar = {'texto': '', 'ruta': None}


def nombre_modelo(ruta):
    return nombres.get(ruta) or os.path.basename(ruta)

marcador = pilas.actores.Esfera(radio=0.08)
marcador.color = pilas.colores.rojo

lista = pilas.actores.Texto("", x=10, y=170, tamano=13)
info = pilas.actores.Texto("", x=10, y=420, tamano=15)
info.color = pilas.colores.amarillo
pilas.actores.Texto(
    "N: modelo - arriba/abajo: hueso - X/Y/Z: eje - <-/->: rotar - "
    "M: keyframe - W: borrar - P: play - J/L: anim - G/C/R: pose "
    "- A: cargar .glb externo",
    x=10, y=10)


def cargar_modelo(i):
    """Instancia el modelo i de MODELOS, recrea lista de huesos."""
    if estado['modelo'] is not None:
        estado['modelo'].eliminar()
    ruta = MODELOS[i]
    modelo = pilas.actores.ModeloGLTF(ruta)
    modelo.escala = autoescala(modelo)
    estado['modelo'] = modelo
    estado['huesos'] = modelo.huesos()
    estado['sel'] = 0
    estado['frames'] = []
    refrescar_ui()


def refrescar_ui():
    huesos, sel = estado['huesos'], estado['sel']
    if not huesos:
        info.texto = "este modelo no tiene esqueleto"
        lista.texto = ""
        return
    i, nombre = huesos[sel]
    base = nombre_modelo(MODELOS[estado['indice']])
    info.texto = "%s  |  hueso: %s  eje: %s" % (base, nombre,
                                               estado['eje'])
    ini = max(0, min(sel - 7, len(huesos) - 14))
    lineas = []
    for k, (j, n) in enumerate(huesos[ini:ini + 14]):
        marca = '>> ' if ini + k == sel else '   '
        lineas.append('%s%s' % (marca, n))
    lista.texto = '\n'.join(lineas)


class MarcadorHueso(object):
    """Actualiza la esfera a la posición del hueso elegido."""

    def actualizar(self):
        if estado['huesos']:
            marcador.posicion = estado['modelo'].posicion_hueso(
                estado['huesos'][estado['sel']][0])


pilas.tareas.siempre(0, MarcadorHueso().actualizar)


# -- explorador de archivos (cargar .glb externo) -------------------------

def _listar_dir():
    """Relee exp['dir']: primero '..', luego dirs, luego .glb/.gltf."""
    try:
        ent = sorted(os.listdir(exp['dir']))
    except OSError:
        ent = []
    dirs = ['[%s]' % d for d in ent
            if os.path.isdir(os.path.join(exp['dir'], d))]
    glbs = [f for f in ent
            if f.lower().endswith(('.glb', '.gltf'))]
    exp['entradas'] = ['..'] + dirs + glbs
    exp['sel'] = min(exp['sel'], len(exp['entradas']) - 1)


def _pintar_explorador():
    info.texto = "Elegir modelo - dir: %s" % exp['dir']
    ini = max(0, min(exp['sel'] - 7, len(exp['entradas']) - 14))
    lista.texto = '\n'.join(
        ('>> ' if ini + k == exp['sel'] else '   ') + e
        for k, e in enumerate(exp['entradas'][ini:ini + 14]))


def abrir_explorador():
    estado['modo'] = 'explorar'
    exp['sel'] = 0
    _listar_dir()
    _pintar_explorador()


def _tecla_explorador(t):
    s = pilas.simbolos
    if t == s.ESCAPE:
        estado['modo'] = 'editar'
    elif t == s.ARRIBA:
        exp['sel'] = (exp['sel'] - 1) % len(exp['entradas'])
    elif t == s.ABAJO:
        exp['sel'] = (exp['sel'] + 1) % len(exp['entradas'])
    elif t == s.ENTER:
        e = exp['entradas'][exp['sel']]
        if e == '..':
            exp['dir'] = os.path.dirname(
                exp['dir'].rstrip(os.sep)) or os.sep
            exp['sel'] = 0
            _listar_dir()
        elif e.startswith('['):
            exp['dir'] = os.path.join(exp['dir'], e[1:-1])
            exp['sel'] = 0
            _listar_dir()
        else:
            nombrar['ruta'] = os.path.join(exp['dir'], e)
            nombrar['texto'] = os.path.splitext(e)[0]
            estado['modo'] = 'nombre'
    if estado['modo'] == 'explorar':
        _pintar_explorador()
    else:
        _pintar_nombre()


def _pintar_nombre():
    base = os.path.basename(nombrar['ruta'])
    info.texto = "nombre para %s (ENTER confirma, ESC cancela)" % base
    lista.texto = '>> %s_' % nombrar['texto']


def _tecla_nombre(t):
    s = pilas.simbolos
    if t == s.ESCAPE:
        estado['modo'] = 'editar'
        refrescar_ui()
    elif t == s.BACKSPACE:
        nombrar['texto'] = nombrar['texto'][:-1]
        _pintar_nombre()
    elif t == s.ENTER:
        ruta = nombrar['ruta']
        MODELOS.append(ruta)
        if nombrar['texto'].strip():
            nombres[ruta] = nombrar['texto'].strip()
        estado['modo'] = 'editar'
        estado['indice'] = len(MODELOS) - 1
        cargar_modelo(estado['indice'])


def _al_pulsar_overlay(simbolo, _mod):
    """Handler sobre la ventana: en modo explorar/nombre consume la
    tecla (incluido ESC, que cancela en vez de cerrar la ventana)."""
    if estado['modo'] == 'editar':
        return None
    if estado['modo'] == 'explorar':
        _tecla_explorador(simbolo)
    else:
        _tecla_nombre(simbolo)
    return True


def _al_texto_overlay(texto):
    if estado['modo'] != 'nombre':
        return None
    if texto >= ' ' and texto != '\r':
        nombrar['texto'] += texto
        _pintar_nombre()
    return True


if pilas.ventana is not None:
    pilas.ventana.push_handlers(on_key_press=_al_pulsar_overlay,
                                on_text=_al_texto_overlay)


def al_pulsar(tecla):
    s = pilas.simbolos
    modelo = estado['modelo']
    huesos = estado['huesos']
    if estado['modo'] != 'editar':
        return          # el overlay ya consumió la tecla
    if tecla == s.a:
        abrir_explorador()
        return
    if tecla == s.n:
        estado['indice'] = (estado['indice'] + 1) % len(MODELOS)
        cargar_modelo(estado['indice'])
        return
    if not huesos:
        refrescar_ui()
        return
    if tecla == s.ARRIBA:
        estado['sel'] = (estado['sel'] - 1) % len(huesos)
    elif tecla == s.ABAJO:
        estado['sel'] = (estado['sel'] + 1) % len(huesos)
    elif tecla == s.x:
        estado['eje'] = 'x'
    elif tecla == s.y:
        estado['eje'] = 'y'
    elif tecla == s.z:
        estado['eje'] = 'z'
    elif tecla in (s.IZQUIERDA, s.DERECHA):
        grados = -10 if tecla == s.IZQUIERDA else 10
        modelo.detener()
        modelo.rotar_hueso(huesos[estado['sel']][0], estado['eje'],
                           grados)
        modelo.refrescar_pose()
    elif tecla == s.g:
        pose = ruta_pose(MODELOS[estado['indice']])
        modelo.guardar_pose(pose)
        info.texto = "pose guardada: " + os.path.basename(pose)
        return
    elif tecla == s.c:
        pose = ruta_pose(MODELOS[estado['indice']])
        if os.path.exists(pose):
            modelo.detener()
            modelo.cargar_pose(pose)
    elif tecla == s.r:
        modelo.reiniciar_pose()
    elif tecla == s.m:
        # captura la pose actual como keyframe (copia JSON-able)
        modelo.detener()
        import json
        pose = json.loads(json.dumps(modelo._pose_actual()))
        estado['frames'].append(pose)
        info.texto = "%d keyframes" % len(estado['frames'])
        return
    elif tecla == s.w:
        if estado['frames']:
            estado['frames'].pop()
    elif tecla == s.p:
        frames = estado['frames']
        if len(frames) < 2:
            info.texto = "necesitás >= 2 keyframes (tecla M)"
            return
        modelo.crear_animacion('mi_anim', frames)
        modelo.animar('mi_anim', ciclica=True)
        info.texto = "reproduciendo %d keyframes" % len(frames)
        return
    elif tecla == s.j:
        frames = estado['frames']
        if len(frames) >= 2:
            modelo.crear_animacion('mi_anim', frames)
        if 'mi_anim' not in modelo.animaciones():
            info.texto = "necesitás >= 2 keyframes (tecla M)"
            return
        ruta = ruta_anim(MODELOS[estado['indice']])
        modelo.guardar_animacion(ruta, 'mi_anim')
        info.texto = "animación guardada: " + os.path.basename(ruta)
        return
    elif tecla == s.l:
        ruta = ruta_anim(MODELOS[estado['indice']])
        if os.path.exists(ruta):
            modelo.animar(modelo.cargar_animacion(ruta), ciclica=True)
            info.texto = "animación cargada: " + os.path.basename(ruta)
            return
    refrescar_ui()


pilas.escena.cuando_pulsa_tecla = al_pulsar
cargar_modelo(0)

camara = pilas.escena.camara
camara.posicion = (0, 2.2, 4.5)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

pilas.ejecutar()
