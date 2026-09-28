# -*- encoding: utf-8 -*-
"""Cámara de la escena.

Equivalente a ``pilasengine.escenas.camara`` pero en 3D: tiene una
posición (x, y, z) y un ``objetivo`` hacia el que mira.

Además ofrece ``usar_control_orbital()``: con el botón izquierdo del
mouse se orbita alrededor del objetivo y con la rueda se acerca/aleja.
"""

import math

from pyglet.math import Mat4, Vec3
from pyglet.window import mouse


class Camara(object):
    def __init__(self, escena, x=0, y=5, z=12, objetivo=(0, 0, 0)):
        self.escena = escena
        self.x = x
        self.y = y
        self.z = z
        self.objetivo = objetivo
        self._orbital = False
        self._orbital_boton = mouse.LEFT
        self._orbital_distancia = 0.0
        self._orbital_yaw = 0.0
        self._orbital_pitch = 0.0
        self._seguir = None
        self.seguir_modo = 'tercera'
        self.seguir_distancia = 6.0
        self.seguir_altura = 3.0
        self.seguir_ojos = 1.5
        self.seguir_suavizado = 8.0

    @property
    def posicion(self):
        return (self.x, self.y, self.z)

    @posicion.setter
    def posicion(self, valor):
        self.x, self.y, self.z = valor

    def matriz_vista(self):
        """Retorna la matriz view para el shader."""
        return Mat4.look_at(
            Vec3(self.x, self.y, self.z),
            Vec3(*self.objetivo),
            Vec3(0, 1, 0),
        )

    # -- rayo / disparo -----------------------------------------------------

    def direccion(self):
        """Vector unitario desde la cámara hacia el objetivo."""
        o = Vec3(self.x, self.y, self.z)
        return (Vec3(*self.objetivo) - o).normalize()

    def rayo_desde_mouse(self, x=None, y=None, ancho=None, alto=None,
                         fov=60.0):
        """Rayo de mundo que sale de la cámara y pasa por el píxel
        (x, y) del mouse. Retorna ``(origen, direccion)``; sin x/y usa
        la posición actual del mouse.

        Es la pieza de los controles de mouse de pilas: ``actor_bajo_
        mouse`` para clicks y ``punto_bajo_mouse`` para arrastrar.
        """
        pilas = self.escena.pilas
        ventana = pilas.ventana
        if x is None:
            x = pilas.control.mouse_x
        if y is None:
            y = pilas.control.mouse_y
        if ancho is None:
            ancho = ventana.width if ventana is not None else 640
        if alto is None:
            alto = ventana.height if ventana is not None else 480

        # píxel -> coordenadas de vista (frustum simétrico, fov=60)
        f = math.tan(math.radians(fov) / 2.0)
        nx = (2.0 * x / ancho - 1.0) * f * (ancho / float(alto))
        ny = (1.0 - 2.0 * y / alto) * f

        frente = self.direccion()
        derecha = frente.cross(Vec3(0, 1, 0)).normalize()
        arriba = derecha.cross(frente).normalize()
        dir_mundo = (frente + derecha * nx + arriba * ny).normalize()
        return Vec3(self.x, self.y, self.z), dir_mundo

    def _intersectar_rayo(self, origen, direccion, actores, alcance):
        """El actor más cercano alcanzado por el rayo (o None)."""
        mejor = None
        t_min = alcance
        for actor in actores:
            radio = actor.radio_de_disparo
            if radio is None:
                radio = actor.radio_de_colision
            oc = Vec3(*actor.posicion) - origen
            t = oc.dot(direccion)
            if t < 0 or t > t_min:
                continue
            punto = origen + direccion * t
            if (Vec3(*actor.posicion) - punto).length() <= radio:
                mejor = actor
                t_min = t
        return mejor

    def disparar_rayo(self, actores, alcance=100.0):
        """Retorna el actor más cercano alcanzado por un rayo de vista.

        Intersección rayo-esfera usando ``radio_de_disparo`` de cada
        actor (o ``radio_de_colision`` si no lo define). Devuelve None
        si no alcanza a nadie.
        """
        origen = Vec3(self.x, self.y, self.z)
        return self._intersectar_rayo(origen, self.direccion(),
                                      actores, alcance)

    def actor_bajo_mouse(self, actores=None, alcance=200.0,
                         x=None, y=None):
        """El actor más cercano bajo el puntero (o None).

        ``actores`` por defecto son los de la escena actual."""
        if actores is None:
            actores = list(self.escena.actores)
        origen, direccion = self.rayo_desde_mouse(x, y)
        return self._intersectar_rayo(origen, direccion, actores,
                                      alcance)

    def punto_bajo_mouse(self, y_plano=0.0, x=None, y=None):
        """Punto del mundo donde el rayo del mouse corta el plano
        horizontal ``y = y_plano`` (None si el rayo no lo toca)."""
        origen, direccion = self.rayo_desde_mouse(x, y)
        if abs(direccion.y) < 1e-8:
            return None
        t = (y_plano - origen.y) / direccion.y
        if t < 0:
            return None
        p = origen + direccion * t
        return (p.x, p.y, p.z)

    # -- seguimiento a un actor (1a/2a/3a persona) -------------------------

    def seguir_a(self, actor, modo='tercera', distancia=6.0,
                 altura=3.0, ojos=1.5, suavizado=8.0):
        """Pega la cámara a ``actor``, como en los juegos con tecla V.

        ``modo``:
          ``'primera'`` — desde los ojos del actor, mira a donde mira
          él (usa ``rotacion_y``).
          ``'segunda'`` — cámara frontal: queda delante mirándolo
          (como lo vería otro personaje).
          ``'tercera'`` — detrás y arriba, vista de hombro.

        ``distancia``/``altura`` aplican a segunda y tercera;
        ``ojos`` es la altura de los ojos; ``suavizado`` interpola el
        movimiento (0 = instantáneo). ``dejar_de_seguir()`` lo suelta.
        """
        if modo not in ('primera', 'segunda', 'tercera'):
            raise ValueError("modo debe ser 'primera', 'segunda' o "
                             "'tercera'")
        self._seguir = actor
        self.seguir_modo = modo
        self.seguir_distancia = distancia
        self.seguir_altura = altura
        self.seguir_ojos = ojos
        self.seguir_suavizado = suavizado

    def dejar_de_seguir(self):
        """Suelta el seguimiento; la cámara queda donde está."""
        self._seguir = None

    def _frente_del_actor(self, actor):
        """Vector al que mira el actor según su ``rotacion_y``."""
        rad = math.radians(actor.rotacion_y)
        return -math.sin(rad), math.cos(rad)

    def actualizar(self, dt):
        """Actualiza el seguimiento (lo llama la escena cada frame)."""
        a = self._seguir
        if a is None or not a.esta_en_escena():
            return
        fx, fz = self._frente_del_actor(a)
        ojos = a.y + self.seguir_ojos

        if self.seguir_modo == 'primera':
            px, py, pz = a.x, ojos, a.z
            objetivo = (a.x + fx, ojos, a.z + fz)
        elif self.seguir_modo == 'segunda':
            d, h = self.seguir_distancia, self.seguir_altura
            px, py, pz = a.x + fx * d, a.y + h, a.z + fz * d
            objetivo = (a.x, ojos, a.z)
        else:   # tercera
            d, h = self.seguir_distancia, self.seguir_altura
            px, py, pz = a.x - fx * d, a.y + h, a.z - fz * d
            objetivo = (a.x, ojos, a.z)

        k = 1.0 if self.seguir_suavizado <= 0 \
            else min(1.0, dt * self.seguir_suavizado)
        self.x += (px - self.x) * k
        self.y += (py - self.y) * k
        self.z += (pz - self.z) * k
        self.objetivo = objetivo

    # -- control orbital con el mouse -------------------------------------

    def usar_control_orbital(self, boton=mouse.LEFT, tecla=None):
        """Activa órbita con ``boton`` + drag, o con ``tecla`` +
        mover el mouse (sin click), y zoom con la rueda.

        La cámara gira siempre alrededor de ``self.objetivo``. Con
        ``boton=mouse.RIGHT`` queda el izquierdo libre para habilidades
        como ``Arrastrable``. Con ``tecla=simbolos.ESPACIO`` se orbita
        manteniendo espacio y moviendo el mouse.
        """
        self._orbital_boton = boton
        self._orbital_tecla = tecla
        ox, oy, oz = self.objetivo
        dx, dy, dz = self.x - ox, self.y - oy, self.z - oz
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        self._orbital_distancia = d
        self._orbital_pitch = math.degrees(math.asin(dy / d))
        self._orbital_yaw = math.degrees(math.atan2(dx, dz))
        self._orbital = True

        ventana = self.escena.pilas.ventana
        if ventana is not None:
            ventana.push_handlers(
                on_mouse_drag=self._on_mouse_drag,
                on_mouse_scroll=self._on_mouse_scroll,
                on_mouse_motion=self._on_mouse_motion,
            )

    def _on_mouse_drag(self, x, y, dx, dy, botones, modificadores):
        if self._orbital_boton is None or \
                not (botones & self._orbital_boton):
            return
        self._orbitar(dx, dy)

    def _on_mouse_motion(self, x, y, dx, dy):
        """Órbita sin click: se activa mientras ``tecla`` está
        pulsada (modo espacio + mouse)."""
        tecla = self._orbital_tecla
        ventana = self.escena.pilas.ventana
        if tecla is None or ventana is None:
            return
        if not ventana.teclas[tecla]:
            return
        self._orbitar(dx, dy)

    def _orbitar(self, dx, dy):
        self._orbital_yaw += dx * 0.4
        self._orbital_pitch = max(
            -89.0, min(89.0, self._orbital_pitch + dy * 0.4))
        self._actualizar_orbita()

    def _on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self._orbital_distancia = max(
            1.0, min(200.0,
                     self._orbital_distancia * (1.0 - scroll_y * 0.1)))
        self._actualizar_orbita()

    def _actualizar_orbita(self):
        ox, oy, oz = self.objetivo
        pitch = math.radians(self._orbital_pitch)
        yaw = math.radians(self._orbital_yaw)
        d = self._orbital_distancia
        self.x = ox + d * math.cos(pitch) * math.sin(yaw)
        self.y = oy + d * math.sin(pitch)
        self.z = oz + d * math.cos(pitch) * math.cos(yaw)
