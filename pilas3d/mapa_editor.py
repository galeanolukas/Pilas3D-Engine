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
- click derecho + drag: orbitar   - rueda: acercar/alejar
- ←/→ o números 1-5: tipo de bloque en la paleta
- S: marcar/quitar el punto de inicio (spawn) bajo el cursor
- G: guardar con nombre           - L: lista los mapas de mapas/ y carga
- N: mapa nuevo (vacío)           - T: terreno procedural de base
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

estado = {'mundo': None, 'tipo': 0, 'spawn': None, 'props': [],
          'celda': None, 'golpe': None, 'modo': 'editar',
          'mapas': [], 'mapa_sel': 0, 'archivo': None}
nombrar = {'texto': 'nivel'}

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
    else:
        marcador.transparencia = 100


def _poner_bloque():
    celda = estado['celda']
    if celda and _dentro(*celda):
        estado['mundo'].poner_bloque(*celda, TIPOS[estado['tipo']])
        _info_extra()


def _sacar_bloque():
    golpe = estado['golpe']
    if golpe:
        estado['mundo'].sacar_bloque(*golpe)
        _info_extra()


def al_click(x, y, boton, _mod):
    if estado['modo'] != 'editar':
        return None
    from pyglet.window import mouse
    if boton & mouse.LEFT:
        _poner_bloque()
        return True
    if boton & mouse.MIDDLE:
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
    info.y = 58


def refrescar_ui():
    lineas = ['paleta de bloques', '']
    for n, tipo in enumerate(TIPOS):
        marca = '>> ' if n == estado['tipo'] else '   '
        lineas.append('%s%s' % (marca, tipo))
    lineas.append('')
    nspawn = 'sí' if estado['spawn'] else 'no'
    lineas.append('spawn: %s' % nspawn)
    lista.texto = '\n'.join(lineas)
    _info_extra()


def _info_extra():
    celda = estado['celda']
    nb = len(estado['mundo'].bloques) if estado['mundo'] else 0
    archivo = estado['archivo'] or '(sin guardar)'
    info.texto = "%s | tipo: %s | celda: %s | bloques: %d" % (
        archivo, TIPOS[estado['tipo']], celda, nb)


# -- guardar / cargar -----------------------------------------------------

def _dir_mapas():
    d = 'mapas'
    os.makedirs(d, exist_ok=True)
    return d


def guardar_mapa(nombre):
    ruta = os.path.join(_dir_mapas(), nombre + '.mapa.json')
    props = []
    for p in estado['props']:
        props.append({'ruta': getattr(p, 'ruta', ''),
                      'x': p.x, 'y': p.y, 'z': p.z,
                      'escala': getattr(p, 'escala', 1.0)})
    pilas.mapas.guardar(ruta, estado['mundo'], nombre=nombre,
                        spawn=estado['spawn'], props=props)
    estado['archivo'] = ruta
    return ruta


def _vaciar_escena():
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


def _pintar_mapas():
    info.texto = "elegir mapa de mapas/ (ENTER carga, ESC cancela)"
    ini = max(0, min(estado['mapa_sel'] - 7,
                     len(estado['mapas']) - 14))
    lista.texto = '\n'.join(
        ('>> ' if ini + k == estado['mapa_sel'] else '   ') +
        os.path.basename(m)
        for k, m in enumerate(estado['mapas'][ini:ini + 14]))


def _abrir_lista_mapas():
    estado['mapas'] = sorted(glob.glob(
        os.path.join(_dir_mapas(), '*.mapa.json')))
    if not estado['mapas']:
        info.texto = "no hay mapas guardados en mapas/"
        return
    estado['mapa_sel'] = 0
    estado['modo'] = 'mapas'
    _pintar_mapas()


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
    elif t == s.ARRIBA:
        estado['mapa_sel'] = (estado['mapa_sel'] - 1) \
            % len(estado['mapas'])
        _pintar_mapas()
    elif t == s.ABAJO:
        estado['mapa_sel'] = (estado['mapa_sel'] + 1) \
            % len(estado['mapas'])
        _pintar_mapas()
    elif t == s.ENTER:
        estado['modo'] = 'editar'
        cargar_mapa(estado['mapas'][estado['mapa_sel']])
        info.texto = "mapa cargado: " + \
            os.path.basename(estado['archivo'])


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
    if tecla == s.IZQUIERDA:
        estado['tipo'] = (estado['tipo'] - 1) % len(TIPOS)
        refrescar_ui()
    elif tecla == s.DERECHA:
        estado['tipo'] = (estado['tipo'] + 1) % len(TIPOS)
        refrescar_ui()
    elif tecla == s.x:
        _sacar_bloque()
    elif tecla == s.s:
        _marcar_spawn()
    elif tecla == s.g:
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

    panel_der = pilas.actores.Panel(color=pilas.colores.negro)
    panel_inf = pilas.actores.Panel(color=pilas.colores.negro)
    lista = pilas.actores.Texto("", tamano=13, ancho=PANEL - 16)
    info = pilas.actores.Texto("", tamano=15)
    info.color = pilas.colores.amarillo
    pilas.actores.Texto(
        "click: poner - medio/X: sacar - der+drag: orbitar\n"
        "1-5 o <-/->: bloque - S: spawn - T: terreno - N: nuevo\n"
        "G: guardar - L: cargar  →  mapas/<nombre>.mapa.json",
        x=10, y=28, tamano=12)

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
    camara.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

    if ejecutar:
        pilas.ejecutar()
    return pilas


def cli():
    """Punto de entrada del comando ``pilas3d-mapas``."""
    main()
