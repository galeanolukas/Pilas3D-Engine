# -*- encoding: utf-8 -*-
"""pilas3d-mapas: editor de mapas de bloques (voxels).

Misma interfaz que el editor de personajes: vista 3D grande, panel
lateral con la paleta y panel inferior con info. El mapa se guarda
en ``mapas/<nombre>.mapa.json`` y los juegos lo cargan con
``pilas.mapas.cargar(ruta)``.

    pilas3d-mapas                # comando (pip install -e .)

    >>> import pilas3d.mapa_editor
    >>> pilas3d.mapa_editor.main()

Controles:

- click izquierdo: poner bloque   - click medio o X: sacar bloque
- espacio + mover mouse: orbitar (click derecho + drag también)
  rueda: acercar/alejar
- ←/→ o números 1-5: tipo de bloque en la paleta
- S: marcar/quitar el punto de inicio (spawn) bajo el cursor
- G: guardar (al path actual o pide nombre) - O: guardar como...
- L: explorador para cargar cualquier .mapa.json
- R: gira el prop 45° - D: agarra/suelta el prop para moverlo
- F/V: subir/bajar el prop - Z/C: achicar/agrandar (paleta props)
- N: mapa nuevo (vacío)           - T: terreno procedural de base
- M: paleta bloques <-> props (modelos .glb/.obj de modelos/props/)
- Q / E: subir / bajar la columna bajo el cursor (esculpir terreno)
"""

import glob
import math
import os

import pilas3d

pilas = None

MITAD = 12          # grilla 24x24 centrada en el origen
ALTO = 10           # altura máxima de construcción
PANEL = 250
PIE = 90

TIPOS = ['cesped', 'tierra', 'piedra', 'ladrillo', 'arena']

estado = {'mundo': None, 'tipo': 0, 'prop': 0, 'props': [],
          'paleta': 'bloques',     # 'bloques' | 'props'
          'spawn': None,
          'celda': None, 'golpe': None, 'modo': 'editar',
          'archivo': None, 'agarrado': None}
nombrar = {'texto': 'nivel'}
exp = {'dir': '.', 'sel': 0, 'entradas': []}


def buscar_props():
    """Modelos estáticos .glb/.gltf/.obj bajo modelos/props/."""
    out = []
    for ext in ('glb', 'gltf', 'obj'):
        out += glob.glob(os.path.join('modelos', 'props', '**',
                                      '*.' + ext), recursive=True)
    return sorted(out)


PROPS = buscar_props()

marcador = marca_spawn = lista = info = panel_der = panel_inf = None


# -- cursor / picking ---------------------------------------------------

def _celda_suelo(origen, direccion):
    """Si el rayo no toca bloque, cae al plano y=0 (base del mapa)."""
    ox, oy, oz = origen
    dx, dy, dz = direccion
    if dy >= 0 or oy <= 0:
        return None
    t = -oy / dy
    return (math.floor(ox + dx * t), 0, math.floor(oz + dz * t))


def _dentro(i, j, k):
    return -MITAD <= i < MITAD and -MITAD <= k < MITAD and \
        0 <= j < ALTO


def refrescar_cursor():
    """Recalcula la celda apuntada por el mouse y mueve el marcador."""
    if pilas.ventana is None or estado['mundo'] is None:
        return
    camara = pilas.escena.camara
    origen, direccion = camara.rayo_desde_mouse()
    bloque, ady = estado['mundo'].disparar_bloque(
        (origen.x, origen.y, origen.z),
        (direccion.x, direccion.y, direccion.z), alcance=40)
    estado['golpe'] = bloque
    estado['celda'] = ady or _celda_suelo(origen, direccion)
    if estado['celda'] and _dentro(*estado['celda']):
        i, j, k = estado['celda']
        marcador.posicion = (i + 0.5, j + 0.5, k + 0.5)
        marcador.transparencia = 0
        ag = estado['agarrado']
        if ag is not None:
            ag.posicion = (i + 0.5, float(j), k + 0.5)
        elif estado['paleta'] == 'props':
            # el marcador salta al prop bajo el cursor: es el objetivo
            # de D (agarrar), R (girar), F/V/Z/C y X (borrar)
            prop = _prop_cercano(estado['celda'], 2.5)
            if prop is not None:
                marcador.posicion = (prop.x, prop.y + 0.4, prop.z)
    else:
        marcador.transparencia = 100


def _autoescala_prop(actor, objetivo=1.6):
    """Normaliza el prop a ~``objetivo`` unidades de alto."""
    pos = getattr(actor, '_pos', None)
    if pos:
        ys = pos[1::3]
        alto = max(ys) - min(ys)
        if alto:
            actor.escala = objetivo / alto


def _poner_bloque():
    celda = estado['celda']
    if celda is None or not _dentro(*celda):
        return
    if estado['paleta'] == 'props':
        if estado['agarrado'] is not None:
            _soltar_prop()
        else:
            _poner_prop(celda)
        return
    estado['mundo'].poner_bloque(*celda, TIPOS[estado['tipo']])
    _info_extra()


def _poner_prop(celda):
    """Coloca el prop elegido parado sobre la celda (centro)."""
    if not PROPS:
        info.texto = "no hay props en modelos/props/"
        return
    ruta = PROPS[estado['prop']]
    i, j, k = celda
    if ruta.lower().endswith(('.glb', '.gltf')):
        actor = pilas.actores.ModeloGLTF(ruta)
    else:
        actor = pilas.actores.Modelo(ruta)
    actor.posicion = (i + 0.5, float(j), k + 0.5)
    _autoescala_prop(actor)
    estado['props'].append(actor)
    _info_extra()


def _prop_cercano(celda, radio=1.6):
    """El prop más cercano al centro de la celda (o None)."""
    if celda is None:
        return None
    i, j, k = celda
    cx, cy, cz = i + 0.5, j + 0.5, k + 0.5
    mejor, dist2 = None, radio * radio
    for p in estado['props']:
        d = (p.x - cx) ** 2 + (p.y - cy) ** 2 + (p.z - cz) ** 2
        if d < dist2:
            mejor, dist2 = p, d
    return mejor


def _prop_objetivo():
    """El prop agarrado o, si no, el más cercano al cursor."""
    return estado['agarrado'] or _prop_cercano(estado['celda'], 2.5)


def _agarrar_prop():
    """D: toma el prop bajo el cursor; vuelve a soltar con D/click."""
    if estado['agarrado'] is not None:
        _soltar_prop()
        return
    prop = _prop_cercano(estado['celda'], 2.5)
    if prop is None:
        info.texto = "no hay prop cerca del cursor"
        return
    estado['agarrado'] = prop
    prop.transparencia = 60          # fantasma mientras se arrastra
    info.texto = "moviendo %s - D/click suelta" % \
        os.path.basename(getattr(prop, 'ruta', 'prop'))


def _soltar_prop():
    prop = estado['agarrado']
    if prop is None:
        return
    estado['agarrado'] = None
    prop.transparencia = 0
    info.texto = "prop soltado en %s" % (prop.posicion,)
    _info_extra()


def _mover_prop_y(delta):
    prop = _prop_objetivo()
    if prop is not None:
        prop.y = prop.y + delta
        _info_extra()


def _escalar_prop(factor):
    prop = _prop_objetivo()
    if prop is not None:
        prop.escala = max(0.05, prop.escala * factor)
        _info_extra()


def _sacar_bloque():
    if estado['paleta'] == 'props':
        prop = estado['agarrado'] or _prop_cercano(estado['celda'])
        if prop is not None:
            if prop is estado['agarrado']:
                estado['agarrado'] = None
            prop.eliminar()
            estado['props'].remove(prop)
            _info_extra()
            return
    golpe = estado['golpe']
    if golpe:
        estado['mundo'].sacar_bloque(*golpe)
        _info_extra()


def _esculpir(delta):
    """Sube (delta>0) o baja (delta<0) la columna bajo el cursor —
    terraformar rápido sin picar bloque por bloque."""
    celda = estado['celda']
    if celda is None:
        return
    mundo = estado['mundo']
    i, _, k = celda
    techo = mundo._columnas.get((i, k), 0)
    if delta > 0:
        if _dentro(i, techo, k):
            mundo.poner_bloque(i, techo, k, TIPOS[estado['tipo']])
    elif techo > 0:
        mundo.sacar_bloque(i, techo - 1, k)
    _info_extra()


def al_click(x, y, boton, _mod):
    if estado['modo'] != 'editar':
        return None
    from pyglet.window import mouse
    # fuera del area 3D (paneles laterales/inferior) no se edita
    ax, ay, aw, ah = pilas.ventana.area_3d or (0, 0, 10 ** 9, 10 ** 9)
    if not (ax <= x < ax + aw and ay <= y < ay + ah):
        return None
    # boton es el valor del boton pulsado (no mascara): comparar ==.
    # Con &, un driver que reporte el derecho como 5/7/9 lo tomaria
    # como izquierdo y colocaria un bloque al orbitar.
    if boton == mouse.LEFT:
        _poner_bloque()
        return True
    if boton == mouse.MIDDLE:
        _sacar_bloque()
        return True
    return None                 # derecho: orbitar


# -- UI -------------------------------------------------------------------

def organizar_layout():
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
    info.y = 70


def refrescar_ui():
    if estado['paleta'] == 'props':
        lineas = ['paleta de PROPS (M bloques)', '']
        if not PROPS:
            lineas.append('   (sin modelos en modelos/props/)')
        for n, ruta in enumerate(PROPS):
            marca = '>> ' if n == estado['prop'] else '   '
            nom = os.path.basename(ruta)[:24]
            lineas.append('%s%s' % (marca, nom))
    else:
        lineas = ['paleta de bloques (M props)', '']
        for n, tipo in enumerate(TIPOS):
            marca = '>> ' if n == estado['tipo'] else '   '
            lineas.append('%s%s' % (marca, tipo))
    lineas.append('')
    nspawn = 'sí' if estado['spawn'] else 'no'
    lineas.append('spawn: %s | props: %d' % (nspawn,
                                           len(estado['props'])))
    lista.texto = '\n'.join(lineas)
    _info_extra()


def _info_extra():
    celda = estado['celda']
    nb = len(estado['mundo'].bloques) if estado['mundo'] else 0
    archivo = estado['archivo'] or '(sin guardar)'
    if estado['paleta'] == 'props':
        sel = os.path.basename(PROPS[estado['prop']]) if PROPS \
            else '(sin props)'
    else:
        sel = TIPOS[estado['tipo']]
    info.texto = "%s | %s | celda: %s | bloques: %d" % (
        archivo, sel, celda, nb)


# -- guardar / cargar -----------------------------------------------------

def _dir_mapas():
    d = 'mapas'
    os.makedirs(d, exist_ok=True)
    return d


def _guardar_en(ruta, nombre=None):
    """Escribe el mapa en el path dado (cualquier directorio)."""
    props = []
    for p in estado['props']:
        props.append({'ruta': getattr(p, 'ruta', ''),
                      'x': p.x, 'y': p.y, 'z': p.z,
                      'escala': getattr(p, 'escala', 1.0),
                      'rotacion_y': getattr(p, 'rotacion_y', 0)})
    pilas.mapas.guardar(ruta, estado['mundo'], nombre=nombre,
                        spawn=estado['spawn'], props=props)
    estado['archivo'] = ruta
    return ruta


def guardar_mapa(nombre):
    """Guarda con nombre en ``mapas/`` (el caso típico)."""
    return _guardar_en(os.path.join(_dir_mapas(),
                                    nombre + '.mapa.json'), nombre)


def _vaciar_escena():
    estado['agarrado'] = None
    for p in estado['props']:
        p.eliminar()
    estado['props'] = []
    if estado['mundo'] is not None:
        estado['mundo'].eliminar()


def nuevo_mapa():
    _vaciar_escena()
    estado['mundo'] = pilas.actores.Mundo()
    estado['spawn'] = None
    estado['archivo'] = None
    marca_spawn.transparencia = 100
    refrescar_ui()


def cargar_mapa(ruta):
    _vaciar_escena()
    mundo = pilas.mapas.cargar(ruta)
    estado['mundo'] = mundo
    estado['props'] = mundo.props
    estado['archivo'] = ruta
    estado['spawn'] = mundo.spawn
    if mundo.spawn:
        marca_spawn.posicion = mundo.spawn
        marca_spawn.transparencia = 0
    else:
        marca_spawn.transparencia = 100
    refrescar_ui()


def terreno_base():
    """Rellena con el heightmap procedural del Mundo (pasto/tierra/
    piedra) dentro de los límites del editor."""
    mundo = estado['mundo']
    mundo.generar_terreno(ancho=MITAD * 2, profundidad=MITAD * 2,
                          altura=3, semilla=estado['tipo'])
    # recorta lo que quede fuera de la grilla del editor
    for (i, j, k) in [b for b in mundo.bloques if not _dentro(*b)]:
        del mundo.bloques[(i, j, k)]
    mundo._sucio = True
    refrescar_ui()


# -- modos overlay: nombre para guardar / lista de mapas -----------------

def _pintar_nombre():
    info.texto = "nombre del mapa (ENTER guarda, ESC cancela)"
    lista.texto = '>> %s_' % nombrar['texto']


def _listar_dir():
    """Entradas del explorador: '..', dirs y *.mapa.json."""
    try:
        ent = sorted(os.listdir(exp['dir']))
    except OSError:
        ent = []
    dirs = ['[%s]' % d for d in ent
            if os.path.isdir(os.path.join(exp['dir'], d))]
    mapas = [f for f in ent if f.endswith('.mapa.json')]
    exp['entradas'] = ['..'] + dirs + mapas
    exp['sel'] = min(exp['sel'], len(exp['entradas']) - 1)


def _pintar_explorador():
    info.texto = "cargar mapa - dir: %s (ESC cancela)" \
        % os.path.abspath(exp['dir'])
    ini = max(0, min(exp['sel'] - 7, len(exp['entradas']) - 14))
    lista.texto = '\n'.join(
        ('>> ' if ini + k == exp['sel'] else '   ') + e
        for k, e in enumerate(exp['entradas'][ini:ini + 14]))


def _abrir_lista_mapas():
    exp['dir'] = _dir_mapas() if os.path.isdir('mapas') else '.'
    exp['sel'] = 0
    _listar_dir()
    estado['modo'] = 'mapas'
    _pintar_explorador()


def _tecla_nombre(t):
    s = pilas.simbolos
    if t == s.ESCAPE:
        estado['modo'] = 'editar'
        refrescar_ui()
    elif t == s.BACKSPACE:
        nombrar['texto'] = nombrar['texto'][:-1]
        _pintar_nombre()
    elif t == s.ENTER:
        nombre = nombrar['texto'].strip() or 'nivel'
        estado['modo'] = 'editar'
        ruta = guardar_mapa(nombre)
        refrescar_ui()
        info.texto = "mapa guardado: %s" % ruta


def _tecla_mapas(t):
    s = pilas.simbolos
    if t == s.ESCAPE:
        estado['modo'] = 'editar'
        refrescar_ui()
        return
    if t == s.ARRIBA:
        exp['sel'] = (exp['sel'] - 1) % len(exp['entradas'])
    elif t == s.ABAJO:
        exp['sel'] = (exp['sel'] + 1) % len(exp['entradas'])
    elif t == s.ENTER:
        e = exp['entradas'][exp['sel']]
        if e == '..':
            exp['dir'] = os.path.dirname(
                os.path.abspath(exp['dir']))
            exp['sel'] = 0
        elif e.startswith('['):
            exp['dir'] = os.path.join(exp['dir'], e[1:-1])
            exp['sel'] = 0
        else:
            estado['modo'] = 'editar'
            cargar_mapa(os.path.join(exp['dir'], e))
            info.texto = "mapa cargado: " + \
                os.path.basename(estado['archivo'])
            return
    _listar_dir()
    _pintar_explorador()


def _al_pulsar_overlay(simbolo, _mod):
    if estado['modo'] == 'editar':
        return None
    if estado['modo'] == 'nombre':
        _tecla_nombre(simbolo)
    elif estado['modo'] == 'mapas':
        _tecla_mapas(simbolo)
    return True


def _al_texto_overlay(texto):
    if estado['modo'] != 'nombre':
        return None
    if texto >= ' ' and texto != '\r':
        nombrar['texto'] += texto
        _pintar_nombre()
    return True


def al_pulsar(tecla):
    s = pilas.simbolos
    if estado['modo'] != 'editar':
        return
    digitos = [s._1, s._2, s._3, s._4, s._5]
    if tecla in digitos and estado['paleta'] == 'bloques':
        estado['tipo'] = digitos.index(tecla)
        refrescar_ui()
    elif tecla == s.IZQUIERDA or tecla == s.DERECHA:
        d = -1 if tecla == s.IZQUIERDA else 1
        if estado['paleta'] == 'props' and PROPS:
            estado['prop'] = (estado['prop'] + d) % len(PROPS)
        else:
            estado['tipo'] = (estado['tipo'] + d) % len(TIPOS)
        refrescar_ui()
    elif tecla == s.m:
        estado['paleta'] = 'props' if estado['paleta'] == 'bloques' \
            else 'bloques'
        refrescar_ui()
    elif tecla == s.q:
        _esculpir(+1)
    elif tecla == s.e:
        _esculpir(-1)
    elif tecla == s.r and estado['paleta'] == 'props':
        prop = _prop_objetivo()
        if prop is not None:
            prop.rotacion_y = (prop.rotacion_y + 45) % 360
            info.texto = "prop girado a %d°" % prop.rotacion_y
    elif tecla == s.d and estado['paleta'] == 'props':
        _agarrar_prop()
    elif tecla == s.f and estado['paleta'] == 'props':
        _mover_prop_y(+0.5)
    elif tecla == s.v and estado['paleta'] == 'props':
        _mover_prop_y(-0.5)
    elif tecla == s.z and estado['paleta'] == 'props':
        _escalar_prop(0.85)
    elif tecla == s.c and estado['paleta'] == 'props':
        _escalar_prop(1.18)
    elif tecla == s.x:
        _sacar_bloque()
    elif tecla == s.s:
        _marcar_spawn()
    elif tecla == s.g:
        if estado['archivo']:
            # ya tiene path -> guarda directo (seguir editando después)
            _guardar_en(estado['archivo'])
            info.texto = "guardado en %s" % estado['archivo']
        else:
            estado['modo'] = 'nombre'
            _pintar_nombre()
    elif tecla == s.o:
        # "guardar como..." -> siempre pide nombre nuevo
        nombrar['texto'] = os.path.splitext(os.path.splitext(
            os.path.basename(
                estado['archivo'] or 'nivel.mapa.json'))[0])[0]
        estado['modo'] = 'nombre'
        _pintar_nombre()
    elif tecla == s.l:
        _abrir_lista_mapas()
    elif tecla == s.n:
        nuevo_mapa()
    elif tecla == s.t:
        terreno_base()


def _marcar_spawn():
    celda = estado['celda']
    if celda is None:
        return
    if estado['spawn'] is not None:
        estado['spawn'] = None
        marca_spawn.transparencia = 100
        info.texto = "spawn quitado"
        return
    i, j, k = celda
    estado['spawn'] = (i + 0.5, float(j + 1), k + 0.5)
    marca_spawn.posicion = estado['spawn']
    marca_spawn.transparencia = 0
    info.texto = "spawn marcado en %s" % (estado['spawn'],)


def main(directorio='mapas', ejecutar=True):
    """Abre el editor de mapas. Devuelve ``pilas``."""
    global pilas, marcador, marca_spawn, lista, info
    global panel_der, panel_inf

    pilas = pilas3d.iniciar(titulo="pilas3d - editor de mapas")
    pilas.escena.fondo = pilas.colores.gris_oscuro
    pilas.luces.direccional.ambiente = 0.6

    marcador = pilas.actores.Esfera(radio=0.18)
    marcador.color = pilas.colores.rojo
    marca_spawn = pilas.actores.Esfera(radio=0.3)
    marca_spawn.color = pilas.colores.celeste
    marca_spawn.transparencia = 100

    # referencias visuales: rejilla 1 celda = 1 línea, ejes de color
    pilas.actores.Piso(tamano=MITAD * 2, divisiones=MITAD * 2)
    pilas.actores.Ejes(largo=MITAD)

    panel_der = pilas.actores.Panel(color=pilas.colores.negro)
    panel_inf = pilas.actores.Panel(color=pilas.colores.negro)
    lista = pilas.actores.Texto("", tamano=13, ancho=PANEL - 16)
    info = pilas.actores.Texto("", tamano=15)
    info.color = pilas.colores.amarillo
    pilas.actores.Texto(
        "click: poner - medio/X: sacar - espacio+mouse: orbitar - rueda\n"
        "1-5 o <-/->: elegir - M: bloques/props - R: girar - D: agarrar\n"
        "F/V: subir/bajar prop - Z/C: escala - Q/E: columna - S: spawn\n"
        "T: terreno - N: nuevo - G: guardar - O: como - L: cargar - ESC",
        x=10, y=52, tamano=12)

    organizar_layout()
    pilas.tareas.siempre(0.5, organizar_layout)
    pilas.tareas.siempre(0, refrescar_cursor)

    estado['mundo'] = pilas.actores.Mundo()
    refrescar_ui()

    if pilas.ventana is not None:
        pilas.ventana.push_handlers(
            on_key_press=_al_pulsar_overlay,
            on_text=_al_texto_overlay,
            on_mouse_press=al_click)
    pilas.escena.cuando_pulsa_tecla = al_pulsar

    camara = pilas.escena.camara
    camara.posicion = (18, 14, 18)
    camara.objetivo = (0, 0, 0)
    camara.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO,
                                tecla=pilas.simbolos.ESPACIO)

    if ejecutar:
        pilas.ejecutar()
    return pilas


def cli():
    """Punto de entrada del comando ``pilas3d-mapas``."""
    main()
