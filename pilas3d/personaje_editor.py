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
from pilas3d.actores.personaje_sprite import PersonajeSprite

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

PANEL = 250   # ancho del panel lateral en px
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
            return '%s → fila %d' % (nombre, pj._mapa[nombre])
        return '%s (sin fila)' % nombre
    e = pj._estados[nombre]
    extras = []
    if e['velocidad']:
        extras.append('v%d' % e['velocidad'])
    extras.append('cíclica' if e['ciclica'] else '1 vez')
    if e['quedarse']:
        extras.append('quedarse')
    return '%s → fila %d (%s)' % (nombre, e['fila'],
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
    info.texto = '%s | %s | %s%s' % (
        estado['hoja'] or os.path.basename(str(pj.imagen)),
        _detalle_slot(pj, tipo, nombre), grilla, celda)


# -- carga -------------------------------------------------------------

def cargar(ruta, **kw):
    """Instancia el PersonajeSprite de una hoja o manifiesto."""
    if estado['pj'] is not None:
        estado['pj'].eliminar()
    if ruta.lower().endswith('.json'):
        pj = pilas.actores.PersonajeSprite(ruta, y=0.9)
        estado['salida'] = ruta
    else:
        kw.setdefault('columnas', 4)
        kw.setdefault('filas', 4)
        kw.setdefault('ancho', 1.4)
        kw.setdefault('alto', 1.8)
        pj = pilas.actores.PersonajeSprite(
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
        ('.png', '.jpg', '.jpeg', '.json'))]
    exp['entradas'] = ['..'] + dirs + archivos
    exp['sel'] = min(exp['sel'], len(exp['entradas']) - 1)


def _pintar_explorador():
    info.texto = "Elegir hoja .png/.jpg o .personaje.json - dir: %s" \
        % exp['dir']
    ini = max(0, min(exp['sel'] - 7, len(exp['entradas']) - 14))
    lista.texto = '\n'.join(
        ('>> ' if ini + k == exp['sel'] else '   ') + e
        for k, e in enumerate(exp['entradas'][ini:ini + 14]))


def abrir_explorador():
    estado['modo'] = 'explorar'
    if estado['pj'] is not None:
        exp['dir'] = os.path.dirname(
            os.path.abspath(str(estado['pj'].imagen))) or exp['dir']
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
            estado['modo'] = 'editar'
            try:
                cargar(os.path.join(exp['dir'], e))
            except Exception as ex:
                info.texto = 'no se pudo cargar: %s' % ex
            return
    if estado['modo'] == 'explorar':
        _pintar_explorador()
    else:
        refrescar_ui()


def _al_pulsar_overlay(simbolo, _mod):
    """En modo explorar consume la tecla (ESC cancela sin salir)."""
    if estado['modo'] == 'editar':
        return None
    _tecla_explorador(simbolo)
    return True


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
        else:
            est = pj._estados[nombre]
            est['fila'] = (est['fila'] + delta) % pj.filas
    elif tecla == s.ESPACIO:
        if tipo == 'dir':
            if nombre in pj._mapa or nombre in pj._espejar:
                pj.definir_direccion(nombre)
        elif tipo == 'estado':
            pj.reproducir_estado(nombre)
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
        "T: hoja a webp - G: guardar\n"
        "ESC: salir - botón derecho: cámara",
        x=10, y=PIE - 50, tamano=12)

    organizar_layout()
    pilas.tareas.siempre(0.5, organizar_layout)

    cam = pilas.escena.camara
    cam.posicion = (0, 2.5, 4.5)
    cam.objetivo = (0, 1, 0)
    cam.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

    if pilas.ventana is not None:
        pilas.ventana.push_handlers(on_key_press=_al_pulsar_overlay)

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
