# -*- encoding: utf-8 -*-
"""Puente HTTP entre la página de bloques y la escena de pilas3d.

``pilas3d-bloques`` levanta este servidor en ``127.0.0.1:8765``: la
página web (Blockly) le hace POST del código Python generado y el
motor lo ejecuta **en el hilo principal** (OpenGL no es thread-safe),
drenando la cola una vez por frame desde una tarea ``siempre``.

Endpoints:

- ``GET  /``            → sirve ``bloques_web/`` (la página de bloques)
- ``POST /codigo``      → ``{"codigo": "..."}`` ejecuta el código
- ``POST /detener``     → mata la corrida en curso
- ``GET  /resultado``   → ``{"estado": ..., "salida": "..."}``

Dos modos:

- **con ``pilas``**: el código se encola y corre en el hilo
  principal de la ventana ya abierta (la usa el motor vivo).
- **sin ``pilas``** (``pilas3d-bloques``): el código corre en un
  **subproceso** con su propia ventana (``bloques_runner``);
  "ejecutar" lo crea, "detener" lo termina.
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Queue

PUERTO = 8765

_RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'bloques_runner.py')


class PuenteBloques(object):
    """Recibe código Python por HTTP y lo corre en la escena."""

    def __init__(self, pilas, directorio_web):
        self.pilas = pilas
        self.directorio_web = os.path.abspath(directorio_web)
        self.cola = Queue()
        self.ultimo = {'estado': 'inactivo', 'salida': ''}
        self._tarea = None
        self._srv = None
        self._proc = None
        self._salida = None

    # -- lado del motor -----------------------------------------------------

    def enganchar(self):
        """Registra la tarea que drena la cola cada frame."""
        if self.pilas is None:
            return
        self._tarea = self.pilas.tareas.siempre(0, self.procesar)

    def procesar(self):
        """Ejecuta el código encolado (hilo principal, una vez por
        frame). Lo llama el planificador de tareas."""
        while True:
            try:
                codigo = self.cola.get_nowait()
            except Empty:
                return
            self._ejecutar(codigo)

    # -- modo subproceso (sin pilas: cada corrida abre su ventana) ---

    def _lanzar(self, codigo):
        """Ejecuta el código en un proceso nuevo con ventana propia."""
        self.detener_proceso()
        fd, ruta = tempfile.mkstemp(prefix='pilas3d_bloques_',
                                    suffix='.py')
        os.write(fd, codigo.encode('utf-8'))
        os.close(fd)
        fd, salida = tempfile.mkstemp(prefix='pilas3d_bloques_',
                                      suffix='.txt')
        self._salida = os.fdopen(fd, 'w+b')
        self._proc = subprocess.Popen(
            [sys.executable, _RUNNER, ruta],
            stdout=self._salida, stderr=subprocess.STDOUT)
        self.ultimo = {'estado': 'ejecutando', 'salida': ''}

    def detener_proceso(self):
        """Mata la corrida en curso (botón detener)."""
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
            self.ultimo = {'estado': 'detenido', 'salida':
                           self._leer_salida()}

    def _leer_salida(self):
        if self._salida is None:
            return ''
        self._salida.flush()
        self._salida.seek(0)
        return self._salida.read().decode('utf-8', 'replace')

    def estado_actual(self):
        """Refresca ``ultimo`` mirando si el subproceso sigue vivo."""
        if self._proc is not None:
            codigo = self._proc.poll()
            if codigo is None:
                self.ultimo = {'estado': 'ejecutando',
                               'salida': self._leer_salida()}
            else:
                self.ultimo = {
                    'estado': 'ok' if codigo == 0 else 'error',
                    'salida': self._leer_salida()}
                self._proc = None
        return self.ultimo

    def _reiniciar_escena(self):
        """Bandera verde estilo Scratch: saca los actores y las tareas
        que dejó la corrida anterior (re-registra el drenaje)."""
        for actor in list(self.pilas.escena.actores):
            actor.eliminar()
        self.pilas.tareas.eliminar_todas()
        self.enganchar()

    def _ejecutar(self, codigo):
        self._reiniciar_escena()
        ns = {'pilas': self.pilas}
        import pilas3d
        ns['pilas3d'] = pilas3d
        salida = io.StringIO()
        try:
            with contextlib.redirect_stdout(salida):
                exec(compile(codigo, '<bloques>', 'exec'), ns)
            self.ultimo = {'estado': 'ok', 'salida': salida.getvalue()}
        except Exception:
            self.ultimo = {'estado': 'error',
                           'salida': salida.getvalue()
                                     + traceback.format_exc(limit=3)}

    # -- lado HTTP (hilo aparte) ---------------------------------------------

    def iniciar(self, puerto=PUERTO):
        puente = self
        web = self.directorio_web

        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass            # silencio en la terminal

            def _json(self, datos, estado=200):
                cuerpo = json.dumps(datos).encode('utf-8')
                self.send_response(estado)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)

            def do_GET(self):
                if self.path == '/resultado':
                    self._json(puente.estado_actual())
                    return
                # estáticos de bloques_web/ (path confinado al dir)
                ruta = self.path.split('?')[0].lstrip('/') or 'index.html'
                destino = os.path.normpath(
                    os.path.join(web, ruta))
                if not destino.startswith(os.path.abspath(web)) \
                        or not os.path.isfile(destino):
                    self.send_error(404)
                    return
                self._servir(destino)

            def _servir(self, destino):
                tipos = {'.html': 'text/html', '.js': 'text/javascript',
                         '.css': 'text/css', '.png': 'image/png',
                         '.json': 'application/json'}
                tipo = tipos.get(os.path.splitext(destino)[1],
                                 'application/octet-stream')
                with open(destino, 'rb') as f:
                    cuerpo = f.read()
                self.send_response(200)
                self.send_header('Content-Type', tipo)
                self.send_header('Content-Length', str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)

            def do_POST(self):
                if self.path == '/detener':
                    puente.detener_proceso()
                    self._json({'estado': 'detenido'})
                    return
                if self.path != '/codigo':
                    self.send_error(404)
                    return
                largo = int(self.headers.get('Content-Length', 0))
                try:
                    datos = json.loads(self.rfile.read(largo) or b'{}')
                except ValueError:
                    self._json({'estado': 'error', 'salida':
                                'JSON inválido'}, 400)
                    return
                codigo = datos.get('codigo', '')
                if not isinstance(codigo, str) or not codigo.strip():
                    self._json({'estado': 'error', 'salida':
                                'código vacío'}, 400)
                    return
                if puente.pilas is None:
                    puente._lanzar(codigo)   # subproceso + ventana
                    self._json({'estado': 'lanzado'})
                else:
                    puente.cola.put(codigo)  # corre en la ventana viva
                    self._json({'estado': 'encolado'})

        self._srv = ThreadingHTTPServer(('127.0.0.1', puerto), Handler)
        hilo = threading.Thread(target=self._srv.serve_forever,
                                daemon=True)
        hilo.start()
        return 'http://127.0.0.1:%d/' % self._srv.server_address[1]

    def detener(self):
        self.detener_proceso()
        if self._srv is not None:
            self._srv.shutdown()
            self._srv = None
