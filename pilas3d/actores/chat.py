# -*- encoding: utf-8 -*-
"""Chat: hablarle a un actor con cerebro (o con IA) desde el teclado.

Al pulsar la tecla se abre un cuadro de texto; el mensaje viaja al
LLM local junto con el estado del actor, y la respuesta vuelve como
una acción del ``Cerebro`` — así el NPC no solo contesta, también
**actúa**: ``"vení"`` -> ``acercarse``, ``"hola"`` -> ``decir``::

    mono.aprender(pilas.habilidades.Cerebro,
                  personalidad='sos un mono charlatan')
    pilas.actores.Chat(mono)          # pulsá T y escribile

Sin cerebro se conversa igual: el actor responde con su globo usando
``asistente.preguntar`` (y si el npc es un ``ActorIA`` se delega a su
propio ``preguntar``, con voz incluida).
"""

import threading
from collections import deque

from pyglet.gl import GL_TRIANGLES

from pilas3d.actores.actor import Actor


class Chat(Actor):
    """Actor invisible: puente entre el teclado y el cerebro del npc."""

    def __init__(self, pilas, npc, tecla='t', etiqueta=None):
        """``npc`` es el actor a charlar; ``tecla`` es un nombre de
        ``pilas.simbolos`` ('t', 'e', 'ESPACIO'…) o un símbolo crudo.
        ``etiqueta`` es el rótulo del cuadro de texto."""
        self._pendientes = deque()
        self._ocupado = False
        self.npc = npc
        self.tecla = tecla
        self.etiqueta = etiqueta
        super(Chat, self).__init__(pilas)
        self._conectar_tecla()

    def _generar_geometria(self):
        # no dibuja nada propio: solo gestiona entrada y respuestas
        return [], [], GL_TRIANGLES, None, None

    def dibujar(self):
        pass

    # -- entrada ------------------------------------------------------------

    def _simbolo_tecla(self):
        if isinstance(self.tecla, str):
            return getattr(self.pilas.simbolos, self.tecla,
                           self.pilas.simbolos.t)
        return self.tecla

    def _conectar_tecla(self):
        """Se engancha a cuando_pulsa_tecla sin pisar al anterior."""
        escena = self.pilas.escena_actual()
        anterior = escena.cuando_pulsa_tecla
        simbolo = self._simbolo_tecla()

        def al_pulsar(s):
            if s == simbolo:
                self.abrir()
                return
            anterior(s)
        escena.cuando_pulsa_tecla = al_pulsar

    def abrir(self, etiqueta=None):
        """Abre el cuadro para escribirle al npc (también a mano)."""
        if self._ocupado or not self.esta_en_escena():
            return
        nombre = getattr(self.npc, 'nombre', None) or \
            self.npc.__class__.__name__.lower()
        self.pilas.pedir_texto(
            etiqueta or self.etiqueta or
            ('decile a %s:' % nombre),
            al_aceptar=self.decir_a)

    # -- diálogo ------------------------------------------------------------

    def _cerebro(self):
        """El Cerebro aprendido por el npc, si tiene."""
        from pilas3d.habilidades.cerebro import Cerebro
        for h in getattr(self.npc, '_habilidades', []):
            if isinstance(h, Cerebro):
                return h
        return None

    def decir_a(self, texto):
        """Envía ``texto`` al npc; la respuesta llega asíncrona."""
        texto = (texto or '').strip()
        if not texto or self._ocupado:
            return
        # un ActorIA ya sabe responder solo (con voz y todo)
        if self._cerebro() is None and hasattr(self.npc, 'preguntar'):
            self.npc.preguntar(texto)
            return
        self._ocupado = True
        threading.Thread(target=self._responder, args=(texto,),
                         daemon=True).start()

    def _responder(self, texto):
        """(hilo) Pregunta al LLM y encola qué hacer con la respuesta."""
        try:
            from pilas3d.ia import asistente
            from pilas3d.habilidades.cerebro import SYSTEM, parsear
            cerebro = self._cerebro()
            if cerebro is not None:
                # mismo canal que el cerebro: la respuesta es una
                # acción (típicamente "decir", pero puede moverse)
                prompt = (cerebro._describir_estado() +
                          u' El jugador te dice: "%s"' % texto)
                crudo = asistente.llamar_ollama(
                    prompt, system=SYSTEM,
                    modelo=cerebro.modelo or asistente.MODELO)
                datos = parsear(crudo)
                if datos is not None:
                    self._pendientes.append(('accion', datos))
                else:
                    self._pendientes.append(('decir', crudo[:160]))
            else:
                resp = asistente.preguntar(texto)
                self._pendientes.append(('decir', resp))
        except Exception:
            self._pendientes.append(
                ('decir', '(no pude hablar con la ia local)'))
        finally:
            self._ocupado = False

    # -- ciclo de vida ------------------------------------------------------

    def actualizar(self):
        """Drena las respuestas en el hilo principal."""
        while self._pendientes:
            tipo, dato = self._pendientes.popleft()
            if tipo == 'accion':
                cerebro = self._cerebro()
                if cerebro is not None:
                    cerebro._aplicar(dato)   # mover, decir, acercarse…
                elif dato.get('accion') == 'decir':
                    self.npc.decir(str(dato.get('texto', '')))
            elif tipo == 'decir':
                self.npc.decir(str(dato))
