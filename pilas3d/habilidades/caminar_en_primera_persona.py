# -*- encoding: utf-8 -*-
"""Caminar en primera persona, estilo Doom.

- El mouse gira la vista (rotacion_y del actor = yaw, pitch interno).
- WASD/flechas mueven al actor sobre el plano XZ relativo a la vista.
- La cámara se posiciona en la "cabeza" del actor.
- Los obstáculos de la escena (paredes) bloquean el movimiento.

>>> jugador.aprender(pilas.habilidades.CaminarEnPrimeraPersona)
"""

import math

from pyglet.window import mouse

from pilas3d import colisiones
from pilas3d.habilidades.habilidad import Habilidad


class CaminarEnPrimeraPersona(Habilidad):
    def iniciar(self, receptor, velocidad=6, altura=1.6,
                sensibilidad=0.15):
        super(CaminarEnPrimeraPersona, self).iniciar(receptor)
        self.velocidad = velocidad
        self.altura = altura
        self.sensibilidad = sensibilidad
        self.pitch = 0.0

        ventana = self.pilas.ventana
        if ventana is not None:
            ventana.set_exclusive_mouse(True)
            ventana.push_handlers(on_mouse_motion=self._on_mouse_motion)

    def _on_mouse_motion(self, x, y, dx, dy):
        self.receptor.rotacion_y -= dx * self.sensibilidad
        self.pitch = max(-89.0, min(89.0, self.pitch + dy * 0.15))

    def direccion_vista(self):
        """Vector 3D unitario hacia donde mira el jugador."""
        yaw = math.radians(self.receptor.rotacion_y)
        pitch = math.radians(self.pitch)
        return (
            -math.sin(yaw) * math.cos(pitch),
            math.sin(pitch),
            -math.cos(yaw) * math.cos(pitch),
        )

    def actualizar(self):
        r = self.receptor
        c = self.pilas.control
        yaw = math.radians(r.rotacion_y)

        # Adelante y costado en el plano XZ (yaw=0 mira hacia -Z).
        fwd_x, fwd_z = -math.sin(yaw), -math.cos(yaw)
        der_x, der_z = -fwd_z, fwd_x

        dx = dz = 0.0
        if c.arriba:
            dx += fwd_x
            dz += fwd_z
        if c.abajo:
            dx -= fwd_x
            dz -= fwd_z
        if c.derecha:
            dx += der_x
            dz += der_z
        if c.izquierda:
            dx -= der_x
            dz -= der_z

        if dx or dz:
            norma = math.sqrt(dx * dx + dz * dz)
            v = self.velocidad * self.pilas.dt
            x = r.x + dx / norma * v
            z = r.z + dz / norma * v

            escena = self.pilas.escena_actual()
            cajas = [o.obtener_caja() for o in escena.obstaculos]
            r.x, r.z = colisiones.resolver_circulo_en_cajas(
                x, z, r.radio_de_colision, cajas)

        # La cámara se posa en la cabeza del actor.
        camara = self.pilas.escena_actual().camara
        camara.posicion = (r.x, r.y + self.altura, r.z)
        vx, vy, vz = self.direccion_vista()
        camara.objetivo = (r.x + vx, r.y + self.altura + vy, r.z + vz)
