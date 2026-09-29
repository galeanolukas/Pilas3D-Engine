# -*- encoding: utf-8 -*-
"""Editor de personajes articulados (v1).

Arranque::

    pilas3d-editor                     # comando (pip install -e .)
    python3 ejemplos/editor_personaje.py
    pilas.ayuda() >> desde la consola interactiva:
    >>> pilas3d.editor.main()

Carga un modelo glTF riggeado y permite posar sus huesos:

- Flechas ARRIBA/ABAJO: elegir hueso
- X / Y / Z: elegir eje de rotación
- IZQUIERDA/DERECHA: rotar el hueso ±10°
- N: siguiente modelo (recorre los .glb de modelos/)
- G: guardar pose en '<modelo>.pose.json' (junto al .glb)   C: cargarla
  R: reiniciar
- M: capturar keyframe   W: borrar último   B: vaciar todos
  P: reproducir la animación formada por los keyframes (interpolada)
- S: detener la animación (queda en el frame actual)
  U: volver a la pose que tenía antes de reproducir (P/L/T)
- J: guardar la animación con nombre → '<modelo>.<nombre>.anim.json'
  L: cicla las animaciones guardadas del modelo
- A: abrir el explorador de archivos para cargar un .glb externo
  (con caja de selección y nombre personalizado para el modelo)
- K: cambiar la textura del modelo (explorador de imágenes;
  "(texturas originales)" restaura las del archivo)
- T: animación procedural (caminar, correr, sentarse, cola, saludar,
  asentir) — generada desde los nombres de los huesos, con ayuda de
  la IA local si no los reconoce
- Botón derecho + drag: orbitar la cámara
- La esfera roja marca la articulación seleccionada
"""

import glob
import os
import re

import pilas3d
from pilas3d.esqueleto import animacion_procedural, mapear_huesos

pilas = None      # instancia de pilas3d.iniciar, la crea main()

MODELOS = []      # .glb/.gltf descubiertos en el directorio de modelos

estado = {'modelo': None, 'huesos': [], 'sel': 0, 'eje': 'y',
          'indice': 0, 'frames': [], 'modo': 'editar', 'proc': 0,
          'anim_sel': 0, 'pose_previa': None}

TIPOS_PROC = ['caminar', 'correr', 'sentarse', 'cola', 'saludar',
              'asentir']
nombres = {}   # ruta -> nombre amigable elegido al cargar externo
exp = {'dir': os.path.expanduser('~'), 'sel': 0, 'entradas': []}
nombrar = {'texto': '', 'ruta': None, 'para': 'modelo'}

PANEL = 250   # ancho del panel lateral en px
PIE = 110     # alto del panel inferior en px

# actores de UI, creados por main()
marcador = panel_der = panel_inf = lista = info = ayuda = None


def ruta_pose(ruta_modelo):
    """El JSON de pose vive JUNTO al modelo (modelos/.../pose-N.json)."""
    base = os.path.splitext(ruta_modelo)[0]
    return base + '.pose.json'


def ruta_anim(ruta_modelo, nombre=None):
    """``<modelo>.<nombre>.anim.json`` junto al .glb (o
    ``<modelo>.anim.json`` si no se nombra)."""
    base = os.path.splitext(ruta_modelo)[0]
    return base + ('.%s' % nombre if nombre else '') + '.anim.json'


def anims_del_modelo(ruta_modelo):
    """Archivos .anim.json junto al modelo (para ciclar con L)."""
    base = os.path.splitext(ruta_modelo)[0]
    patron = re.compile('^%s\\.(?:[^.]+\\.)?anim\\.json$'
                        % re.escape(os.path.basename(base)))
    return [f for f in sorted(glob.glob(base + '*.anim.json'))
            if patron.match(os.path.basename(f))]


def autoescala(modelo, objetivo=1.8):
    """Normaliza el modelo a ~``objetivo`` unidades de alto
    (los .glb vienen en unidades arbitrarias: el Fox está en cm)."""
    pos = modelo._pos
    if not pos:
        return 1.0
    ys = pos[1::3]
    alto = max(ys) - min(ys) or 1.0
    return objetivo / alto


def nombre_modelo(ruta):
    return nombres.get(ruta) or os.path.basename(ruta)


def buscar_modelos(directorio):
    """.glb + .gltf recursivos; si un modelo existe en ambos
    formatos gana el .glb."""
    vistos = {}
    for r in sorted(glob.glob(os.path.join(directorio, '**', '*.gl*'),
                              recursive=True)):
        if not r.lower().endswith(('.glb', '.gltf')):
            continue
        base = os.path.splitext(r)[0]
        if base not in vistos or r.endswith('.glb'):
            vistos[base] = r
    return sorted(vistos.values())


def organizar_layout():
    """Reparte la ventana: vista 3D arriba-izquierda, panel lateral
    para la lista de huesos y panel inferior para la info."""
    if pilas.ventana is None:
        return
    w, h = pilas.ventana.width, pilas.ventana.height
    pilas.ventana.area_3d = (0, PIE, w - PANEL, h - PIE)
    panel_der.x = w - PANEL
    panel_der.y = PIE
    panel_der.ancho = PANEL
    panel_der.alto = h - PIE
    panel_inf.ancho = w
    panel_inf.alto = PIE
    lista.x = w - PANEL + 8
    lista.y = h - 25
    lista.ancho = PANEL - 16
    info.x = 10
    info.y = PIE - 25
    ayuda.x = 10
    ayuda.y = PIE - 50


def cargar_modelo(i):
    """Instancia el modelo i de MODELOS, recrea lista de huesos."""
    if estado['modelo'] is not None:
        estado['modelo'].eliminar()
    estado['indice'] = i
    ruta = MODELOS[i]
    modelo = pilas.actores.ModeloGLTF(ruta)
    modelo.escala = autoescala(modelo)
    estado['modelo'] = modelo
    estado['huesos'] = modelo.huesos()
    estado['sel'] = 0
    estado['frames'] = []
    estado['anim_sel'] = 0
    estado['pose_previa'] = None
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
        lineas.append(('%s%s' % (marca, n))[:30])   # que entre en el panel
    lista.texto = '\n'.join(lineas)


class MarcadorHueso(object):
    """Actualiza la esfera a la posición del hueso elegido."""

    def actualizar(self):
        if estado['huesos']:
            marcador.posicion = estado['modelo'].posicion_hueso(
                estado['huesos'][estado['sel']][0])


# -- explorador de archivos (cargar .glb externo) -------------------------

def _listar_dir():
    """Relee exp['dir']: primero '..', luego dirs, luego los
    archivos según exp['para'] ('modelo' -> .glb/.gltf,
    'textura' -> imágenes + opción de restaurar)."""
    try:
        ent = sorted(os.listdir(exp['dir']))
    except OSError:
        ent = []
    dirs = ['[%s]' % d for d in ent
            if os.path.isdir(os.path.join(exp['dir'], d))]
    if exp.get('para') == 'textura':
        archivos = [f for f in ent if f.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.bmp'))]
        extra = ['(texturas originales)']
    else:
        archivos = [f for f in ent
                if f.lower().endswith(('.glb', '.gltf'))]
        extra = []
    exp['entradas'] = ['..'] + extra + dirs + archivos
    exp['sel'] = min(exp['sel'], len(exp['entradas']) - 1)


def _pintar_explorador():
    que = 'textura' if exp.get('para') == 'textura' else 'modelo'
    info.texto = "Elegir %s - dir: %s" % (que, exp['dir'])
    ini = max(0, min(exp['sel'] - 7, len(exp['entradas']) - 14))
    lista.texto = '\n'.join(
        ('>> ' if ini + k == exp['sel'] else '   ') + e
        for k, e in enumerate(exp['entradas'][ini:ini + 14]))


def abrir_explorador(para='modelo'):
    estado['modo'] = 'explorar'
    exp['para'] = para
    exp['sel'] = 0
    if para == 'textura' and estado['modelo'] is not None:
        # arranca junto al modelo: las texturas suelen estar ahí
        exp['dir'] = os.path.dirname(
            os.path.abspath(MODELOS[estado['indice']]))
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
        elif exp.get('para') == 'textura':
            modelo = estado['modelo']
            if modelo is not None:
                if e == '(texturas originales)':
                    modelo.imagen = None      # vuelven los materiales
                else:
                    modelo.imagen = os.path.join(exp['dir'], e)
            estado['modo'] = 'editar'
            refrescar_ui()
            info.texto = "textura: %s" % (
                e if e != '(texturas originales)' else 'originales')
            return
        else:
            nombrar['ruta'] = os.path.join(exp['dir'], e)
            nombrar['texto'] = os.path.splitext(e)[0]
            nombrar['para'] = 'modelo'
            estado['modo'] = 'nombre'
    if estado['modo'] == 'explorar':
        _pintar_explorador()
    elif estado['modo'] == 'nombre':
        _pintar_nombre()
    else:
        refrescar_ui()


def _pintar_nombre():
    if nombrar['para'] == 'anim':
        info.texto = ("nombre de la animación (ENTER guarda, "
                      "ESC cancela)")
    else:
        base = os.path.basename(nombrar['ruta'])
        info.texto = "nombre para %s (ENTER confirma, ESC cancela)" \
            % base
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
        if nombrar['para'] == 'anim':
            _guardar_anim_con_nombre()
            return
        ruta = nombrar['ruta']
        MODELOS.append(ruta)
        if nombrar['texto'].strip():
            nombres[ruta] = nombrar['texto'].strip()
        estado['modo'] = 'editar'
        cargar_modelo(len(MODELOS) - 1)


def _guardar_anim_con_nombre():
    """Compila los keyframes si hace falta y guarda
    ``<modelo>.<nombre>.anim.json``."""
    modelo = estado['modelo']
    nombre = nombrar['texto'].strip() or 'mi_anim'
    estado['modo'] = 'editar'
    if len(estado['frames']) >= 2:
        try:
            modelo.crear_animacion(nombre, estado['frames'])
        except ValueError as e:
            refrescar_ui()
            info.texto = str(e)
            return
    if nombre not in modelo.animaciones():
        refrescar_ui()
        info.texto = "necesitás >= 2 keyframes (tecla M)"
        return
    ruta = ruta_anim(MODELOS[estado['indice']], nombre)
    modelo.guardar_animacion(ruta, nombre)
    refrescar_ui()
    info.texto = "animación '%s' guardada" % nombre


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


def _guardar_pose_previa():
    """Copia la pose actual antes de reproducir una animación
    (teclas P/L/T) para que U la pueda restaurar."""
    import json
    modelo = estado['modelo']
    if modelo is not None:
        estado['pose_previa'] = json.loads(
            json.dumps(modelo._pose_actual()))


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
        if MODELOS:
            cargar_modelo((estado['indice'] + 1) % len(MODELOS))
        return
    if tecla == s.s:
        # stop: frena la animación y deja el modelo en el frame actual
        if modelo is not None and modelo.animacion:
            modelo.detener()
            info.texto = "animación detenida (frame actual)"
        return
    if tecla == s.u:
        # volver: restaura la pose previa a la última reproducción
        if modelo is not None:
            modelo.detener()
            if estado['pose_previa'] is not None:
                modelo.aplicar_pose(estado['pose_previa'])
                info.texto = "pose anterior restaurada"
            else:
                modelo.reiniciar_pose()
                info.texto = "pose de carga restaurada"
        return
    if tecla == s.k:
        abrir_explorador('textura')
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
        info.texto = "%d keyframes" % len(estado['frames'])
        return
    elif tecla == s.b:
        estado['frames'] = []
        info.texto = "keyframes vaciados"
        return
    elif tecla == s.p:
        frames = estado['frames']
        if len(frames) < 2:
            info.texto = "necesitás >= 2 keyframes (tecla M)"
            return
        _guardar_pose_previa()
        modelo.crear_animacion('mi_anim', frames)
        modelo.animar('mi_anim', ciclica=True)
        info.texto = "reproduciendo %d keyframes" % len(frames)
        return
    elif tecla == s.j:
        # pide el nombre: 'Fox.correr.anim.json' junto al modelo
        nombrar['para'] = 'anim'
        nombrar['texto'] = modelo.animacion or 'mi_anim'
        estado['modo'] = 'nombre'
        _pintar_nombre()
        return
    elif tecla == s.l:
        anims = anims_del_modelo(MODELOS[estado['indice']])
        if not anims:
            info.texto = "no hay .anim.json para este modelo"
            return
        estado['anim_sel'] = (estado['anim_sel'] + 1) % len(anims)
        ruta = anims[estado['anim_sel']]
        _guardar_pose_previa()
        modelo.animar(modelo.cargar_animacion(ruta), ciclica=True)
        info.texto = "animación: " + os.path.basename(ruta)
        return
    elif tecla == s.t:
        tipo = TIPOS_PROC[estado['proc'] % len(TIPOS_PROC)]
        estado['proc'] += 1
        mapa = mapear_huesos(huesos)
        try:
            _guardar_pose_previa()
            nombre = animacion_procedural(modelo, tipo, mapa=mapa,
                                          usar_ia=True)
            modelo.animar(nombre, ciclica=True)
            info.texto = "procedural: %s (T otra)" % nombre
        except Exception as e:
            info.texto = "no pude generar '%s': %s" % (tipo, e)
        return
    refrescar_ui()


def main(directorio='modelos', ejecutar=True):
    """Abre el editor. ``directorio`` es donde busca los .glb/.gltf
    (por defecto ``modelos/`` en el directorio actual). Con
    ``ejecutar=False`` deja todo listo sin entrar al loop
    (para pruebas o para seguir desde IPython)."""
    global pilas, MODELOS, marcador, panel_der, panel_inf, lista, \
        info, ayuda

    encontrados = buscar_modelos(directorio)
    if not encontrados:
        # también junto al paquete (pip install -e . → raíz del repo)
        raiz = os.path.join(os.path.dirname(__file__), '..',
                            directorio)
        encontrados = buscar_modelos(raiz)
    MODELOS = encontrados

    pilas = pilas3d.iniciar(titulo="pilas3d - editor de personaje")

    pilas.escena.fondo = pilas.colores.gris_oscuro   # fondo de estudio
    piso = pilas.actores.Piso(tamano=30, divisiones=30)
    piso.color = pilas.colores.gris
    pilas.luces.direccional.ambiente = 0.6

    marcador = pilas.actores.Esfera(radio=0.08)
    marcador.color = pilas.colores.rojo

    # Layout de dos áreas: la escena 3D se dibuja solo en `area_3d`;
    # los paneles negros llevan los textos (lateral y abajo).
    panel_der = pilas.actores.Panel(color=pilas.colores.negro)
    panel_inf = pilas.actores.Panel(color=pilas.colores.negro)

    lista = pilas.actores.Texto("", tamano=12, ancho=PANEL - 16)
    info = pilas.actores.Texto("", tamano=15)
    info.color = pilas.colores.amarillo
    ayuda = pilas.actores.Texto(
        "N: modelo - flechas + X/Y/Z + <-/->: rotar hueso - "
        "G/C/R: pose\n"
        "M/W/B: keyframes - P: play - S: stop - U: volver - "
        "J/L: animaciones\n"
        "A: cargar .glb - K: textura - T: procedural - "
        "botón derecho: cámara",
        x=10, y=PIE - 50, tamano=12)

    organizar_layout()
    pilas.tareas.siempre(0.5, organizar_layout)   # sigue el resize
    pilas.tareas.siempre(0, MarcadorHueso().actualizar)

    if pilas.ventana is not None:
        pilas.ventana.push_handlers(on_key_press=_al_pulsar_overlay,
                                    on_text=_al_texto_overlay)

    pilas.escena.cuando_pulsa_tecla = al_pulsar
    if MODELOS:
        cargar_modelo(0)
    else:
        # escena vacía: el usuario carga el primero con A
        info.texto = ("no hay .glb/.gltf en '%s/' - apretá A y "
                      "buscá un modelo" % directorio)
        lista.texto = ""

    camara = pilas.escena.camara
    camara.posicion = (0, 2.2, 4.5)
    camara.objetivo = (0, 1, 0)
    camara.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

    if ejecutar:
        pilas.ejecutar()
    return pilas


def cli():
    """Punto de entrada del comando ``pilas3d-editor``."""
    main()
