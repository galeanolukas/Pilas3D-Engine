# -*- encoding: utf-8 -*-
"""Red: multijugador simple por TCP con mensajes JSON.

Nivel educativo ("mundo compartido"): un jugador hospeda y los demás
se conectan. Los mensajes son líneas JSON ``{"t": tipo, "d": datos}``;
el servidor los reenvía a todos los demás clientes y también al
jugador que hospeda.

Los callbacks registrados con ``cuando_reciba`` NO corren en el hilo
de red: se encolan y se despachan desde el bucle del juego
(``Pilas._tick``), así se puede tocar actores y OpenGL tranquilo.

    >>> red = pilas.red.hospedar(puerto=7777)     # servidor + jugador
    >>> red = pilas.red.conectar("192.168.0.5", 7777)  # solo cliente
    >>> red.enviar("posicion", x=1, y=0, z=2)
    >>> red.cuando_reciba("posicion", lambda datos, de: print(de, datos))
"""

import json
import queue
import socket
import threading


def _mandar(sock, nombre, datos):
    """Envía un mensaje como línea JSON (con su propio lock por socket)."""
    linea = json.dumps({'t': nombre, 'd': datos}) + '\n'
    sock.sendall(linea.encode('utf-8'))


class _Conexion(object):
    """Base: cola de mensajes entrantes + callbacks por tipo."""

    def __init__(self, pilas):
        self.pilas = pilas
        self._callbacks = {}
        self._cola = queue.Queue()
        self.cerrada = False

    def cuando_reciba(self, nombre, funcion):
        """Registra ``funcion(datos, de)`` para mensajes de ese nombre.

        ``de`` es el id del cliente que lo envió (None si lo mandó
        directamente el servidor). La funcion corre en el hilo del
        juego durante el próximo ``paso()``/frame.
        """
        self._callbacks.setdefault(nombre, []).append(funcion)

    def _encolar(self, nombre, datos, de):
        self._cola.put((nombre, datos, de))

    # -- chat incorporado --------------------------------------------------

    def chatear(self, texto, nombre='jugador'):
        """Envía un mensaje de chat a todos: ``{'texto', 'nombre'}``."""
        self.enviar('chat', texto=str(texto), nombre=nombre)

    def cuando_chat(self, funcion):
        """``funcion(datos, de)`` con ``datos`` = {'texto','nombre'}."""
        self.cuando_reciba('chat', funcion)

    def actualizar(self):
        """Despacha los mensajes encolados (llamado por ``Pilas._tick``)."""
        while True:
            try:
                nombre, datos, de = self._cola.get_nowait()
            except queue.Empty:
                return
            for fn in self._callbacks.get(nombre, ()):
                fn(datos, de)

    def cerrar(self):
        self.cerrada = True


class Servidor(_Conexion):
    """Acepta clientes y reenvía cada mensaje a todos los demás.

    El jugador que hospeda también recibe los mensajes por
    ``cuando_reciba`` (le llegan con el ``id`` del cliente remitente).
    """

    def __init__(self, pilas, puerto=7777):
        super(Servidor, self).__init__(pilas)
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(('', puerto))
        self._listener.listen(8)
        self.puerto = self._listener.getsockname()[1]
        self._clientes = {}          # id -> socket
        self._locks = {}             # id -> lock de escritura
        self._siguiente_id = 1
        self._hilo = threading.Thread(target=self._aceptar)
        self._hilo.daemon = True
        self._hilo.start()

    def jugadores(self):
        """Ids de los clientes conectados (sin contar al que hospeda)."""
        return sorted(self._clientes)

    def enviar(self, tipo, **datos):
        """Broadcast a todos los clientes conectados."""
        for cid in list(self._clientes):
            self._mandar_a(cid, tipo, datos)

    def _mandar_a(self, cid, nombre, datos):
        try:
            with self._locks[cid]:
                _mandar(self._clientes[cid], nombre, datos)
        except (OSError, KeyError):
            pass   # el cliente se fue; el hilo lector lo limpia

    def _aceptar(self):
        while not self.cerrada:
            try:
                sock, _ = self._listener.accept()
            except OSError:
                return
            cid = self._siguiente_id
            self._siguiente_id += 1
            self._clientes[cid] = sock
            self._locks[cid] = threading.Lock()
            # le avisamos su id y quiénes ya estaban
            self._mandar_a(cid, 'hola', {'id': cid,
                                         'jugadores': self.jugadores()})
            for otro in self._clientes:
                if otro != cid:
                    self._mandar_a(otro, 'entro', {'id': cid})
            self._encolar('entro', {'id': cid}, cid)
            threading.Thread(target=self._escuchar,
                             args=(cid, sock), daemon=True).start()

    def _escuchar(self, cid, sock):
        try:
            for linea in sock.makefile('r', encoding='utf-8'):
                try:
                    msg = json.loads(linea)
                except ValueError:
                    continue
                nombre, datos = msg.get('t'), msg.get('d', {})
                fwd = dict(datos, de=cid) if isinstance(datos, dict) \
                    else {'de': cid, 'v': datos}
                for otro in list(self._clientes):   # reenvío a los demás
                    if otro != cid:
                        self._mandar_a(otro, nombre, fwd)
                self._encolar(nombre, datos, cid)
        except OSError:
            pass
        finally:
            self._clientes.pop(cid, None)
            self._locks.pop(cid, None)
            try:
                sock.close()
            except OSError:
                pass
            for otro in list(self._clientes):
                self._mandar_a(otro, 'salio', {'id': cid})
            self._encolar('salio', {'id': cid}, cid)

    def cerrar(self):
        super(Servidor, self).cerrar()
        try:
            self._listener.close()
        except OSError:
            pass
        for sock in list(self._clientes.values()):
            try:
                sock.close()
            except OSError:
                pass


class Cliente(_Conexion):
    """Cliente TCP: envía al servidor, que reenvía a los demás.

    Los mensajes llegan con ``d['de']`` = id del cliente que los mandó
    (o sin ``de`` si los envió el servidor con ``enviar``).
    """

    def __init__(self, pilas, host='localhost', puerto=7777, timeout=5):
        super(Cliente, self).__init__(pilas)
        self.id = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((host, puerto))
        self._sock.settimeout(None)
        self._lock = threading.Lock()
        self._hilo = threading.Thread(target=self._escuchar)
        self._hilo.daemon = True
        self._hilo.start()

    def enviar(self, tipo, **datos):
        with self._lock:
            _mandar(self._sock, tipo, datos)

    def _escuchar(self):
        try:
            for linea in self._sock.makefile('r', encoding='utf-8'):
                try:
                    msg = json.loads(linea)
                except ValueError:
                    continue
                nombre, datos = msg.get('t'), msg.get('d', {})
                de = datos.pop('de', None) if isinstance(datos, dict) \
                    else None
                if nombre == 'hola':
                    self.id = datos.get('id')
                self._encolar(nombre, datos, de)
        except OSError:
            pass
        finally:
            self.cerrada = True
            self._encolar('salio', {'id': self.id}, None)

    def cerrar(self):
        super(Cliente, self).cerrar()
        try:
            self._sock.close()
        except OSError:
            pass


class Red(object):
    """Fachada ``pilas.red``: hospedar/conectar y despacho por frame.

    Mantiene la conexión activa (una a la vez) y la pulea en cada
    ``Pilas._tick`` para que los callbacks corran en el hilo del juego.
    """

    def __init__(self, pilas):
        self.pilas = pilas
        self.conexion = None

    def hospedar(self, puerto=7777):
        """Crea un servidor y retorna el ``Servidor`` (sos el host)."""
        self.conexion = Servidor(self.pilas, puerto=puerto)
        return self.conexion

    def conectar(self, host='localhost', puerto=7777):
        """Conecta a un servidor y retorna el ``Cliente``."""
        self.conexion = Cliente(self.pilas, host=host, puerto=puerto)
        return self.conexion

    def _actualizar(self):
        if self.conexion is not None:
            self.conexion.actualizar()
