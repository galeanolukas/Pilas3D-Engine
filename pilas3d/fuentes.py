# -*- encoding: utf-8 -*-
"""Fuentes tipográficas (.ttf/.otf) para los textos del motor.

``Texto``/``Menu``/``Globo`` aceptan ``fuente=`` con dos formas:

- ``fuente='DejaVu Sans'`` — nombre de una familia ya instalada
- ``fuente='arcade.ttf'`` — archivo de fuente; se busca en cwd,
  ``fonts/`` del proyecto y ``pilas3d/data/fonts/`` (las del motor),
  se registra con pyglet y se usa su familia real

    >>> t = pilas.actores.Texto('hola', fuente='DejaVuSansMono.ttf')
    >>> t.fuente = 'mi_fuente.ttf'          # cambia en vivo
    >>> pilas.fuentes.lista()               # ttfs disponibles
"""

import os
import struct

_EXT = ('.ttf', '.otf', '.ttc')
_REGISTRADAS = {}        # ruta resuelta -> nombre de familia


def _resolver(ruta):
    """Busca la fuente: ruta literal, ``fonts/`` del proyecto y
    ``pilas3d/data/fonts/`` — también por basename en subcarpetas
    (``'Arcade.ttf'`` encuentra ``fonts/arcade/Arcade.ttf``)."""
    base = os.path.dirname(os.path.abspath(__file__))
    dirs = ('fonts', os.path.join(base, 'data', 'fonts'))
    for cand in (ruta,
                 os.path.join('fonts', ruta),
                 os.path.join(dirs[1], ruta),
                 os.path.join(base, 'data', ruta)):
        if os.path.exists(cand):
            return cand
    nombre = os.path.basename(ruta)
    for d in dirs:
        if os.path.isdir(d):
            for raiz, _subs, archivos in os.walk(d):
                if nombre in archivos:
                    return os.path.join(raiz, nombre)
    return ruta                       # que el llamador decida


def _familia_ttf(ruta):
    """Nombre de familia del .ttf/.otf, leído de la tabla ``name``
    (registro 1) — pyglet registra el archivo pero no dice cómo se
    llama la familia, y el Label la pide por nombre."""
    try:
        with open(ruta, 'rb') as f:
            data = f.read(1 << 20)          # las tablas van al inicio
        if len(data) < 12:
            return None
        # colecciones .ttc: saltar al primer directorio sfnt
        if data[:4] == b'ttcf':
            base_sfnt = struct.unpack('>I', data[12:16])[0]
        else:
            base_sfnt = 0
        num = struct.unpack('>H', data[base_sfnt + 4:base_sfnt + 6])[0]
        base = None
        for i in range(num):
            rec = base_sfnt + 12 + i * 16
            if data[rec:rec + 4] == b'name':
                base = struct.unpack('>I', data[rec + 8:rec + 12])[0]
                break
        if base is None:
            return None
        count = struct.unpack('>H', data[base + 2:base + 4])[0]
        stroff = base + struct.unpack('>H', data[base + 4:base + 6])[0]
        mejor = None
        for i in range(count):
            rec = base + 6 + i * 12
            pid, _eid, _lid, nid, largo, off = struct.unpack(
                '>6H', data[rec:rec + 12])
            if nid != 1:                    # 1 = nombre de familia
                continue
            raw = data[stroff + off:stroff + off + largo]
            if pid == 3:                    # Windows: UTF-16BE
                return raw.decode('utf-16-be', 'replace')
            if mejor is None:               # Mac/u otros: latin-1
                mejor = raw.decode('latin-1', 'replace')
        return mejor
    except (OSError, IndexError, struct.error):
        return None


def familia(nombre):
    """Convierte ``fuente=`` en el ``font_name`` que entiende pyglet.

    Devuelve el nombre tal cual si ya es una familia, o registra el
    archivo y devuelve su familia real (cacheada). Si no se puede
    resolver, devuelve ``nombre`` — pyglet cae a la fuente default.
    """
    if not nombre:
        return None
    if not str(nombre).lower().endswith(_EXT):
        return nombre
    ruta = _resolver(str(nombre))
    if ruta in _REGISTRADAS:
        return _REGISTRADAS[ruta]
    fam = _familia_ttf(ruta) or nombre
    try:
        import pyglet
        pyglet.font.add_file(ruta)
        _REGISTRADAS[ruta] = fam
    except Exception:
        _REGISTRADAS[ruta] = nombre
    return _REGISTRADAS[ruta]


class Fuentes(object):
    """Punto de acceso de ``pilas.fuentes``."""

    def __init__(self, pilas):
        self.pilas = pilas

    def familia(self, nombre):
        """Igual que :func:`familia` — para adelantar el registro."""
        return familia(nombre)

    def lista(self):
        """Fuentes en ``fonts/`` del proyecto y en
        ``pilas3d/data/fonts/`` (las del motor), recursivo — son
        basenames listos para ``fuente=``: ``'Arcade.ttf'``."""
        base = os.path.dirname(os.path.abspath(__file__))
        out = []
        for d in ('fonts', os.path.join(base, 'data', 'fonts')):
            if not os.path.isdir(d):
                continue
            for raiz, _subs, archivos in os.walk(d):
                if '__MACOSX' in raiz:
                    continue
                out += [f for f in archivos
                        if f.lower().endswith(_EXT)]
        return sorted(set(out))
