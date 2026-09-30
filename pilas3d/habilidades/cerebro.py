# -*- encoding: utf-8 -*-
"""Cerebro: el actor piensa con la IA local y actúa solo.

Cada ``cada`` segundos la habilidad describe el estado del actor
(posición, actores cercanos, objetivo) a un LLM local (Ollama) y el
modelo responde UNA acción de una lista cerrada. La acción se aplica
al actor en el hilo principal — nunca se ejecuta código arbitrario::

    mono = pilas.actores.Mono()
    mono.aprender(pilas.habilidades.Cerebro,
                  cada=3,
                  personalidad='sos un mono tímido que evita a todos',
                  objetivo=jugador)

El pensamiento corre en un hilo (el juego nunca se congela) y mientras
el modelo "piensa" el actor simplemente espera la orden siguiente.
"""

import json
import math
import re
import threading
from collections import deque

from pilas3d.habilidades.habilidad import Habilidad

SYSTEM = """\
Sos el cerebro de un actor en un videojuego 3D educativo (Pilas3D).
Respondés SOLO con un JSON de una acción, sin texto extra.

Acciones posibles:
  {"accion":"mover","dx":<n>,"dz":<n>}   — se mueve dx, dz metros
  {"accion":"girar","grados":<n>}        — gira n grados
  {"accion":"ir_a","x":<n>,"z":<n>}      — se teletransporta a (x, z)
  {"accion":"decir","texto":"<t>"}       — muestra un globo de diálogo
  {"accion":"acercarse"}                 — un paso hacia el objetivo
  {"accion":"alejarse"}                  — un paso lejos del objetivo
  {"accion":"esperar"}                   — no hace nada este turno

Reglas: el mundo se mide en metros; el suelo está en y=0; distancias
razonables son entre -5 y 5. Contestá siempre un solo JSON válido.\
"""

_ACCIONES = ('mover', 'girar', 'ir_a', 'decir',
             'acercarse', 'alejarse', 'esperar')

_JSON = re.compile(r'\{[^{}]*\}')


def _num(v, defecto=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


def parsear(texto):
    """Extrae la acción JSON de la respuesta del modelo.

    Devuelve el dict o ``None`` si no hay un JSON válido con una
    acción conocida. Separada para poder probarla sin Ollama."""
    m = _JSON.search(texto or '')
    if not m:
        return None
    try:
        datos = json.loads(m.group())
    except ValueError:
        return None
    if not isinstance(datos, dict):
        return None
    accion = str(datos.get('accion', '')).lower()
    if accion not in _ACCIONES:
        return None
    datos['accion'] = accion
    return datos


class Cerebro(Habilidad):
    """Habilidad: un LLM local decide qué hace el actor cada N s."""

    def iniciar(self, receptor, cada=3.0, personalidad='',
                objetivo=None, radio_vista=10.0, modelo=None):
        super(Cerebro, self).iniciar(receptor)
        self.cada = cada                # segundos entre decisiones
        self.personalidad = personalidad
        self.objetivo = objetivo        # actor a observar (jugador…)
        self.radio_vista = radio_vista
        self.modelo = modelo            # None = PILAS3D_IA_MODELO
        self._espera = min(1.0, cada)   # primera decisión rápida
        self._ocupado = False           # una petición a la vez
        self._pendientes = deque()
        self.ultima_decision = None     # para depurar
        self.fallos = 0                 # respuestas no entendidas

    # -- pensar (en hilo, nunca bloquea el juego) ----------------------------

    def _describir_estado(self):
        r = self.receptor
        partes = [
            u'Estás en posición (x=%.1f, z=%.1f) mirando %d grados.'
            % (r.x, r.z, int(r.rotacion_y) % 360)]
        if self.personalidad:
            partes.insert(0, u'Tu personalidad: %s.' % self.personalidad)
        if self.objetivo is not None and \
                self.objetivo.esta_en_escena():
            o = self.objetivo
            d = math.hypot(o.x - r.x, o.z - r.z)
            partes.append(
                u'Tu objetivo está a %.1f m en (x=%.1f, z=%.1f).'
                % (d, o.x, o.z))
        cerca = []
        try:
            for a in r.pilas.escena_actual().actores:
                if a is r or not a.esta_en_escena():
                    continue
                d = math.hypot(a.x - r.x, a.z - r.z)
                if d <= self.radio_vista:
                    cerca.append(
                        u'%s a %.1f m' % (a.__class__.__name__, d))
        except AttributeError:
            pass
        if cerca:
            partes.append(u'Ves cerca: ' + u', '.join(cerca[:5]) + u'.')
        return u' '.join(partes) + u' ¿Qué hacés?'

    def _pensar(self):
        try:
            from pilas3d.ia import asistente
            texto = asistente.llamar_ollama(
                self._describir_estado(), system=SYSTEM,
                modelo=self.modelo or asistente.MODELO)
            datos = parsear(texto)
            if datos is None:
                self.fallos += 1
            else:
                self._pendientes.append(datos)
        except Exception:
            self.fallos += 1        # sin Ollama: el actor espera
        finally:
            self._ocupado = False

    # -- actuar (hilo principal, vía actualizar) -----------------------------

    def _hacia(self, signo):
        r = self.receptor
        o = self.objetivo
        if o is None or not o.esta_en_escena():
            return
        dx, dz = o.x - r.x, o.z - r.z
        d = math.hypot(dx, dz)
        if d < 0.01:
            return
        r.x += signo * dx / d * 0.5
        r.z += signo * dz / d * 0.5
        r.mirar_hacia(r.x + signo * dx, r.z + signo * dz)

    def _aplicar(self, datos):
        r = self.receptor
        a = datos['accion']
        self.ultima_decision = a
        if a == 'mover':
            dx = _num(datos.get('dx'))
            dz = _num(datos.get('dz'))
            r.x += dx
            r.z += dz
            if dx or dz:
                r.mirar_hacia(r.x + dx, r.z + dz)
        elif a == 'girar':
            r.rotacion_y += _num(datos.get('grados'))
        elif a == 'ir_a':
            r.x = _num(datos.get('x'))
            r.z = _num(datos.get('z'))
        elif a == 'decir':
            texto = str(datos.get('texto', ''))[:200]
            if texto:
                try:
                    r.decir(texto, duracion=self.cada)
                except TypeError:
                    r.decir(texto)   # p.ej. ActorIA.decir no lleva duracion
        elif a == 'acercarse':
            self._hacia(+1)
        elif a == 'alejarse':
            self._hacia(-1)
        # 'esperar': no hace nada

    def actualizar(self):
        while self._pendientes:
            self._aplicar(self._pendientes.popleft())
        if self._ocupado:
            return
        self._espera -= self.pilas.dt
        if self._espera > 0:
            return
        self._espera = self.cada
        self._ocupado = True
        threading.Thread(target=self._pensar, daemon=True).start()
