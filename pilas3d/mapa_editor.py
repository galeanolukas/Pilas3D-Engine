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

- el mouse es solo cámara: cualquier botón + drag orbita, rueda zoom,
  espacio + mover el mouse también orbita
- ENTER o B: poner bloque / prop / colina en la celda marcada
  (CTRL+click hace lo mismo como atajo)
- X: sacar el bloque/prop - Q/E: subir/bajar la columna o vértice
- ←/→ o números 1-5: tipo de bloque en la paleta
- S: marcar/quitar el punto de inicio (spawn) bajo el cursor
- G: guardar (al path actual o pide nombre) - O: guardar como...
- L: explorador para cargar cualquier .mapa.json/.terreno.json
- R: gira el prop 45° - D: agarra/suelta el prop para moverlo
- F/V: subir/bajar el prop - Z/C: achicar/agrandar (paleta props)
- N: mapa nuevo (vacío)           - T: terreno procedural de base
- M: paleta bloques <-> props (modelos .glb/.obj de modelos/props/)

Modo terreno (Y: voxels <-> terreno heightmap, *.terreno.json):

- ENTER o B: colina bajo el cursor - X: pozo (lago si hay agua)
- P: pinta celdas con la baldosa elegida - 1-3 o ←/→: baldosa
- Z/C: tamaño del brush - W: poner/sacar el agua - T: lomas azar
- U: cicla packs de texturas (texturas/ y pilas3d/data/texturas/)
- H: aplica el heightmap del pack como relieve del terreno
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
          'archivo': None, 'agarrado': None,
          # modo terreno: heightmap suave en vez de voxels
          'escenario': 'voxels',   # 'voxels' | 'terreno'
          'terreno': None, 'brush': 2, 'tile': 0}
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
guias = []


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


def _celda_terreno(origen, direccion):
    """Cruza el rayo del mouse con el heightmap del Terreno y
    devuelve la celda (i, k) — dos pasadas: contra el plano base y
    luego contra la altura real del punto, para precisión."""
    t = estado['terreno']
    if t is None:
        return None
    ox, oy, oz = origen
    dx, dy, dz = direccion
    if dy >= 0:
        return None
    tt = (t.y - oy) / dy
    px, pz = ox + dx * tt, oz + dz * tt
    h = t.altura_suelo(px, pz)
    if h is not None:
        tt = (h - oy) / dy
        px, pz = ox + dx * tt, oz + dz * tt
    li = (px - t.x) / t.tamano_celda + t.celdas / 2.0
    lk = (pz - t.z) / t.tamano_celda + t.celdas / 2.0
    i, k = int(math.floor(li)), int(math.floor(lk))
    if 0 <= i < t.celdas and 0 <= k < t.celdas:
        return i, k
    return None


def refrescar_cursor():
    """Recalcula la celda apuntada por el mouse y mueve el marcador."""
    if pilas.ventana is None:
        return
    camara = pilas.escena.camara
    origen, direccion = camara.rayo_desde_mouse()
    if estado['escenario'] == 'terreno':
        celda = _celda_terreno(
            (origen.x, origen.y, origen.z),
            (direccion.x, direccion.y, direccion.z))
        estado['golpe'] = None
        estado['celda'] = celda
        if celda is not None:
            i, k = celda
            t = estado['terreno']
            px = t.x + (i + 0.5 - t.celdas / 2.0) * t.tamano_celda
            pz = t.z + (k + 0.5 - t.celdas / 2.0) * t.tamano_celda
            py = t.altura_suelo(px, pz) or t.y
            marcador.posicion = (px, py + 0.3, pz)
            marcador.transparencia = 0
            ag = estado['agarrado']
            if ag is not None:
                ag.posicion = (px, float(py), pz)
            elif estado['paleta'] == 'props':
                prop = _prop_cercano_xyz(px, py, pz, 2.5)
                if prop is not None:
                    marcador.posicion = (prop.x, prop.y + 0.4, prop.z)
        else:
            marcador.transparencia = 100
        return
    if estado['mundo'] is None:
        return
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
    if celda is None or (estado['escenario'] == 'voxels'
                         and not _dentro(*celda)):
        return
    if estado['paleta'] == 'props':
        if estado['agarrado'] is not None:
            _soltar_prop()
        else:
            _poner_prop(celda)
        return
    if estado['escenario'] == 'terreno':
        i, k = celda[0], celda[-1]
        estado['terreno'].montana(i, k, radio=estado['brush'],
                                  altura=0.6)
    else:
        estado['mundo'].poner_bloque(*celda, TIPOS[estado['tipo']])
    _info_extra()


def _poner_prop(celda):
    """Coloca el prop elegido parado sobre la celda (centro)."""
    if not PROPS:
        info.texto = "no hay props en modelos/props/"
        return
    ruta = PROPS[estado['prop']]
    if ruta.lower().endswith(('.glb', '.gltf')):
        actor = pilas.actores.ModeloGLTF(ruta)
    else:
        actor = pilas.actores.Modelo(ruta)
    if estado['escenario'] == 'terreno':
        x, y, z = _punto_terreno(celda)
        actor.posicion = (x, y, z)
    else:
        i, j, k = celda
        actor.posicion = (i + 0.5, float(j), k + 0.5)
    _autoescala_prop(actor)
    estado['props'].append(actor)
    _info_extra()


def _punto_terreno(celda):
    """Centro de la celda (i, k) del terreno en coordenadas de mundo."""
    i, k = celda
    t = estado['terreno']
    x = t.x + (i + 0.5 - t.celdas / 2.0) * t.tamano_celda
    z = t.z + (k + 0.5 - t.celdas / 2.0) * t.tamano_celda
    y = t.altura_suelo(x, z)
    return x, (y if y is not None else t.y), z


def _prop_cercano(celda, radio=1.6):
    """El prop más cercano al centro de la celda (o None)."""
    if celda is None:
        return None
    if estado['escenario'] == 'terreno':
        x, y, z = _punto_terreno(celda)
        return _prop_cercano_xyz(x, y, z, radio)
    i, j, k = celda
    return _prop_cercano_xyz(i + 0.5, j + 0.5, k + 0.5, radio)


def _prop_cercano_xyz(cx, cy, cz, radio=1.6):
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
    """D: toma el prop bajo el cursor; vuelve a soltar con D/ENTER."""
    if estado['agarrado'] is not None:
        _soltar_prop()
        return
    prop = _prop_cercano(estado['celda'], 2.5)
    if prop is None:
        info.texto = "no hay prop cerca del cursor"
        return
    estado['agarrado'] = prop
    prop.transparencia = 60          # fantasma mientras se arrastra
    info.texto = "moviendo %s - D/ENTER suelta" % \
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
    if estado['escenario'] == 'terreno':
        celda = estado['celda']
        if celda is not None:
            estado['terreno'].pozo(celda[0], celda[-1],
                                   radio=estado['brush'],
                                   profundidad=0.6)
            _info_extra()
        return
    golpe = estado['golpe']
    if golpe:
        estado['mundo'].sacar_bloque(*golpe)
        _info_extra()


def _esculpir(delta):
    """Sube (delta>0) o baja (delta<0) la columna/vértice bajo el
    cursor — terraformar rápido sin picar de a uno."""
    celda = estado['celda']
    if celda is None:
        return
    if estado['escenario'] == 'terreno':
        t = estado['terreno']
        if delta > 0:
            t.subir(celda[0], celda[-1], 0.25)
        else:
            t.bajar(celda[0], celda[-1], 0.25)
        _info_extra()
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


def al_click(x, y, boton, mod):
    """El mouse es solo para orbitar: poner/sacar va por teclado
    (ENTER/B y X). ``CTRL+click`` queda como atajo de precisión."""
    if estado['modo'] != 'editar':
        return None
    from pyglet.window import mouse, key
    # fuera del area 3D (paneles laterales/inferior) no se edita
    ax, ay, aw, ah = pilas.ventana.area_3d or (0, 0, 10 ** 9, 10 ** 9)
    if not (ax <= x < ax + aw and ay <= y < ay + ah):
        return None
    if boton == mouse.LEFT and (mod & key.MOD_CTRL):
        _poner_bloque()
        return True
    if boton == mouse.MIDDLE and (mod & key.MOD_CTRL):
        _sacar_bloque()
        return True
    return None


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
    # guia de controles: columnas repartidas por todo el panel
    paso = (w - 20) / float(len(guias))
    for n, g in enumerate(guias):
        g.x = 10 + n * paso
        g.y = 40


def _tiles_terreno():
    t = estado['terreno']
    return t._tiles if t is not None else []


def refrescar_ui():
    if estado['escenario'] == 'terreno' \
            and estado['paleta'] == 'bloques':
        tiles = _tiles_terreno()
        lineas = ['TERRENO - baldosas (Y voxels, M props)', '']
        for n, tile in enumerate(tiles):
            marca = '>> ' if n == estado['tile'] else '   '
            lineas.append('%s%s' % (marca, tile))
        lineas.append('')
        lineas.append('brush: %d | agua: %s' % (
            estado['brush'],
            estado['terreno'].agua if estado['terreno'] else '-'))
        pack = getattr(estado['terreno'], '_material_nombre',
                       None) if estado['terreno'] else None
        lineas.append('pack: %s (U cicla, H altura)' % (
            pack or 'baldosas'))
        nspawn = 'sí' if estado['spawn'] else 'no'
        lineas.append('spawn: %s | props: %d' % (nspawn,
                                               len(estado['props'])))
        lista.texto = '\n'.join(lineas)
        _info_extra()
        return
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
    archivo = estado['archivo'] or '(sin guardar)'
    if estado['escenario'] == 'terreno':
        tiles = _tiles_terreno()
        sel = tiles[estado['tile']] if tiles else '-'
        info.texto = "%s | terreno %s | celda: %s | brush %d" % (
            archivo, sel, celda, estado['brush'])
        return
    nb = len(estado['mundo'].bloques) if estado['mundo'] else 0
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
    if estado['escenario'] == 'terreno':
        pilas.mapas.guardar_terreno(ruta, estado['terreno'],
                                    nombre=nombre,
                                    spawn=estado['spawn'],
                                    props=props)
    else:
        pilas.mapas.guardar(ruta, estado['mundo'], nombre=nombre,
                            spawn=estado['spawn'], props=props)
    estado['archivo'] = ruta
    return ruta


def guardar_mapa(nombre):
    """Guarda con nombre en ``mapas/`` (el caso típico)."""
    ext = '.terreno.json' if estado['escenario'] == 'terreno' \
        else '.mapa.json'
    return _guardar_en(os.path.join(_dir_mapas(), nombre + ext),
                       nombre)


def _vaciar_escena():
    estado['agarrado'] = None
    for p in estado['props']:
        p.eliminar()
    estado['props'] = []
    if estado['mundo'] is not None:
        estado['mundo'].eliminar()
        estado['mundo'] = None
    if estado['terreno'] is not None:
        estado['terreno'].eliminar()
        estado['terreno'] = None


def nuevo_mapa():
    _vaciar_escena()
    if estado['escenario'] == 'terreno':
        estado['terreno'] = pilas.actores.Terreno(celdas=MITAD * 2)
    else:
        estado['mundo'] = pilas.actores.Mundo()
    estado['spawn'] = None
    estado['archivo'] = None
    marca_spawn.transparencia = 100
    refrescar_ui()


def cargar_mapa(ruta):
    _vaciar_escena()
    esc = pilas.mapas.cargar(ruta)
    if type(esc).__name__ == 'Terreno':
        estado['terreno'] = esc
        estado['mundo'] = None
        estado['escenario'] = 'terreno'
    else:
        estado['mundo'] = esc
        estado['terreno'] = None
        estado['escenario'] = 'voxels'
    estado['props'] = esc.props
    estado['archivo'] = ruta
    estado['spawn'] = esc.spawn
    if esc.spawn:
        marca_spawn.posicion = esc.spawn
        marca_spawn.transparencia = 0
    else:
        marca_spawn.transparencia = 100
    refrescar_ui()


def _ciclar_pack():
    """U en modo terreno: recorre los packs de ``pilas.materiales``
    y tras el último vuelve a las baldosas por celda."""
    t = estado['terreno']
    if t is None:
        return
    packs = pilas.materiales.lista()
    if not packs:
        info.texto = "sin packs: bajalos a texturas/<nombre>/"
        return
    actual = getattr(t, '_material_nombre', None)
    n = packs.index(actual) if actual in packs else -1
    n += 1
    if n >= len(packs):
        t.aplicar_material(None)
        info.texto = "terreno: baldosas por celda"
    else:
        t.aplicar_material(packs[n])
        info.texto = "material: %s" % packs[n]
    refrescar_ui()


def _terreno_procedural():
    """Lomas y un lago aleatorios sobre el Terreno del editor."""
    import random
    t = estado['terreno']
    if t is None:
        return
    for _ in range(5):
        t.montana(random.randrange(t.celdas),
                  random.randrange(t.celdas),
                  radio=random.randrange(2, 6),
                  altura=random.uniform(0.8, 2.5))
    i, k = random.randrange(t.celdas), random.randrange(t.celdas)
    t.pozo(i, k, radio=3, profundidad=1.6)
    t.pintar_zona(i, k, 3, 'agua')
    if t.agua is None:
        t.agua = 0.4
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
    mapas = [f for f in ent
             if f.endswith('.mapa.json') or f.endswith('.terreno.json')]
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
    if tecla == s.ENTER or tecla == s.b:
        _poner_bloque()
    elif tecla in digitos and estado['paleta'] == 'bloques':
        if estado['escenario'] == 'terreno':
            tiles = _tiles_terreno()
            if tiles:
                estado['tile'] = digitos.index(tecla) % len(tiles)
        else:
            estado['tipo'] = digitos.index(tecla)
        refrescar_ui()
    elif tecla == s.IZQUIERDA or tecla == s.DERECHA:
        d = -1 if tecla == s.IZQUIERDA else 1
        if estado['paleta'] == 'props' and PROPS:
            estado['prop'] = (estado['prop'] + d) % len(PROPS)
        elif estado['escenario'] == 'terreno':
            tiles = _tiles_terreno()
            if tiles:
                estado['tile'] = (estado['tile'] + d) % len(tiles)
        else:
            estado['tipo'] = (estado['tipo'] + d) % len(TIPOS)
        refrescar_ui()
    elif tecla == s.m:
        estado['paleta'] = 'props' if estado['paleta'] == 'bloques' \
            else 'bloques'
        refrescar_ui()
    elif tecla == s.y:
        # voxels <-> terreno: el mundo queda, el terreno se crea al
        # pasar por primera vez (ambos pueden convivir en la escena)
        if estado['escenario'] == 'terreno':
            estado['escenario'] = 'voxels'
            if estado['mundo'] is None:
                estado['mundo'] = pilas.actores.Mundo()
        else:
            estado['escenario'] = 'terreno'
            if estado['terreno'] is None:
                estado['terreno'] = pilas.actores.Terreno(
                    celdas=MITAD * 2)
        estado['archivo'] = None
        refrescar_ui()
        info.texto = "modo " + estado['escenario']
    elif tecla == s.p and estado['escenario'] == 'terreno':
        celda = estado['celda']
        tiles = _tiles_terreno()
        if celda is not None and tiles:
            estado['terreno'].pintar_zona(celda[0], celda[-1],
                                          estado['brush'],
                                          tiles[estado['tile']])
            _info_extra()
    elif tecla == s.w and estado['escenario'] == 'terreno':
        t = estado['terreno']
        if t is not None:
            t.agua = None if t.agua is not None else 0.4
            info.texto = "agua: %s" % (t.agua if t.agua is not None
                                       else 'no')
    elif tecla == s.u and estado['escenario'] == 'terreno':
        _ciclar_pack()
    elif tecla == s.h and estado['escenario'] == 'terreno':
        t = estado['terreno']
        hm = getattr(getattr(t, 'material', None), 'heightmap',
                     None)
        if t is not None and hm:
            t.desde_heightmap(hm)
            info.texto = "relieve desde el heightmap del pack"
        else:
            info.texto = "sin pack con heightmap (U cambia)"
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
    elif tecla == s.z and estado['escenario'] == 'terreno' \
            and estado['paleta'] == 'bloques':
        estado['brush'] = max(1, estado['brush'] - 1)
        _info_extra()
    elif tecla == s.c and estado['escenario'] == 'terreno' \
            and estado['paleta'] == 'bloques':
        estado['brush'] = min(10, estado['brush'] + 1)
        _info_extra()
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
        if estado['escenario'] == 'terreno':
            _terreno_procedural()
        else:
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
    if estado['escenario'] == 'terreno':
        x, y, z = _punto_terreno(celda)
        estado['spawn'] = (x, y + 1.0, z)
    else:
        i, j, k = celda
        estado['spawn'] = (i + 0.5, float(j + 1), k + 0.5)
    marca_spawn.posicion = estado['spawn']
    marca_spawn.transparencia = 0
    info.texto = "spawn marcado en %s" % (estado['spawn'],)


def main(directorio='mapas', ejecutar=True):
    """Abre el editor de mapas. Devuelve ``pilas``."""
    global pilas, marcador, marca_spawn, lista, info
    global panel_der, panel_inf, guias

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
    del guias[:]
    for txt in (
            "ENTER/B: poner - X: sacar\n"
            "drag o espacio: orbitar",
            "M: paleta - 1-5: elegir\n"
            "R: girar - D: agarrar",
            "F/V Z/C: alto/escala\n"
            "Q/E: columna - S: spawn",
            "T: base - N: nuevo\n"
            "G/O: guardar - L: cargar",
            "Y: terreno - P: pinta\n"
            "Z/C,W: brush,agua\n"
            "U/H: pack/heightmap"):
        guias.append(pilas.actores.Texto(txt, tamano=10))

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
    # cualquier botón + drag orbita (el mouse ya no pone bloques);
    # espacio + mover el mouse sigue funcionando sin click
    botones = (pilas.simbolos.BOTON_IZQUIERDO |
               pilas.simbolos.BOTON_MEDIO |
               pilas.simbolos.BOTON_DERECHO)
    camara.usar_control_orbital(boton=botones,
                                tecla=pilas.simbolos.ESPACIO)

    if ejecutar:
        pilas.ejecutar()
    return pilas


def cli():
    """Punto de entrada del comando ``pilas3d-mapas``."""
    main()
