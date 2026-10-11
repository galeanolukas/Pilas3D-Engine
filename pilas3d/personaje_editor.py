# -*- encoding: utf-8 -*-
"""Editor de personajes-sprite: arma el ``.personaje.json`` de un
``PersonajeSprite`` viendo el billboard caminar en 3D en vivo —
la misma interfaz del editor de huesos (``pilas3d-editor``): panel
lateral con la lista de slots y barra de estado abajo.

    pilas3d-personaje                          # ejemplos del motor
    pilas3d-personaje vikingo.png              # hoja suelta
    pilas3d-personaje vikingo.personaje.json   # manifiesto

Teclas:
  flechas ↑/↓   elegir slot (↑/↓ también mueven al personaje:
                para probar el movimiento sin tocar el editor
                sirven las 4 flechas libremente)
  + / -         ajustar el valor del slot (fila, grilla, vel...)
  WASD/flechas  mueve el sprite — se ve la fila según la dirección
  ESPACIO       previsualiza el slot (pose o estado)
  M             espejar la dirección desde otra (cicla por fuentes)
  E / B         crea / borra estados (atacar, morir, saltar...)
  C / B         apila una capa (ropa, cabello) / la quita
  X / K         estado cíclico / quedarse en el último cuadro
  N             siguiente personaje (manifiestos y hojas de ejemplo)
  O             explorador: carga una hoja .png/.jpg o .json externa
  G             guarda el .personaje.json
  ESC           salir   -   botón derecho: órbita de cámara
"""

import argparse
import glob
import os
import sys

import pilas3d
from pilas3d.actores.personaje_sprite import PersonajeSprite  # noqa: F401
from pilas3d.actores.personaje_capas import PersonajeCapas  # noqa: F401

pilas = None      # instancia de pilas3d.iniciar, la crea main()

DIRECCIONES = ['abajo', 'izquierda', 'derecha', 'arriba']
NOMBRES_ESTADO = ['atacar', 'morir', 'saltar', 'correr', 'especial']
PROPS = ['columnas', 'filas', 'variantes', 'variante',
         'cuadro_quieto', 'velocidad', 'ancho', 'alto']

# hojas que trae el motor para empezar sin archivos propios; la
# mayoría viene de pilas-engine 1.x con la grilla que su actor
# declaraba (maton.png: 3x4 con filas norte/este/sur/oeste)
_TODAS_A_0 = {'abajo': 0, 'izquierda': 0, 'derecha': 0, 'arriba': 0}
EJEMPLOS = [
    # direccionales: una fila por sentido
    ('rpg/maton.png',
     dict(columnas=3, filas=4,
          direcciones={'arriba': 0, 'derecha': 1, 'abajo': 2,
                       'izquierda': 3},
          cuadro_quieto=1, ancho=0.7, alto=1.4)),
    ('rpg/calvo.png',
     dict(columnas=3, filas=4,
          direcciones={'arriba': 0, 'derecha': 1, 'abajo': 2,
                       'izquierda': 3},
          cuadro_quieto=1, ancho=0.7, alto=1.4)),
    ('pacman.png',
     dict(columnas=4, filas=4,
          direcciones={'izquierda': 0, 'derecha': 1, 'arriba': 2,
                       'abajo': 3},
          ancho=0.7, alto=0.7)),
    ('sprite_personaje.png',
     dict(columnas=6, filas=6, ancho=1.2, alto=1.2)),
    # tiras de una sola fila: todas las direcciones usan la fila 0
    ('fantasma.png',
     dict(columnas=8, filas=1, direcciones=_TODAS_A_0,
          ancho=0.8, alto=0.8)),
    ('pingu.png',
     dict(columnas=10, filas=1, direcciones=_TODAS_A_0,
          ancho=0.9, alto=1.0)),
    ('vaca_corriendo.png',
     dict(columnas=10, filas=1, direcciones=_TODAS_A_0,
          ancho=2.4, alto=1.0)),
    ('marcianitos/martian.png',
     dict(columnas=12, filas=1, direcciones=_TODAS_A_0,
          ancho=0.8, alto=0.7)),
    ('shaolin/camina.png',
     dict(columnas=4, filas=1, direcciones=_TODAS_A_0,
          ancho=1.1, alto=1.4)),
    ('shaolin/parado.png',
     dict(columnas=4, filas=1, direcciones=_TODAS_A_0,
          ancho=1.1, alto=1.4)),
    ('cooperativista/camina.png',
     dict(columnas=4, filas=1, direcciones=_TODAS_A_0,
          ancho=1.0, alto=1.1)),
    ('cooperativista/alerta.png',
     dict(columnas=2, filas=1, direcciones=_TODAS_A_0,
          ancho=1.0, alto=1.0)),
    ('moneda.png',
     dict(columnas=8, filas=1, direcciones=_TODAS_A_0,
          ancho=0.6, alto=0.6)),
    ('banana.png',
     dict(columnas=2, filas=1, direcciones=_TODAS_A_0,
          ancho=0.7, alto=0.5)),
    ('spacekids.png',
     dict(columnas=2, filas=1, direcciones=_TODAS_A_0,
          ancho=0.9, alto=0.9)),
    ('explosion.png',
     dict(columnas=7, filas=1, direcciones=_TODAS_A_0,
          ancho=1.0, alto=1.0)),
]

estado = {'pj': None, 'sel': 0, 'indice': -1, 'modo': 'editar',
          'salida': None, 'hoja': None}

exp = {'dir': os.path.expanduser('~'), 'sel': 0, 'entradas': []}

PANEL = 280   # ancho del panel lateral en px
PIE = 110     # alto del panel inferior en px

# actores de UI, creados por main()
panel_der = panel_inf = lista = info = ayuda = ayuda2 = None


# -- slots ------------------------------------------------------------

def _slots():
    """Filas del panel: propiedades + direcciones + estados."""
    pj = estado['pj']
    filas = [('prop', p) for p in PROPS]
    filas += [('dir', d) for d in DIRECCIONES]
    if pj is not None:
        filas += [('estado', n) for n in pj._estados
                  if n not in DIRECCIONES]
        for i in range(len(pj._capas)):
            filas.append(('capa', i))
            filas.append(('capa_var', i))
            filas.append(('capa_vars', i))
            filas.append(('capa_sync', i))
    return filas


def _valor_prop(pj, nombre):
    if nombre == 'columnas':
        return pj.columnas
    if nombre == 'filas':
        return pj.filas
    if nombre == 'variantes':
        return pj.variantes
    if nombre == 'variante':
        return pj.variante
    if nombre == 'cuadro_quieto':
        return pj.cuadro_quieto
    if nombre == 'velocidad':
        return pj.velocidad
    if nombre == 'ancho':
        return pj.ancho
    return pj.alto


def _ajustar_prop(pj, nombre, delta):
    if nombre == 'columnas':
        pj.columnas = min(64, max(1, pj.columnas + delta))
        pj.cuadro %= pj._paso
        pj.cuadro_quieto %= pj._paso
    elif nombre == 'filas':
        pj.filas = min(32, max(1, pj.filas + delta))
        pj._fila %= pj.filas
        for e in pj._estados.values():
            e['fila'] %= pj.filas
        for d in pj._mapa:
            pj._mapa[d] %= pj.filas
    elif nombre == 'variantes':
        pj.variantes = min(pj.columnas, max(1, pj.variantes + delta))
        pj.variante %= pj.variantes
    elif nombre == 'variante':
        pj.variante = (pj.variante + delta) % pj.variantes
    elif nombre == 'cuadro_quieto':
        pj.cuadro_quieto = (pj.cuadro_quieto + delta) % pj._paso
    elif nombre == 'velocidad':
        pj.velocidad = min(30, max(1, pj.velocidad + delta))
    elif nombre == 'ancho':
        pj.ancho = round(min(5.0, max(0.2, pj.ancho + delta * 0.1)), 2)
    else:
        pj.alto = round(min(5.0, max(0.2, pj.alto + delta * 0.1)), 2)
    pj._encuadrar()


def _detalle_slot(pj, tipo, nombre):
    if tipo == 'prop':
        return '%s: %s' % (nombre, _valor_prop(pj, nombre))
    if tipo == 'dir':
        if nombre in pj._espejar:
            return '%s ~ %s' % (nombre, pj._espejar[nombre])
        if nombre in pj._mapa:
            return '%s -> fila %d' % (nombre, pj._mapa[nombre])
        return '%s (sin fila)' % nombre
    if tipo == 'capa':
        c = pj._capas[nombre]
        sync = ' [sync]' if c.seguir_variante else ''
        return 'capa %d: %s%s' % (
            nombre + 1, os.path.basename(str(c.imagen)), sync)
    if tipo == 'capa_var':
        c = pj._capas[nombre]
        return '  variante: %d / %d' % (c.variante + 1, c.variantes)
    if tipo == 'capa_vars':
        c = pj._capas[nombre]
        return '  variantes: %d' % c.variantes
    if tipo == 'capa_sync':
        c = pj._capas[nombre]
        return '  seguir base: %s' % ('si' if c.seguir_variante else 'no')
    e = pj._estados[nombre]
    extras = []
    if e['velocidad']:
        extras.append('v%d' % e['velocidad'])
    extras.append('ciclica' if e['ciclica'] else '1 vez')
    if e['quedarse']:
        extras.append('quedarse')
    return '%s -> fila %d (%s)' % (nombre, e['fila'],
                                  ', '.join(extras))


# -- UI --------------------------------------------------------------

def organizar_layout():
    """Reparte la ventana: vista 3D a la izquierda, panel lateral
    para la lista de slots y panel inferior para la info."""
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
    # la ayuda reparte su texto en dos columnas sobre el ancho
    # disponible de la barra inferior (vista 3D + panel)
    ayuda2.x = max(10, int(w * 0.52))
    ayuda2.y = PIE - 50


def refrescar_ui():
    pj = estado['pj']
    if pj is None:
        lista.texto = ''
        return
    slots = _slots()
    estado['sel'] %= len(slots)
    ini = max(0, min(estado['sel'] - 7, len(slots) - 14))
    lineas = []
    for k, (tipo, nombre) in enumerate(slots[ini:ini + 14]):
        marca = '>> ' if ini + k == estado['sel'] else '   '
        lineas.append(('%s%s' % (marca,
                                _detalle_slot(pj, tipo, nombre)))[:30])
        # separadores visuales entre grupos
        if ini + k < len(slots) - 1:
            sig = slots[ini + k + 1][0]
            if sig != tipo:
                lineas.append('   ' + '-' * 20)
    lista.texto = '\n'.join(lineas)
    # info: archivo, grilla real y celda en píxeles
    grilla = 'grilla %dx%d' % (pj.columnas, pj.filas)
    if pj.variantes > 1:
        grilla += ' x%d var' % pj.variantes
    celda = ''
    if estado['hoja']:
        try:
            img = pilas.imagenes.cargar(pj.imagen)
            cw, ch = img.width / pj.columnas, img.height / pj.filas
            celda = ' celda %gx%g' % (cw, ch)
            if cw != int(cw) or ch != int(ch):
                celda += ' !grilla no divide parejo!'
        except Exception:
            celda = ' (hoja ilegible)'
    tipo, nombre = slots[estado['sel']]
    if tipo == 'capa':
        c = pj._capas[nombre]
        info.texto = '%s | capa %d: %s | grilla %dx%d (%d var)%s' % (
            estado['hoja'] or os.path.basename(str(pj.imagen)),
            nombre + 1, os.path.basename(str(c.imagen)),
            c.columnas, c.filas, c.variantes, celda)
    elif tipo == 'capa_var':
        c = pj._capas[nombre]
        info.texto = 'capa %d (%s) | color activo: %d de %d (+/- para cambiar color)' % (
            nombre + 1, os.path.basename(str(c.imagen)),
            c.variante + 1, c.variantes)
    elif tipo == 'capa_vars':
        c = pj._capas[nombre]
        info.texto = 'capa %d (%s) | total variantes en hoja: %d (+/- para ajustar grilla)' % (
            nombre + 1, os.path.basename(str(c.imagen)), c.variantes)
    elif tipo == 'capa_sync':
        c = pj._capas[nombre]
        info.texto = 'capa %d (%s) | seguir color del personaje: %s (+/- o ESPACIO para alternar)' % (
            nombre + 1, os.path.basename(str(c.imagen)),
            'si' if c.seguir_variante else 'no')
    else:
        info.texto = '%s | %s | %s%s' % (
            estado['hoja'] or os.path.basename(str(pj.imagen)),
            _detalle_slot(pj, tipo, nombre), grilla, celda)
    ayuda.texto = (
        "Arriba/Abajo: elegir slot - +/-: ajustar valor\n"
        "WASD/flechas: mover - ESPACIO: preview - M: espejo\n"
        "E/B: estado +/- - X: ciclica - K: quedarse")
    ayuda2.texto = (
        "N: siguiente - O: cargar hoja/json\n"
        "C: agregar capa - B: quitar capa/estado\n"
        "+/- en capa: su color - T: webp - G: guardar - ESC: salir")


# -- carga -------------------------------------------------------------

def cargar(ruta, **kw):
    """Instancia el PersonajeSprite de una hoja o manifiesto."""
    if estado['pj'] is not None:
        estado['pj'].eliminar()
    if ruta.lower().endswith('.json'):
        pj = pilas.actores.PersonajeCapas(ruta, y=0.9)
        estado['salida'] = ruta
    else:
        kw.setdefault('columnas', 4)
        kw.setdefault('filas', 4)
        kw.setdefault('ancho', 1.4)
        kw.setdefault('alto', 1.8)
        pj = pilas.actores.PersonajeCapas(
            ruta, y=0.9, velocidad=8, **kw)
        salida = os.path.splitext(ruta)[0] + '.personaje.json'
        carpeta = os.path.dirname(salida)
        if carpeta and not os.path.isdir(carpeta):
            # ejemplo del motor ('rpg/maton.png'): el json va al
            # cwd, la hoja la resuelve el fallback a pilas3d/data
            salida = os.path.basename(salida)
        estado['salida'] = salida
    pj.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)
    estado['pj'] = pj
    estado['hoja'] = os.path.basename(str(ruta))
    estado['sel'] = 0
    cam = pilas.escena.camara
    cam.seguir_a(pj, modo='tercera', distancia=4.5, altura=2.5)
    refrescar_ui()


def buscar_personajes():
    """*.personaje.json del cwd + las hojas de ejemplo del motor."""
    encontrados = sorted(glob.glob('*.personaje.json'))
    for r in sorted(glob.glob('**/*.personaje.json', recursive=True)):
        if r not in encontrados:
            encontrados.append(r)
    return encontrados


def siguiente_personaje():
    """N: cicla manifiestos del cwd y después las hojas ejemplo."""
    manis = buscar_personajes()
    n_total = len(manis) + len(EJEMPLOS)
    estado['indice'] = (estado['indice'] + 1) % n_total
    i = estado['indice']
    if i < len(manis):
        cargar(manis[i])
    else:
        nombre, kw = EJEMPLOS[i - len(manis)]
        cargar(nombre, **kw)


# -- explorador de archivos (hoja externa) -----------------------------

def _listar_dir():
    try:
        ent = sorted(os.listdir(exp['dir']))
    except OSError:
        ent = []
    dirs = ['[%s]' % d for d in ent
            if os.path.isdir(os.path.join(exp['dir'], d))]
    archivos = [f for f in ent if f.lower().endswith(
        ('.png', '.jpg', '.jpeg', '.json', '.webp'))]
    exp['entradas'] = ['..'] + dirs + archivos
    exp['sel'] = max(0, min(exp['sel'], len(exp['entradas']) - 1))


def _pintar_explorador():
    titulo = ('Elegir hoja para CAPA (ropa, cabello...)'
              if estado['modo'] == 'explorar_capa'
              else 'Elegir hoja .png/.jpg/.webp o .personaje.json')
    sel_nombre = exp['entradas'][exp['sel']] if exp['entradas'] else ''
    info.texto = ">> %s << | %s - dir: %s" % (sel_nombre, titulo, exp['dir'])
    ini = max(0, min(exp['sel'] - 7, len(exp['entradas']) - 14))
    lineas = []
    for k, e in enumerate(exp['entradas'][ini:ini + 14]):
        marca = '>> ' if ini + k == exp['sel'] else '   '
        e_vis = (e[:25] + '..') if len(e) > 28 else e
        lineas.append(marca + e_vis)
    lista.texto = '\n'.join(lineas)
    ayuda.texto = (
        "ENTER / ESPACIO / ->: seleccionar archivo o carpeta\n"
        "Flechas / rueda: mover seleccion - RePag/AvPag: saltar 10\n"
        "ESC / <-: cancelar y volver a la edicion")
    ayuda2.texto = (
        "Click en la lista: elegir con el mouse\n"
        "Doble click: confirmar seleccion")


def abrir_explorador(para_capa=False):
    estado['modo'] = 'explorar_capa' if para_capa else 'explorar'
    if estado['pj'] is not None:
        try:
            ruta_act = str(estado['pj'].imagen)
            if not os.path.exists(ruta_act):
                from pilas3d import imagenes
                ruta_act = imagenes.resolver(ruta_act)
            if os.path.exists(ruta_act):
                exp['dir'] = os.path.dirname(os.path.abspath(ruta_act))
        except Exception:
            pass
    exp['sel'] = 0
    _listar_dir()
    _pintar_explorador()


def _tecla_explorador(t):
    s = pilas.simbolos
    teclas_elegir = (s.ENTER, getattr(s, 'NUM_ENTER', s.ENTER),
                     getattr(s, 'RETURN', s.ENTER), s.ESPACIO, s.DERECHA)
    teclas_atras = (s.ESCAPE, s.BACKSPACE)
    repag = getattr(s, 'PAGEUP', None)
    avpag = getattr(s, 'PAGEDOWN', None)

    if t in teclas_atras:
        estado['modo'] = 'editar'
    elif t == s.IZQUIERDA:
        padre = os.path.dirname(exp['dir'].rstrip(os.sep))
        if padre and padre != exp['dir']:
            exp['dir'] = padre
            exp['sel'] = 0
            _listar_dir()
        else:
            estado['modo'] = 'editar'
    elif t == s.ARRIBA:
        exp['sel'] = (exp['sel'] - 1) % max(1, len(exp['entradas']))
    elif t == s.ABAJO:
        exp['sel'] = (exp['sel'] + 1) % max(1, len(exp['entradas']))
    elif repag and t == repag:
        exp['sel'] = max(0, exp['sel'] - 10)
    elif avpag and t == avpag:
        exp['sel'] = min(max(0, len(exp['entradas']) - 1), exp['sel'] + 10)
    elif t in teclas_elegir:
        if not exp['entradas']:
            return
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
            destino = estado['modo']
            estado['modo'] = 'editar'
            ruta = os.path.join(exp['dir'], e)
            try:
                if destino == 'explorar_capa':
                    estado['pj'].agregar_capa(ruta)
                    slots = _slots()
                    try:
                        estado['sel'] = slots.index(
                            ('capa', len(estado['pj']._capas) - 1))
                    except ValueError:
                        pass
                    refrescar_ui()
                    info.texto = 'capa agregada: %s (slot capa %d)' % (
                        e, len(estado['pj']._capas))
                    return
                cargar(ruta)
                info.texto = 'cargado: %s' % e
            except Exception as ex:
                refrescar_ui()
                info.texto = 'no se pudo cargar: %s' % ex
            return

    if estado['modo'].startswith('explorar'):
        _pintar_explorador()
    else:
        refrescar_ui()


def _al_pulsar_overlay(simbolo, _mod):
    """En modo explorar consume la tecla (ESC cancela sin salir)."""
    if estado['modo'] == 'editar':
        return None
    _tecla_explorador(simbolo)
    return True


def _al_click_mouse(x, y, boton, _mod):
    if boton != pilas.simbolos.BOTON_IZQUIERDO:
        return None
    if estado['modo'].startswith('explorar'):
        w, h = pilas.ventana.width, pilas.ventana.height
        if x >= w - PANEL and y >= PIE:
            dy = (h - 25) - y
            linea = int(dy // 16)
            ini = max(0, min(exp['sel'] - 7, len(exp['entradas']) - 14))
            idx = ini + linea
            if 0 <= idx < len(exp['entradas']):
                if exp['sel'] == idx:
                    _tecla_explorador(pilas.simbolos.ENTER)
                else:
                    exp['sel'] = idx
                    _pintar_explorador()
            return True
    return None


def _al_scroll_mouse(_x, _y, _sx, sy):
    if estado['modo'].startswith('explorar'):
        if sy > 0:
            exp['sel'] = (exp['sel'] - 1) % max(1, len(exp['entradas']))
        elif sy < 0:
            exp['sel'] = (exp['sel'] + 1) % max(1, len(exp['entradas']))
        _pintar_explorador()
        return True
    return None


# -- teclas principales -------------------------------------------------

def al_pulsar(tecla):
    s = pilas.simbolos
    pj = estado['pj']
    if estado['modo'] != 'editar':
        return                          # el overlay la consumió
    if tecla == s.ESCAPE:
        pilas.terminar()
        return
    if tecla == s.n:
        siguiente_personaje()
        return
    if tecla == s.o:
        abrir_explorador()
        return
    if pj is None:
        return
    if tecla == s.c:
        # elige una hoja y la apila como capa (ropa, cabello...)
        abrir_explorador(para_capa=True)
        return
    slots = _slots()
    tipo, nombre = slots[estado['sel'] % len(slots)]
    if tecla == s.ARRIBA:
        estado['sel'] = (estado['sel'] - 1) % len(slots)
    elif tecla == s.ABAJO:
        estado['sel'] = (estado['sel'] + 1) % len(slots)
    elif tecla in (s.MENOS, s.NUM_MENOS, s.MAS, s.NUM_MAS, s.IGUAL):
        # +/- ajustan el valor; las flechas quedan libres para
        # probar el movimiento (control fusiona WASD + flechas)
        delta = -1 if tecla in (s.MENOS, s.NUM_MENOS) else 1
        if tipo == 'prop':
            _ajustar_prop(pj, nombre, delta)
        elif tipo == 'dir':
            pj._mapa[nombre] = (pj._mapa.get(nombre, 0) + delta) \
                % pj.filas
            pj._espejar.pop(nombre, None)
            pj.definir_direccion(nombre)
        elif tipo in ('capa', 'capa_var'):
            capa = pj._capas[nombre]
            capa.seguir_variante = False
            capa.variante = (capa.variante + delta) % capa.variantes
        elif tipo == 'capa_vars':
            capa = pj._capas[nombre]
            capa.variantes = max(1, min(capa.columnas, capa.variantes + delta))
            capa.variante %= capa.variantes
            capa._encuadrar()
        elif tipo == 'capa_sync':
            capa = pj._capas[nombre]
            capa.seguir_variante = not capa.seguir_variante
            if capa.seguir_variante:
                capa.variante = pj.variante % capa.variantes
        else:
            est = pj._estados[nombre]
            est['fila'] = (est['fila'] + delta) % pj.filas
    elif tecla == s.ESPACIO:
        if tipo == 'dir':
            if nombre in pj._mapa or nombre in pj._espejar:
                pj.definir_direccion(nombre)
        elif tipo == 'estado':
            pj.reproducir_estado(nombre)
        elif tipo in ('capa', 'capa_var'):
            capa = pj._capas[nombre]
            capa.seguir_variante = False
            capa.variante = (capa.variante + 1) % capa.variantes
        elif tipo == 'capa_sync':
            capa = pj._capas[nombre]
            capa.seguir_variante = not capa.seguir_variante
            if capa.seguir_variante:
                capa.variante = pj.variante % capa.variantes
    elif tecla == s.g:
        pj.guardar(estado['salida'])
        info.texto = 'guardado %s' % estado['salida']
        return
    elif tecla == s.t:
        # comprime la hoja a WebP junto al manifest; repointa el
        # actor a la nueva imagen (el motor la lee por gdkpixbuf)
        from pilas3d import imagenes, sprites
        base = os.path.dirname(os.path.abspath(estado['salida']))
        nombre = os.path.splitext(
            os.path.basename(str(pj.imagen)))[0] + '.webp'
        try:
            dest = sprites.a_webp(
                imagenes.resolver(str(pj.imagen)),
                os.path.join(base, nombre))
        except Exception as ex:
            info.texto = 'webp: %s' % ex
            return
        pj.imagen = dest
        pj._textura = None
        estado['hoja'] = nombre
        info.texto = 'hoja -> %s' % nombre
        return
    elif tipo == 'dir' and tecla == s.m:
        # cicla: sin espejo -> espejar desde cada otra dirección
        otras = [d for d in DIRECCIONES if d != nombre]
        act = pj._espejar.get(nombre)
        if act is None:
            pj._espejar[nombre] = otras[0]
        elif act in otras:
            i = otras.index(act) + 1
            if i < len(otras):
                pj._espejar[nombre] = otras[i]
            else:
                del pj._espejar[nombre]
        if nombre in pj._mapa or nombre in pj._espejar:
            pj.definir_direccion(nombre)
    elif tipo in ('capa', 'capa_var', 'capa_vars', 'capa_sync') and tecla == s.b:
        pj.quitar_capa(nombre)
        estado['sel'] = 0
    elif tipo == 'estado':
        est = pj._estados[nombre]
        if tecla == s.x:
            est['ciclica'] = not est['ciclica']
        elif tecla == s.k:
            est['quedarse'] = not est['quedarse']
        elif tecla == s.b:
            del pj._estados[nombre]
            if pj._estado and pj._estado['nombre'] == nombre:
                pj.reproducir_estado(None)
            estado['sel'] = 0
    if tecla == s.e:
        for nom in NOMBRES_ESTADO:
            if nom not in pj._estados:
                pj.agregar_estado(nom, fila=0)
                estado['sel'] = _slots().index(('estado', nom))
                break
    refrescar_ui()


def main(archivo=None, salida=None, ejecutar=True):
    """Abre el editor. Con ``ejecutar=False`` deja todo listo sin
    entrar al loop (para pruebas o para seguir desde IPython)."""
    global pilas, panel_der, panel_inf, lista, info, ayuda, ayuda2

    pilas = pilas3d.iniciar(ancho=800, alto=600,
                            titulo='pilas3d - editor de personaje')

    pilas.escena.fondo = pilas.colores.gris_oscuro
    piso = pilas.actores.Piso(tamano=24, divisiones=24)
    piso.color = pilas.colores.gris

    panel_der = pilas.actores.Panel(color=pilas.colores.negro)
    panel_inf = pilas.actores.Panel(color=pilas.colores.negro)

    lista = pilas.actores.Texto('', tamano=12, ancho=PANEL - 16)
    info = pilas.actores.Texto('', tamano=15)
    info.color = pilas.colores.amarillo
    ayuda = pilas.actores.Texto(
        "↑/↓: elegir slot - +/-: ajustar valor\n"
        "WASD/flechas: mover - ESPACIO: preview - M: espejo\n"
        "E/B: estado +/- - X: cíclica - K: quedarse",
        x=10, y=PIE - 50, tamano=12)
    ayuda2 = pilas.actores.Texto(
        "N: siguiente - O: cargar hoja/json\n"
        "C: agregar capa - B: quitar capa/estado\n"
        "+/- en capa: su color - T: webp - G: guardar - ESC: salir",
        x=10, y=PIE - 50, tamano=12)

    organizar_layout()
    pilas.tareas.siempre(0.5, organizar_layout)

    cam = pilas.escena.camara
    cam.posicion = (0, 2.5, 4.5)
    cam.objetivo = (0, 1, 0)
    cam.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

    if pilas.ventana is not None:
        pilas.ventana.push_handlers(
            on_key_press=_al_pulsar_overlay,
            on_mouse_press=_al_click_mouse,
            on_mouse_scroll=_al_scroll_mouse)

    pilas.escena.cuando_pulsa_tecla = al_pulsar
    if archivo:
        cargar(archivo)
        if salida:
            estado['salida'] = salida
    else:
        siguiente_personaje()

    if ejecutar:
        pilas.ejecutar()
    return pilas


def cli(argv=None):
    ap = argparse.ArgumentParser(
        prog='pilas3d-personaje',
        description='Editor de personajes-sprite (.personaje.json)')
    ap.add_argument('archivo', nargs='?', default=None,
                    help='hoja .png/.jpg o .personaje.json '
                         '(sin archivo: ejemplos del motor)')
    ap.add_argument('-o', '--salida', default=None,
                    help='ruta del .personaje.json a guardar')
    a = ap.parse_args(argv)
    main(a.archivo, salida=a.salida)
    return 0


if __name__ == '__main__':
    sys.exit(cli())
