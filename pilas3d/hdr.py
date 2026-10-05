# -*- encoding: utf-8 -*-
"""Decodificador Radiance ``.hdr`` (RGBE) para fondos HDR.

Formato equirectangular 2:1 — el que distribuye Poly Haven::

    ancho, alto, datos = hdr.cargar('mirrored_hall_2k.hdr')
    # datos: array('f') RGBA lineal, fila 0 = cenit

Sin dependencias: parsea el encabezado de texto y los scanlines
(``32-bit_rle_rgbe`` moderno o plano) y expande RGBE -> float con
``f = valor * 2^(exponente - 136)``.

También extrae datos de iluminación del mapa (``promedio`` y
``direccion_sol``) — la base del efecto "la luz sale del fondo".
"""

import array
import math
import os
import struct

_cache = {}

# Caché binario junto al .hdr (``<archivo>.hdr.cache``): guarda los
# floats ya decodificados — la primera carga de un 4K tarda ~9s pero
# las siguientes leen el dump directo (<1s). Se regenera si el .hdr
# es más nuevo que el .cache.
_MAGIA = b'P3DHDR01'

# RGBE: exponente compartido; 136 = 128 (bias) + 8 (mantisa /256)
_TABLA_E = [0.0] + [math.ldexp(1.0, e - 136) for e in range(1, 256)]


def cargar(ruta):
    """Decodifica un ``.hdr`` a floats. Cachea por ruta absoluta.

    Devuelve ``(ancho, alto, array('f'))`` — RGBA lineal listo para
    subir como ``GL_RGBA16F``. La fila 0 es el cenit (v=0 del domo).
    """
    ruta = os.path.abspath(ruta)
    if ruta not in _cache:
        _cache[ruta] = _cargar_con_cache(ruta)
    return _cache[ruta]


def _cargar_con_cache(ruta):
    cache = ruta + '.cache'
    try:
        if os.path.getmtime(cache) >= os.path.getmtime(ruta):
            res = _leer_cache(cache)
            if res is not None:
                return res
    except OSError:
        pass
    with open(ruta, 'rb') as f:
        res = _decodificar(f.read())
    _guardar_cache(cache, res)
    return res


def _leer_cache(cache):
    with open(cache, 'rb') as f:
        cab = f.read(16)
        if len(cab) != 16 or cab[:8] != _MAGIA:
            return None
        ancho, alto = struct.unpack('<II', cab[8:16])
        datos = array.array('f')
        try:
            datos.fromfile(f, ancho * alto * 4)
        except EOFError:
            return None          # cache truncado: redecodificar
        return ancho, alto, datos


def _guardar_cache(cache, res):
    ancho, alto, datos = res
    try:
        with open(cache, 'wb') as f:
            f.write(_MAGIA + struct.pack('<II', ancho, alto))
            datos.tofile(f)
    except OSError:
        pass                     # dir de solo lectura: sin cache


def _decodificar(buf):
    # encabezado: líneas de texto hasta una línea vacía
    pos = 0
    while True:
        fin = buf.index(b'\n', pos)
        if not buf[pos:fin].strip():
            pos = fin + 1
            break
        pos = fin + 1
    # línea de resolución: p. ej. "-Y 1024 +X 2048"
    fin = buf.index(b'\n', pos)
    res = buf[pos:fin].split()
    pos = fin + 1
    alto, ancho = int(res[1]), int(res[3])
    invertir = res[0] == b'+Y'           # la mayoría es "-Y"

    filas = []
    for _ in range(alto):
        fila, pos = _scanline(buf, pos, ancho)
        filas.append(fila)
    if invertir:
        filas.reverse()

    datos = array.array('f')
    ext = datos.extend
    for fila in filas:
        for i in range(0, ancho * 4, 4):
            f = _TABLA_E[fila[i + 3]]
            ext((fila[i] * f, fila[i + 1] * f, fila[i + 2] * f, 1.0))
    return ancho, alto, datos


def _scanline(buf, pos, ancho):
    """Una fila RGBE. Devuelve ``(bytes(ancho*4), nueva_pos)``."""
    if ancho < 8 or ancho > 0x7fff or buf[pos] != 2 or \
            buf[pos + 1] != 2 or (buf[pos + 2] & 0x80):
        # formato plano: 4 bytes por píxel
        return buf[pos:pos + ancho * 4], pos + ancho * 4
    pos += 4                            # marca 2,2 + ancho (2 bytes)
    fila = bytearray(ancho * 4)
    for canal in range(4):
        ch = bytearray(ancho)
        x = 0
        while x < ancho:
            n = buf[pos]
            pos += 1
            if n > 128:                 # corrida: repite el byte
                n -= 128
                ch[x:x + n] = buf[pos:pos + 1] * n
                pos += 1
            else:                       # literales
                ch[x:x + n] = buf[pos:pos + n]
                pos += n
            x += n
        fila[canal::4] = ch
    return bytes(fila), pos


# -- extracción de iluminación -------------------------------------------

def _luminancia(datos, i):
    return datos[i] * 0.3 + datos[i + 1] * 0.6 + datos[i + 2] * 0.1


def promedio(ancho, alto, datos, paso=8):
    """Color medio del mapa (muestreado cada ``paso`` píxeles)."""
    tr = tg = tb = n = 0.0
    for i in range(0, ancho * alto * 4, 4 * paso):
        tr += datos[i]
        tg += datos[i + 1]
        tb += datos[i + 2]
        n += 1
    return (tr / n, tg / n, tb / n)


def direccion_sol(ancho, alto, datos):
    """Dirección unitaria hacia la zona más brillante del mapa.

    Centroide ponderado de los píxeles sobre el 50% del máximo —
    más robusto que el píxel suelto (una lámpara pequeña no gana).
    Devuelve también ``(direccion, color_sol)``.
    """
    lmax = 0.0
    for i in range(0, len(datos), 4):
        l = _luminancia(datos, i)
        if l > lmax:
            lmax = l
    umbral = lmax * 0.5
    dx = dy = dz = 0.0
    tr = tg = tb = w = 0.0
    for i in range(0, len(datos), 4):
        l = _luminancia(datos, i)
        if l < umbral:
            continue
        px = (i // 4) % ancho
        py = (i // 4) // ancho
        lat = ((py + 0.5) / alto) * math.pi    # v=0 es el cenit
        lon = ((px + 0.5) / ancho) * 2 * math.pi
        dx += math.sin(lat) * math.cos(lon) * l
        dy += math.cos(lat) * l
        dz += math.sin(lat) * math.sin(lon) * l
        tr += datos[i] * l
        tg += datos[i + 1] * l
        tb += datos[i + 2] * l
        w += l
    if w == 0:
        return (0.0, 1.0, 0.0), (1.0, 1.0, 1.0)
    norma = math.sqrt(dx * dx + dy * dy + dz * dz)
    m = max(tr, tg, tb) or 1.0
    return (dx / norma, dy / norma, dz / norma), \
        (tr / m, tg / m, tb / m)
