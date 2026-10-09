# -*- encoding: utf-8 -*-
"""Puente WebSocket + Three.js: el motor corre en Python y el
navegador dibuja.

    pilas = pilas3d.iniciar()
    pilas.web.servir()            # http://127.0.0.1:8000/
    pilas.web.servir(publico=True)  # la LAN entera puede mirar/jugar
    pilas.ejecutar()              # o pilas.web.ejecutar() sin ventana

Cada ``hz`` veces por segundo el puente manda una foto de la escena
(posición/rotación/escala/color de cada actor, cámara, luces, niebla)
como JSON por WebSocket; la geometría de cada actor viaja una sola vez
(y se reenvía cuando cambia: skinning, terreno deformado...). El
cliente Three.js la reconstruye con ``BufferGeometry`` — así cualquier
actor del motor (Cubo, Terreno, ModeloGLTF skinneado, Mundo voxel)
aparece en el navegador sin código extra.

El input viaja de vuelta: las teclas del navegador se fusionan en
``pilas.control`` (flechas/WASD funcionan igual que el mando USB), así
el juego es *jugable* desde el browser. ``es_overlay`` (Texto, Menu,
Panel...) no se envía: es dibujo 2D de pantalla, no geometría.

Sin dependencias: el WebSocket es RFC6455 mínimo hecho a mano sobre
``http.server`` y Three.js va vendored en ``pilas3d/web/``.
"""

import base64
import hashlib
import json
import os
import struct
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Queue

_DIR_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'web')
_GUIA_WS = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

_MIME = {'.html': 'text/html; charset=utf-8',
         '.js': 'text/javascript',
         '.css': 'text/css',
         '.png': 'image/png', '.jpg': 'image/jpeg',
         '.jpeg': 'image/jpeg', '.bmp': 'image/bmp'}

#: clases que dibujan en pantalla, no en el mundo 3D
_SKIP = ('Sombra',)


def _hdr_a_png(ruta, max_ancho=1024):
    """Decodifica un ``.hdr`` Radiance y lo convierte a PNG 8-bit
    (tonemap exponencial + gamma 2.2), bajando la resolución si hace
    falta — el navegador lo usa como fondo equirectangular."""
    import math
    import struct
    import zlib

    from pilas3d import hdr as _hdr

    ancho, alto, datos = _hdr.cargar(ruta)
    paso = max(1, ancho // max_ancho)
    aw, ah = ancho // paso, alto // paso
    rgb = bytearray(aw * ah * 3)
    o = 0
    inv_gamma = 1.0 / 2.2
    for y in range(ah):
        for x in range(aw):
            i = (y * paso * ancho + x * paso) * 4   # rgba floats
            for c in range(3):
                v = 1.0 - math.exp(-datos[i + c])     # tonemap
                rgb[o] = min(255, int(v ** inv_gamma * 255))
                o += 1
    # PNG 8-bit RGB: filas con filtro 0, un IDAT zlib
    def _chunk(tipo, cuerpo):
        c = tipo + cuerpo
        return struct.pack('>I', len(cuerpo)) + c + struct.pack(
            '>I', zlib.crc32(c) & 0xffffffff)
    crudo = b''.join(
        b'\x00' + bytes(rgb[y * aw * 3:(y + 1) * aw * 3])
        for y in range(ah))
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', struct.pack('>IIBBBBB', aw, ah, 8, 2,
                                          0, 0, 0))
            + _chunk(b'IDAT', zlib.compress(crudo, 6))
            + _chunk(b'IEND', b''))


def _mapa_codigos():
    """``e.code`` del navegador -> constante de ``pyglet.window.key``."""
    from pyglet.window import key
    m = {'ArrowUp': key.UP, 'ArrowDown': key.DOWN,
         'ArrowLeft': key.LEFT, 'ArrowRight': key.RIGHT,
         'Space': key.SPACE, 'Enter': key.ENTER, 'Escape': key.ESCAPE,
         'Tab': key.TAB, 'Backspace': key.BACKSPACE,
         'ShiftLeft': key.LSHIFT, 'ShiftRight': key.RSHIFT,
         'ControlLeft': key.LCTRL, 'ControlRight': key.RCTRL,
         'AltLeft': key.LALT, 'AltRight': key.RALT}
    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        m['Key' + letra] = getattr(key, letra)
    for d in '0123456789':
        m['Digit' + d] = getattr(key, '_' + d)
    for i in range(1, 13):
        m['F%d' % i] = getattr(key, 'F%d' % i)
    return m


# -- WebSocket mínimo (RFC6455) ----------------------------------------------

def _recv_exacto(sock, n):
    datos = b''
    while len(datos) < n:
        trozo = sock.recv(n - len(datos))
        if not trozo:
            raise ConnectionError('socket cerrado')
        datos += trozo
    return datos


def _leer_frame(sock):
    """Lee un frame: (opcode, payload). Lanza al cerrar."""
    b = _recv_exacto(sock, 2)
    op = b[0] & 0x0F
    enmascarado = b[1] & 0x80
    largo = b[1] & 0x7F
    if largo == 126:
        largo = struct.unpack('!H', _recv_exacto(sock, 2))[0]
    elif largo == 127:
        largo = struct.unpack('!Q', _recv_exacto(sock, 8))[0]
    mascara = _recv_exacto(sock, 4) if enmascarado else b''
    datos = bytearray(_recv_exacto(sock, largo))
    if enmascarado:                              # el cliente siempre
        for i in range(largo):                   # enmascara (spec)
            datos[i] ^= mascara[i % 4]
    return op, bytes(datos)


def _frame(payload, opcode=0x1):
    """Frame server->cliente (sin máscara, como manda la spec)."""
    n = len(payload)
    if n < 126:
        cab = struct.pack('!BB', 0x80 | opcode, n)
    elif n < 65536:
        cab = struct.pack('!BBH', 0x80 | opcode, 126, n)
    else:
        cab = struct.pack('!BBQ', 0x80 | opcode, 127, n)
    return cab + payload


class _ClienteWS(object):
    """Un navegador conectado: socket + qué geometrías ya recibió."""

    def __init__(self, sock):
        self.sock = sock
        self.lock = threading.Lock()
        self.geo = {}              # id_actor -> version enviada
        self.vivo = True

    def enviar(self, texto):
        with self.lock:
            self.sock.sendall(_frame(texto.encode('utf-8')))

    def enviar_bytes(self, opcode, datos):
        with self.lock:
            self.sock.sendall(_frame(datos, opcode))


class _VentanaWeb(object):
    """Fachada de ventana para modo headless: su ``teclas`` es el
    estado que llega por WebSocket y el mouse el del navegador."""

    def __init__(self, teclas):
        self.teclas = teclas
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_botones = 0


def _b64f(vals):
    return base64.b64encode(
        struct.pack('<%df' % len(vals), *vals)).decode('ascii')


def _b64i(vals):
    return base64.b64encode(
        struct.pack('<%dI' % len(vals), *vals)).decode('ascii')


class PuenteWeb(object):
    """Sirve la escena de pilas3d a navegadores por WebSocket."""

    def __init__(self, pilas):
        self.pilas = pilas
        self.hz = 20               # snapshots por segundo
        self.clientes = []
        self.teclas = {}           # simbolo pyglet -> bool (input web)
        self._entrada = Queue()    # eventos crudos de los clientes
        self._imagenes = []        # [(nombre_url, ruta|bytes)]
        self._img_indice = {}      # fuente -> nombre_url
        self._cielos = {}          # ruta .hdr -> nombre_url (png)
        self._srv = None
        self._ultimo = 0.0
        self._vw = None

    @property
    def activo(self):
        return self._srv is not None

    # -- API pública ----------------------------------------------------

    def servir(self, puerto=8000, publico=False, hz=None):
        """Levanta el servidor y devuelve la URL para abrir.

        ``publico=True`` ata a todas las interfaces (la LAN ve el
        juego); por defecto solo ``127.0.0.1``. ``hz`` son los
        snapshots por segundo (default 20)."""
        if hz:
            self.hz = hz
        self._servir_http('0.0.0.0' if publico else '127.0.0.1',
                          puerto)
        self._fusionar_control()
        url = 'http://%s:%d/' % (
            'localhost' if not publico else '0.0.0.0',
            self._srv.server_address[1])
        if publico:
            import socket as _s
            try:
                ip = _s.gethostbyname(_s.gethostname())
            except OSError:
                ip = '?'
            url = 'http://%s:%d/' % (ip, self._srv.server_address[1])
        print('pilas3d web en %s — abrilo en un navegador' % url)
        return url

    def ejecutar(self):
        """Loop principal: con ventana delega a ``pilas.ejecutar()``;
        headless corre el event loop de pyglet (que dispara _tick y
        por tanto los snapshots)."""
        if self.pilas.ventana is not None:
            return self.pilas.ejecutar()
        import pyglet
        pyglet.clock.schedule_interval(self.pilas._tick, 1 / 60.0)
        pyglet.app.run()

    def detener(self):
        if self._srv is not None:
            self._srv.shutdown()
            self._srv = None
        for c in list(self.clientes):
            try:
                c.sock.close()
            except OSError:
                pass
        self.clientes = []

    # -- integración con el motor -----------------------------------------

    def _fusionar_control(self):
        """Las teclas del navegador entran a ``pilas.control``: con
        ventana se suman como fuente extra; sin ventana se crea un
        Control real sobre la fachada web (WASD del browser funciona
        en un server headless)."""
        from pilas3d.control import ControlNulo
        control = getattr(self.pilas, 'control', None)
        if self.pilas.ventana is None or isinstance(control,
                                                    ControlNulo):
            from pilas3d.control import Control
            self._vw = _VentanaWeb(self.teclas)
            self.pilas.control = Control(
                self._vw, getattr(self.pilas, 'mandos', None))
        else:
            control.agregar_fuente(self.teclas)

    def _tick(self):
        """Lo llama ``Pilas._tick`` cada frame: drena el input y
        emite el snapshot si toca (throttle por ``self.hz``)."""
        if not self.activo:
            return
        self._drenar_entrada()
        ahora = time.monotonic()
        if not self.clientes or ahora - self._ultimo < 1.0 / self.hz:
            return
        self._ultimo = ahora
        for c in list(self.clientes):
            try:
                c.enviar(self._snapshot(c))
            except (OSError, ConnectionError):
                self._baja(c)

    def _baja(self, cliente):
        cliente.vivo = False
        if cliente in self.clientes:
            self.clientes.remove(cliente)
        try:
            cliente.sock.close()
        except OSError:
            pass

    # -- input del navegador ----------------------------------------------

    def _mensaje_ws(self, datos, cliente):
        """JSON entrante de un cliente (hilo del handler)."""
        try:
            msg = json.loads(datos)
        except ValueError:
            return
        self._entrada.put(msg)

    def _drenar_entrada(self):
        """Aplica el input en el hilo del motor: estado de teclas +
        ``cuando_pulsa_tecla`` de la escena."""
        mapa = _mapa_teclas_lazy()
        escena = self.pilas.escena_actual()
        while True:
            try:
                msg = self._entrada.get_nowait()
            except Empty:
                return
            t = msg.get('t')
            if t == 'k':
                sim = mapa.get(msg.get('k'))
                if sim is None:
                    continue
                v = bool(msg.get('v'))
                self.teclas[sim] = v
                if v:
                    cb = getattr(escena, 'cuando_pulsa_tecla', None)
                    if cb:
                        cb(sim)
            elif t == 'm':
                if self._vw is not None:
                    self._vw.mouse_x = msg.get('x', 0)
                    self._vw.mouse_y = msg.get('y', 0)
                    self._vw.mouse_botones = msg.get('b', 0)

    # -- serialización de la escena ------------------------------------------

    def _extraer_geo(self, actor):
        """Geometría de un actor como dict b64 (o None si no es
        malla de triángulos / no genera)."""
        pos = getattr(actor, '_pos_skin', None) \
            or getattr(actor, '_pos', None)
        nor = getattr(actor, '_nor_skin', None) \
            or getattr(actor, '_nor', None)
        if pos is not None:
            modo = getattr(actor, '_modo', None) or 4
            col = getattr(actor, '_col', None)
            uv = getattr(actor, '_uv', None)
            idx = getattr(actor, '_indices', None)
        else:
            try:
                datos = actor._generar_geometria()
            except (NotImplementedError, AttributeError):
                return None
            pos, nor, modo = datos[0], datos[1], datos[2]
            col = datos[3] if len(datos) > 3 else None
            uv = datos[4] if len(datos) > 4 else None
            idx = getattr(actor, '_indices', None)
        if modo not in (0, 1, 4) or not pos:   # puntos, líneas, tris
            return None
        g = {'i': id(actor), 'm': modo, 'v': _b64f(pos)}
        if nor:
            g['n'] = _b64f(nor)
        if col:
            g['c'] = _b64f(col)
        if uv:
            g['u'] = _b64f(uv)
        if idx:
            g['x'] = _b64i(idx)
        return g

    def _url_imagen(self, fuente):
        """Registra una textura (ruta o bytes) y devuelve su URL."""
        if fuente in self._img_indice:
            return self._img_indice[fuente]
        if isinstance(fuente, bytes):
            ext = '.png' if fuente[:4] == b'\x89PNG' else '.jpg'
        else:
            if not isinstance(fuente, str) \
                    or fuente.lower().endswith('.hdr') \
                    or not os.path.isfile(fuente):
                return None
            ext = os.path.splitext(fuente)[1]
        nombre = 'img%d%s' % (len(self._imagenes), ext)
        self._imagenes.append((nombre, fuente))
        self._img_indice[fuente] = nombre
        return nombre

    def _resolver_imagen_actor(self, actor):
        """La textura del actor como fuente servible: bytes o ruta."""
        img = getattr(actor, '_imagen', None)
        if img is None:
            return None
        if isinstance(img, bytes):
            return img
        if isinstance(img, str):
            try:
                return actor._resolver_imagen(img)
            except Exception:
                return None
        return None                 # ImageData pyglet: no servible

    def _cielo_hdr(self, cielo):
        """Si el Cielo usa un ``.hdr``, lo decodifica una vez,
        tonemapea a PNG y lo registra como textura servible.
        Devuelve el nombre URL o None."""
        ruta = getattr(cielo, '_imagen', None)
        if not isinstance(ruta, str) \
                or not ruta.lower().endswith('.hdr'):
            return None
        if ruta in self._cielos:
            return self._cielos[ruta]
        try:
            from pilas3d import hdr as _hdr
            from pilas3d.imagenes import resolver
            png = _hdr_a_png(resolver(ruta))
        except (IOError, OSError, ValueError):
            self._cielos[ruta] = None
            return None
        nombre = self._url_imagen(png)
        self._cielos[ruta] = nombre
        return nombre

    def _describir_overlay(self, a):
        """Actor 2D -> dict para el HUD del navegador (o None)."""
        clase = type(a).__name__
        if clase in ('Texto', 'Puntaje', 'Temporizador'):
            d = {'k': 't', 'x': a.x, 'y': a.y, 's': a.texto,
                 'z': a.tamano, 'c': list(a.color)}
            if getattr(a, 'ancho', None):
                d['w'] = a.ancho
            return d
        if clase == 'Panel':
            d = {'k': 'p', 'x': a.x, 'y': a.y, 'w': a.ancho,
                 'h': a.alto, 'c': list(a.color)}
            return d
        if clase == 'Barra':
            d = {'k': 'b', 'x': a.x, 'y': a.y, 'w': a.ancho,
                 'h': a.alto, 'f': a.fraccion()}
            if a.color_fijo is not None:
                d['c'] = list(a.color_fijo)
            return d
        if clase == 'Globo':
            if not getattr(a, '_visible', True):
                return None
            paginas = getattr(a, '_paginas', None)
            s = paginas[a._indice] if paginas else a.texto
            d = {'k': 'g', 's': s, 'z': a.tamano, 'h': a.alto}
            if getattr(a, 'actor', None) is not None:
                d['a'] = id(a.actor)      # anclado: el cliente proyecta
            else:
                d['x'], d['y'] = a.x, a.y
            return d
        # Menu dibuja sus opciones como Textos internos (ya viajan)
        return None

    def _snapshot(self, cliente):
        """JSON del frame para un cliente: actores + geometrías que
        le falten + HUD 2D + cámara + luces + niebla."""
        pilas = self.pilas
        escena = pilas.escena_actual()
        actores, geos, hud = [], [], []
        msg_cielo = None
        vivos = set()
        for a in list(escena.actores):
            if getattr(a, 'es_overlay', False):
                if getattr(a, 'visible', True):
                    d = self._describir_overlay(a)
                    if d:
                        hud.append(d)
                continue
            if not getattr(a, 'visible', True) \
                    or type(a).__name__ in _SKIP:
                continue
            if type(a).__name__ == 'Cielo':
                # el domo HDR se convierte en fondo/ambiente del
                # cliente; el generado ('dia'...) sale como color
                ruta = self._cielo_hdr(a)
                if ruta:
                    msg_cielo = ruta
                continue
            i = id(a)
            vivos.add(i)
            ver = getattr(a, '_geo_version', 0)
            dinamico = getattr(a, '_modo', 4) in (0, 1)
            if cliente.geo.get(i) != ver or dinamico:
                g = self._extraer_geo(a)
                if g is None:
                    cliente.geo[i] = ver       # no insistir
                    continue
                cliente.geo[i] = ver
                geos.append(g)
            entrada = {
                'i': i,
                'p': [round(a.x, 3), round(a.y, 3), round(a.z, 3)],
                'r': [round(a.rotacion_x, 2), round(a.rotacion_y, 2),
                      round(a.rotacion_z, 2)],
                'e': [round(a.escala_x, 3), round(a.escala_y, 3),
                      round(a.escala_z, 3)],
            }
            if a._color != (255, 255, 255):
                entrada['c'] = list(a._color)
            if a._transparencia:
                entrada['o'] = round(1 - a._transparencia / 100.0, 3)
            if a.sin_luz:
                entrada['l'] = 1
            if getattr(a, '_modo', 4) == 0:
                entrada['pt'] = getattr(a, 'punto_tamano', 1.0)
            fuente = self._resolver_imagen_actor(a)
            if fuente is not None:
                nombre = self._url_imagen(fuente)
                if nombre:
                    entrada['t'] = nombre
            actores.append(entrada)
        # olvidar geometrías de actores que ya no existen
        for i in list(cliente.geo):
            if i not in vivos:
                del cliente.geo[i]

        cam = escena.camara
        msg = {'t': 'e', 'a': actores}
        if geos:
            msg['g'] = geos
        msg['cam'] = {'p': [cam.x, cam.y, cam.z],
                      'o': list(cam.objetivo)}
        d = pilas.luces.direccional
        msg['luz'] = {
            'd': list(d.direccion), 'c': list(d.color),
            'amb': d.ambiente, 'ambc': list(d.ambiente_color),
            'p': [[l.x, l.y, l.z, list(l.color), l.alcance]
                  for l in pilas.luces.puntuales],
        }
        if escena.niebla:
            color, ini, fin = escena.niebla
            msg['nie'] = [list(color), ini, fin]
        fondo = getattr(escena, 'fondo', None)
        if fondo is not None:
            msg['fondo'] = list(fondo)
        if msg_cielo:
            msg['cielo'] = msg_cielo
        if hud:
            msg['hud'] = hud
        v = pilas.ventana
        msg['v'] = [v.width, v.height] if v is not None else [800, 600]
        return json.dumps(msg, separators=(',', ':'))

    # -- HTTP + upgrade WS ------------------------------------------------

    def _servir_http(self, host, puerto):
        puente = self
        web = _DIR_WEB

        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path.split('?')[0] == '/ws' and \
                        'websocket' in \
                        self.headers.get('Upgrade', '').lower():
                    self._upgrade_ws()
                    return
                self._estatico()

            def _estatico(self):
                ruta = self.path.split('?')[0].lstrip('/')
                if not ruta:
                    ruta = 'cliente.html'
                if ruta.startswith('img'):
                    return self._imagen(ruta)
                destino = os.path.normpath(os.path.join(web, ruta))
                if not destino.startswith(web) \
                        or not os.path.isfile(destino):
                    self.send_error(404)
                    return
                with open(destino, 'rb') as f:
                    cuerpo = f.read()
                self.send_response(200)
                self.send_header('Content-Type', _MIME.get(
                    os.path.splitext(destino)[1],
                    'application/octet-stream'))
                self.send_header('Content-Length', str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)

            def _imagen(self, nombre):
                """Texturas registradas por los actores."""
                for nom, fuente in puente._imagenes:
                    if nom != nombre:
                        continue
                    if isinstance(fuente, bytes):
                        datos = fuente
                    else:
                        with open(fuente, 'rb') as f:
                            datos = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', _MIME.get(
                        os.path.splitext(nombre)[1],
                        'application/octet-stream'))
                    self.send_header('Content-Length', str(len(datos)))
                    self.end_headers()
                    self.wfile.write(datos)
                    return
                self.send_error(404)

            def _upgrade_ws(self):
                clave = self.headers.get('Sec-WebSocket-Key', '')
                aceptar = base64.b64encode(hashlib.sha1(
                    (clave + _GUIA_WS).encode()).digest()).decode()
                self.send_response(101, 'Switching Protocols')
                self.send_header('Upgrade', 'websocket')
                self.send_header('Connection', 'Upgrade')
                self.send_header('Sec-WebSocket-Accept', aceptar)
                self.end_headers()
                cliente = _ClienteWS(self.connection)
                puente.clientes.append(cliente)
                self.close_connection = True
                try:
                    while True:
                        op, datos = _leer_frame(self.connection)
                        if op == 8:                    # close
                            break
                        if op == 9:                    # ping -> pong
                            cliente.enviar_bytes(0xA, datos)
                            continue
                        if op in (1, 2):
                            puente._mensaje_ws(datos, cliente)
                except (OSError, ConnectionError):
                    pass
                finally:
                    puente._baja(cliente)

        try:
            self._srv = ThreadingHTTPServer((host, puerto), Handler)
        except OSError as e:
            if e.errno == 98:                  # EADDRINUSE
                raise IOError(
                    'el puerto %d ya está ocupado — ¿hay otro '
                    'pilas.web.servir() corriendo? Matá el proceso '
                    'viejo o pasá otro puerto: servir(puerto=8001)'
                    % puerto) from e
            raise
        self._srv.daemon_threads = True
        hilo = threading.Thread(target=self._srv.serve_forever,
                                daemon=True)
        hilo.start()


_MAPA_TECLAS = None


def _mapa_teclas_lazy():
    """Construido a demanda: requiere pyglet.window.key."""
    global _MAPA_TECLAS
    if _MAPA_TECLAS is None:
        _MAPA_TECLAS = _mapa_codigos()
    return _MAPA_TECLAS
