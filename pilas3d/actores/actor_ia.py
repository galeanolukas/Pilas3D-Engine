# -*- encoding: utf-8 -*-
"""ActorIA: un personaje que conversa con IA local.

Junta las dos piezas del módulo ``pilas3d.ia``:

- **responde** con el asistente de Ollama (``preguntar``),
- **habla** con voz sintetizada por Piper (``hablar``), y
- muestra la respuesta como subtítulo en pantalla (``decir``).

Todo es asíncrono: Ollama y Piper corren en un hilo y el resultado
vuelve por una cola que se drena en ``actualizar`` (OpenGL y el
audio no son thread-safe)::

    npc = pilas.actores.ActorIA('robot')
    npc.preguntar('hola, ¿en qué juego estamos?')
    npc.hablar('bienvenidos')          # solo voz
    npc.decir('bienvenidos')           # solo subtítulo
    npc.al_responder = mi_funcion      # callback(respuesta)
    npc.habla = False                  # responder en silencio
"""

import threading
from collections import deque

from pyglet.gl import GL_TRIANGLES

from pilas3d.actores.actor import Actor


class ActorIA(Actor):
    """NPC con IA: ``preguntar`` (Ollama) + ``hablar`` (Piper)."""

    def __init__(self, pilas, personaje='robot', x=0, y=0, z=0,
                 habla=True, nombre=None, voz=None, alto_globo=2.4):
        self._pendientes = deque()
        self.al_responder = None
        self.ultima_respuesta = ''
        self.habla = habla
        #: Voz de Piper del actor (None = ``PILAS3D_VOZ`` o la
        #: por defecto). Ej. ``'es_AR-daniela-high'``.
        self.voz = voz
        self.nombre = nombre or (personaje
                                 if isinstance(personaje, str)
                                 else 'npc')
        super(ActorIA, self).__init__(pilas, x=x, y=y, z=z)
        self.cuerpo = self._crear_cuerpo(personaje)
        #: Bocadillo de diálogo que sigue al NPC (``Globo`` overlay).
        self.subtitulo = pilas.actores.Globo(
            actor=self.cuerpo, alto=alto_globo, tamano=14)

    # -- cuerpo visible -----------------------------------------------------

    def _crear_cuerpo(self, personaje):
        """El personaje visible: nombre de Personaje o ruta de modelo."""
        a = self.pilas.actores
        if isinstance(personaje, Actor):
            return personaje
        if isinstance(personaje, str) and personaje.lower().endswith(
                ('.glb', '.gltf')):
            return a.ModeloGLTF(personaje)
        if isinstance(personaje, str) and personaje.lower().endswith(
                '.obj'):
            return a.Modelo(personaje)
        fabrica = getattr(a, str(personaje).capitalize(), None)
        if fabrica is None:
            fabrica = a.Robot
        return fabrica()

    def _generar_geometria(self):
        # ActorIA no dibuja nada propio: el cuerpo es otro actor
        return [], [], GL_TRIANGLES, None, None

    def dibujar(self):
        pass

    # -- charla -------------------------------------------------------------

    def decir(self, texto):
        """Muestra la respuesta en el globo (paginado si es larga)
        y dispara el callback."""
        self.ultima_respuesta = texto
        self.subtitulo.decir("%s: %s" % (self.nombre, texto))
        if self.al_responder:
            self.al_responder(texto)

    def preguntar(self, texto, modelo=None):
        """Le pregunta al asistente local; responde y habla sola."""
        def trabajo():
            try:
                from pilas3d.ia import asistente
                respuesta = asistente.preguntar(texto, modelo=modelo)
                self._pendientes.append(('decir', respuesta))
                if self.habla:
                    self._pendientes.append(
                        ('hablar', (respuesta, self.voz)))
            except Exception as e:
                self._pendientes.append(('error', e))
        threading.Thread(target=trabajo, daemon=True).start()

    def hablar(self, texto, voz=None):
        """Sintetiza ``texto`` con Piper y lo reproduce (asíncrono)."""
        cual = voz or self.voz
        def trabajo():
            try:
                from pilas3d.ia import voz as modulo
                ruta = modulo.sintetizar(texto, voz=cual)
                self._pendientes.append(('sonido', ruta))
            except Exception as e:
                self._pendientes.append(('error', e))
        threading.Thread(target=trabajo, daemon=True).start()

    # -- ciclo de vida ------------------------------------------------------

    def _drenar(self):
        while self._pendientes:
            tipo, dato = self._pendientes.popleft()
            if tipo == 'decir':
                self.decir(dato)
            elif tipo == 'hablar':
                texto, cual = dato
                self.hablar(texto, voz=cual)
            elif tipo == 'sonido':
                self.pilas.sonidos.cargar(dato).reproducir()
            elif tipo == 'error':
                self.decir("(sin conexión con la IA: %s)" % dato)

    def actualizar(self):
        self._drenar()
        c = self.cuerpo
        c.posicion = self.posicion
        c.rotacion_y = self.rotacion_y

    def eliminar(self):
        self.cuerpo.eliminar()
        self.subtitulo.eliminar()
        super(ActorIA, self).eliminar()
