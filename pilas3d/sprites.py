# -*- encoding: utf-8 -*-
"""Herramienta de hojas de sprites: convierte imágenes de stock
(JPG/PNG con personajes sobre fondo liso) en una hoja PNG con
transparencia lista para ``PersonajeSprite``/``Animacion``.

    python3 -m pilas3d.sprites entrada.jpg -o hoja.png
    pilas3d-sprites entrada.jpg -o hoja.png --margen 4

Qué hace:

- **Fondo automático**: toma el color de las esquinas y vuelve
  transparente todo lo parecido (con borde suave).
- **Sombra horneada**: los grises casi neutros (la sombra que traen
  las fotos/vectores bajo los pies) también se quitan.
- **Grilla automática**: detecta las celdas buscando los huecos
  entre personajes (perfil de proyección); con ``--columnas`` y
  ``--filas`` se usa una grilla regular en vez de auto-detectar.
- **Recentrado**: cada personaje se centra en su celda con los pies
  abajo, para que no "salte" al animar.
- **Manifiesto**: junto al PNG escribe ``hoja.sprites.json`` con
  ``columnas``/``filas`` para leer desde el juego.
- **WebP**: si ``salida`` termina en ``.webp`` la hoja se escribe
  en WebP (~85% menos peso) usando un encoder externo —``cwebp``,
  ImageMagick ``convert`` o ``ffmpeg``, el primero instalado—;
  el motor la lee igual (gdkpixbuf). La entrada también acepta
  ``.webp``.

Uso desde Python::

    from pilas3d import sprites
    hoja = sprites.convertir('entrada.jpg', 'hoja.png')
    print(hoja['columnas'], hoja['filas'])
"""

import json
import struct
import zlib


def _chunk(t, d):
    c = t + d
    return struct.pack('>I', len(d)) + c + struct.pack(
        '>I', zlib.crc32(c) & 0xffffffff)


def escribir_png(ruta, ancho, alto, rgba):
    """Escribe un PNG RGBA 8-bit con stdlib (zlib+crc)."""
    crudo = b''.join(
        b'\x00' + bytes(rgba[y * ancho * 4:(y + 1) * ancho * 4])
        for y in range(alto))
    png = (b'\x89PNG\r\n\x1a\n'
           + _chunk(b'IHDR', struct.pack('>IIBBBBB',
                                         ancho, alto, 8, 6, 0, 0, 0))
           + _chunk(b'IDAT', zlib.compress(crudo, 6))
           + _chunk(b'IEND', b''))
    with open(ruta, 'wb') as f:
        f.write(png)
    return len(png)


def a_webp(entrada, salida=None, calidad=90):
    """Convierte ``entrada`` (PNG/JPG/WebP legible) a WebP con un
    encoder externo — el primero instalado entre ``cwebp``,
    ImageMagick ``convert`` y ``ffmpeg``. Devuelve la ruta
    escrita; sin encoder lanza RuntimeError."""
    import os
    import shutil
    import subprocess
    salida = salida or os.path.splitext(entrada)[0] + '.webp'
    if shutil.which('cwebp'):
        cmd = ['cwebp', '-quiet', '-q', str(calidad), entrada,
               '-o', salida]
    elif shutil.which('convert'):
        cmd = ['convert', entrada, '-quality', str(calidad), salida]
    elif shutil.which('ffmpeg'):
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', entrada,
               '-quality', str(calidad), salida]
    else:
        raise RuntimeError(
            'no hay encoder WebP: instalá cwebp (paquete webp), '
            'ImageMagick o ffmpeg')
    subprocess.check_call(cmd)
    return salida


def escribir_imagen(ruta, ancho, alto, rgba):
    """Escribe la hoja en ``ruta``: PNG con stdlib, o WebP si la
    extensión es ``.webp`` (vía PNG temporal + encoder externo)."""
    if ruta.lower().endswith('.webp'):
        import os
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        try:
            escribir_png(tmp, ancho, alto, rgba)
            a_webp(tmp, ruta)
        finally:
            os.unlink(tmp)
        return os.path.getsize(ruta)
    return escribir_png(ruta, ancho, alto, rgba)


def _decodificar(ruta):
    """Devuelve (ancho, alto, bytes RGBA) usando pyglet.
    Ojo: pyglet entrega las filas de abajo hacia arriba."""
    import pyglet
    img = pyglet.image.load(ruta)
    datos = img.get_data('RGBA', img.width * 4)
    return img.width, img.height, datos


def _fondo_de_esquinas(ancho, alto, datos):
    esq = []
    for x, y in ((0, 0), (ancho - 1, 0), (0, alto - 1),
                 (ancho - 1, alto - 1)):
        i = (y * ancho + x) * 4
        esq.append((datos[i], datos[i + 1], datos[i + 2]))
    return (sum(p[0] for p in esq) // 4,
            sum(p[1] for p in esq) // 4,
            sum(p[2] for p in esq) // 4)


def _clasifica(r, g, b, fondo, tol):
    """0=fondo, 1=contenido firme, 2=gris sospechoso (sombra u
    objeto gris: se decide por celda, franja inferior)."""
    fr, fg, fb = fondo
    if abs(r - fr) + abs(g - fg) + abs(b - fb) < tol * 3:
        return 0
    brillo = max(r, g, b)
    if brillo - min(r, g, b) < 26 and brillo > 150:
        return 2
    return 1


def _bandas(mini, mw, mh, hueco_min):
    """Filas de contenido en la máscara diezmada."""
    perfil = [mini[y * mw:(y + 1) * mw].count(1) for y in range(mh)]
    return _rangos(perfil, hueco_min)


def _rangos(perfil, hueco_min):
    """Rangos (ini, fin) de zonas con contenido, separadas por
    huecos de >= ``hueco_min`` posiciones vacías."""
    n = len(perfil)
    umbral = max(1, (max(perfil) or 1) * 0.02)
    rangos, ini, vacio = [], None, 0
    for i, v in enumerate(perfil):
        if v > umbral:
            if ini is None:
                ini = i
            vacio = 0
        else:
            if ini is not None:
                vacio += 1
                if vacio >= hueco_min:
                    rangos.append((ini, i - vacio))
                    ini = None
                    vacio = 0
    if ini is not None:
        rangos.append((ini, n - 1))
    return rangos


def _celdas_auto(ancho, alto, datos, fondo, tol, hueco_min, paso=4):
    """Detecta celdas como cajas (x, y, w, h) fila a fila.

    Trabaja sobre la clasificación diezmada ``paso``:1 para ir
    rápido; cuenta solo píxeles de contenido firme (``1``), no los
    grises sospechosos (``2``). Devuelve una lista de filas; cada
    fila es una lista de celdas (x, y, w, h) en coordenadas reales.
    """
    mw, mh = max(1, ancho // paso), max(1, alto // paso)
    mini = bytearray(mw * mh)
    for y in range(mh):
        base = y * paso * ancho
        for x in range(mw):
            i = (base + x * paso) * 4
            if _clasifica(datos[i], datos[i + 1], datos[i + 2],
                          fondo, tol) == 1:
                mini[y * mw + x] = 1
    hueco_s = max(2, hueco_min // paso)
    filas = []
    for y0, y1 in _bandas(mini, mw, mh, hueco_s):
        perfil = [0] * mw
        for y in range(y0, y1 + 1):
            for x in range(mw):
                if mini[y * mw + x]:
                    perfil[x] += 1
        celdas = []
        for x0, x1 in _rangos(perfil, hueco_s):
            # recorta el contenido exacto en Y dentro de la banda
            ys = [y for y in range(y0, y1 + 1)
                  if any(mini[y * mw + x] for x in range(x0, x1 + 1))]
            celdas.append((x0 * paso, ys[0] * paso,
                           min(ancho - 1, (x1 + 1) * paso) - x0 * paso,
                           min(alto - 1, (ys[-1] + 1) * paso)
                           - ys[0] * paso))
        if celdas:
            filas.append(celdas)
    return filas


def _celdas_grilla(ancho, alto, columnas, filas, datos, fondo, tol):
    """Grilla regular de ``columnas`` x ``filas``.

    Cada celda se queda solo con su componente conexa mayor (el
    personaje): los fragmentos del vecino que cruzan el borde — una
    espada, un brazo— se descartan. Devuelve filas de
    ``(x, y, w, h, mini, mw, paso)`` donde ``mini`` marca las
    posiciones válidas para empaquetar.
    """
    cw, ch = ancho // columnas, alto // filas
    paso = max(1, min(cw, ch) // 400)
    grid = []
    for f in range(filas):
        celdas = []
        for c in range(columnas):
            x0, y0 = c * cw, f * ch
            mw = max(1, cw // paso)
            mh = max(1, ch // paso)
            mini = bytearray(mw * mh)
            for my in range(mh):
                y = y0 + my * paso
                if y >= alto:
                    break
                base = y * ancho * 4
                for mx in range(mw):
                    x = x0 + mx * paso
                    if x >= ancho:
                        break
                    i = base + x * 4
                    if _clasifica(datos[i], datos[i + 1],
                                  datos[i + 2], fondo, tol):
                        mini[my * mw + mx] = 1
            comp = _componente_mayor(_dilatar(mini, mw, mh), mw, mh)
            if comp is None:
                celdas.append((x0, y0, cw, ch, None))
                continue
            xs, ys = [], []
            keep = bytearray(mw * mh)
            for p in comp:
                if mini[p]:               # solo muestras reales, no
                    keep[p] = 1           # las agregadas por dilatar
                    xs.append(p % mw)
                    ys.append(p // mw)
            celdas.append((x0 + min(xs) * paso, y0 + min(ys) * paso,
                           (max(xs) - min(xs) + 1) * paso,
                           (max(ys) - min(ys) + 1) * paso,
                           (keep, mw, paso, x0, y0)))
        grid.append(celdas)
    return grid


def _dilatar(mini, mw, mh):
    """Copia de la máscara con cada muestra + sus 8 vecinos.
    Puentea los huecos finos del muestreo (empuñaduras, bordes)."""
    out = bytearray(mini)
    for y in range(mh):
        for x in range(mw):
            if not mini[y * mw + x]:
                continue
            for dy in (-1, 0, 1):
                ny = y + dy
                if 0 <= ny < mh:
                    base = ny * mw
                    for dx in (-1, 0, 1):
                        nx = x + dx
                        if 0 <= nx < mw:
                            out[base + nx] = 1
    return out


def _componente_mayor(mini, mw, mh):
    """Conjunto de índices de la componente conexa (8-vecinos) más
    grande de la máscara, o None si está vacía."""
    visto = bytearray(mw * mh)
    mejor = None
    for i in range(mw * mh):
        if not mini[i] or visto[i]:
            continue
        comp, cola = set(), [i]
        visto[i] = 1
        while cola:
            p = cola.pop()
            comp.add(p)
            px, py = p % mw, p // mw
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < mw and 0 <= ny < mh:
                        q = ny * mw + nx
                        if mini[q] and not visto[q]:
                            visto[q] = 1
                            cola.append(q)
        if mejor is None or len(comp) > len(mejor):
            mejor = comp
    return mejor


def convertir(entrada, salida, columnas=None, filas=None,
              celda_max=512, umbral=232, hueco=16, margen=2,
              quitar_sombra=True):
    """Convierte una imagen a hoja de sprites PNG.

    Devuelve el manifiesto dict con ``columnas``, ``filas``,
    ``celda_ancho``, ``celda_alto`` y ``salida``.
    """
    ancho, alto, datos = _decodificar(entrada)
    fondo = _fondo_de_esquinas(ancho, alto, datos)
    tol = max(18, 255 - umbral + 12)

    if columnas and filas:
        grid = _celdas_grilla(ancho, alto, columnas, filas,
                              datos, fondo, tol)
    else:
        grid = _celdas_auto(ancho, alto, datos, fondo, tol,
                            max(hueco, 4))
    if not grid:
        raise ValueError("no se detectó contenido en %s" % entrada)

    cols = max(len(f) for f in grid)
    cw_max = max(c[2] for f in grid for c in f) + margen * 2
    ch_max = max(c[3] for f in grid for c in f) + margen * 2
    # las celdas de grilla traen máscara propia: (x,y,w,h,(mini,mw,paso,ox,oy))
    def _celda(c):
        if len(c) > 4:
            return c[0], c[1], c[2], c[3], c[4]
        return c[0], c[1], c[2], c[3], None
    esc = min(1.0, celda_max / float(max(cw_max, ch_max)))
    CW = max(8, int(cw_max * esc))
    CH = max(8, int(ch_max * esc))

    hoja = bytearray(CW * cols * CH * len(grid) * 4)

    def y_datos(y_top):
        return alto - 1 - y_top

    for fi, fila_celdas in enumerate(grid):
        for ci in range(cols):
            if ci >= len(fila_celdas):
                continue
            x0, y0, w, h, keep = _celda(fila_celdas[ci])
            # escala el contenido dentro de la celda, centrado en X
            # y con los pies abajo
            k = min((CW - margen * 2) / float(w),
                    (CH - margen * 2) / float(h))
            dw, dh = max(1, int(w * k)), max(1, int(h * k))
            ox = ci * CW + (CW - dw) // 2
            oy = fi * CH + (CH - dh - margen)
            for dy in range(dh):
                sy = y0 + int(dy * h / dh)
                yd = y_datos(sy)
                fraccion = (sy - y0) / float(max(1, h))
                for dx in range(dw):
                    sx = x0 + int(dx * w / dw)
                    si = (yd * ancho + sx) * 4
                    r, g, b, a = (datos[si], datos[si + 1],
                                  datos[si + 2], datos[si + 3])
                    m = _clasifica(r, g, b, fondo, tol)
                    if keep is not None and m:
                        km, kmw, kpaso, kx0, ky0 = keep
                        kmx, kmy = (sx - kx0) // kpaso, (sy - ky0) // kpaso
                        if not (0 <= kmx < kmw and 0 <= kmy < len(km) // kmw
                                and km[kmy * kmw + kmx]):
                            m = 0
                    di = ((oy + dy) * cols * CW + ox + dx) * 4
                    if m == 0:
                        hoja[di:di + 4] = b'\x00\x00\x00\x00'
                    elif m == 2 and quitar_sombra \
                            and fraccion > 0.82:
                        # gris neutro en la base de la celda: sombra
                        hoja[di:di + 4] = b'\x00\x00\x00\x00'
                    else:
                        hoja[di:di + 4] = bytes((r, g, b, 255))

    n = escribir_imagen(salida, cols * CW, len(grid) * CH, hoja)
    man = {'columnas': cols, 'filas': len(grid),
           'celda_ancho': CW, 'celda_alto': CH,
           'cuadros': sum(len(f) for f in grid),
           'fondo': list(fondo), 'salida': salida}
    with open(salida.rsplit('.', 1)[0] + '.sprites.json', 'w') as f:
        json.dump(man, f, indent=2)
    print('%s: %dx%d hoja (%d columnas x %d filas), %d bytes'
          % (salida, cols * CW, len(grid) * CH, cols, len(grid), n))
    return man


def cli(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        prog='pilas3d-sprites',
        description='Convierte una imagen en hoja de sprites PNG '
                    'con transparencia para PersonajeSprite/Animacion')
    p.add_argument('entrada', help='imagen fuente (.jpg/.png/.webp)')
    p.add_argument('-o', '--salida', required=True,
                   help='hoja de salida: .png (stdlib) o .webp '
                        '(encoder externo: cwebp/convert/ffmpeg)')
    p.add_argument('--columnas', type=int, default=None,
                   help='grilla regular en vez de auto-detectar')
    p.add_argument('--filas', type=int, default=None,
                   help='grilla regular en vez de auto-detectar')
    p.add_argument('--celda-max', type=int, default=512,
                   help='tamaño máximo de celda (default 512)')
    p.add_argument('--hueco', type=int, default=16,
                   help='hueco mínimo entre personajes, px (default 16)')
    p.add_argument('--margen', type=int, default=2,
                   help='margen interno de cada celda (default 2)')
    p.add_argument('--mantener-sombra', action='store_true',
                   help='no quitar el gris de la base (sombra de piso)')
    a = p.parse_args(argv)
    if bool(a.columnas) != bool(a.filas):
        p.error('--columnas y --filas van juntas')
    man = convertir(a.entrada, a.salida, columnas=a.columnas,
                    filas=a.filas, celda_max=a.celda_max,
                    hueco=a.hueco, margen=a.margen,
                    quitar_sombra=not a.mantener_sombra)
    return man


if __name__ == '__main__':
    cli()
