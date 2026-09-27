# -*- encoding: utf-8 -*-
"""Sistema de partículas (GL_POINTS) para efectos: fuego, humo,
lluvia, explosiones.

Cada partícula vive ``vida`` segundos, sale de la posición del actor
con ``velocidad`` en ``direccion`` ± ``dispersion``, y desvanece su
alpha con la edad. Con ``ciclico=True`` se re-emiten solas.
"""

import random

from pyglet.gl import GL_POINTS

from pilas3d import colores
from pilas3d.actores.actor import Actor


class Particulas(Actor):
    """Emisor de partículas.

    >>> fuego = pilas.actores.Particulas(
    ...     cantidad=200, vida=1.5, velocidad=3, dispersion=0.7,
    ...     direccion=(0, 1, 0), gravedad=1,
    ...     color=pilas.colores.naranja,
    ...     color_final=pilas.colores.rojo, tamano=6)

    También hay presets: ``Particulas.fuego(pilas)``,
    ``Particulas.humo(pilas)``, ``Particulas.lluvia(pilas)`` y
    ``Particulas.explosion(pilas, x, y, z)``.
    """

    def __init__(self, pilas, cantidad=100, vida=2.0, velocidad=3.0,
                 direccion=(0, 1, 0), dispersion=0.5, gravedad=0.0,
                 color=None, color_final=None, tamano=4.0,
                 ciclico=True, x=0, y=0, z=0):
        self.cantidad = cantidad
        self.vida = vida
        self.velocidad = velocidad
        self.direccion = direccion
        self.dispersion = dispersion
        self.gravedad = gravedad
        self.color_final = (colores.normalizar(color_final)
                            if color_final else None)
        self.ciclico = ciclico
        self.emitiendo = True
        self.punto_tamano = tamano

        # estado por partícula: pos local, velocidad, edad, ttl
        self._px = [0.0] * cantidad
        self._py = [0.0] * cantidad
        self._pz = [0.0] * cantidad
        self._vx = [0.0] * cantidad
        self._vy = [0.0] * cantidad
        self._vz = [0.0] * cantidad
        self._edad = [0.0] * cantidad
        self._ttl = [1.0] * cantidad
        for i in range(cantidad):
            self._reset(i, repartir=True)

        super(Particulas, self).__init__(pilas, x=x, y=y, z=z)
        if color is not None:
            self.color = color

    # -- simulación ----------------------------------------------------------

    def _reset(self, i, repartir=False):
        """Re-emite la partícula i desde el origen del emisor."""
        dx, dy, dz = self.direccion
        d = self.dispersion
        v = self.velocidad
        self._vx[i] = (dx + random.uniform(-d, d)) * v
        self._vy[i] = (dy + random.uniform(-d, d)) * v
        self._vz[i] = (dz + random.uniform(-d, d)) * v
        self._px[i] = self._py[i] = self._pz[i] = 0.0
        self._ttl[i] = self.vida * random.uniform(0.6, 1.0)
        # repartir edades al arrancar para no ver el "cañón" inicial
        self._edad[i] = (random.uniform(0, self._ttl[i])
                         if repartir else 0.0)

    def actualizar(self):
        dt = self.pilas.dt
        g = self.gravedad
        vivas = False
        for i in range(self.cantidad):
            self._edad[i] += dt
            if self._edad[i] >= self._ttl[i]:
                if self.ciclico and self.emitiendo:
                    self._reset(i)
                else:
                    continue    # muerta: queda con edad >= ttl
            vivas = True
            self._vy[i] -= g * dt
            self._px[i] += self._vx[i] * dt
            self._py[i] += self._vy[i] * dt
            self._pz[i] += self._vz[i] * dt
        self._volcar()
        if not vivas and not self.ciclico:
            self.eliminar()   # estallido único terminado: se auto-destruye

    def _volcar(self):
        """Escribe posiciones y colores (alpha por edad) en la lista."""
        if self._vertex_list is None:
            return
        r, g, b = colores.normalizar(self._color)
        if self.color_final:
            r2, g2, b2 = self.color_final
        pos = self._vertex_list.position
        col = self._vertex_list.color
        posiciones = []
        colores_v = []
        for i in range(self.cantidad):
            t = min(self._edad[i] / self._ttl[i], 1.0)
            posiciones += [self._px[i], self._py[i], self._pz[i]]
            if self.color_final:
                colores_v += [r + (r2 - r) * t, g + (g2 - g) * t,
                              b + (b2 - b) * t, 1.0 - t]
            else:
                colores_v += [r, g, b, 1.0 - t]
        pos[:] = posiciones
        col[:] = colores_v

    def pausar(self):
        """Deja de emitir; las vivas terminan su vida."""
        self.emitiendo = False

    def reanudar(self):
        self.emitiendo = True

    # -- render ---------------------------------------------------------------

    def _generar_geometria(self):
        cantidad = self.cantidad
        posiciones = [0.0] * (cantidad * 3)
        normales = [0.0] * (cantidad * 3)
        colores_v = [0.0] * (cantidad * 4)
        return posiciones, normales, GL_POINTS, colores_v

    def dibujar(self):
        self._volcar()
        super(Particulas, self).dibujar()

    # -- presets ----------------------------------------------------------------

    @classmethod
    def fuego(cls, pilas, **kw):
        """Llamas naranja→rojo que suben."""
        kw.setdefault('cantidad', 150)
        kw.setdefault('vida', 1.2)
        kw.setdefault('velocidad', 2.5)
        kw.setdefault('dispersion', 0.5)
        kw.setdefault('gravedad', -1.0)
        kw.setdefault('color', pilas.colores.naranja)
        kw.setdefault('color_final', pilas.colores.rojo)
        kw.setdefault('tamano', 6.0)
        return cls(pilas, **kw)

    @classmethod
    def humo(cls, pilas, **kw):
        """Humo gris que sube despacio y se disipa."""
        kw.setdefault('cantidad', 120)
        kw.setdefault('vida', 3.0)
        kw.setdefault('velocidad', 1.2)
        kw.setdefault('dispersion', 0.4)
        kw.setdefault('gravedad', -0.5)
        kw.setdefault('color', pilas.colores.gris)
        kw.setdefault('color_final', (0.3, 0.3, 0.3))
        kw.setdefault('tamano', 9.0)
        return cls(pilas, **kw)

    @classmethod
    def lluvia(cls, pilas, **kw):
        """Gotas celestes que caen en un área (usar dispersion alta
        y direccion hacia abajo)."""
        kw.setdefault('cantidad', 400)
        kw.setdefault('vida', 1.5)
        kw.setdefault('velocidad', 12.0)
        kw.setdefault('direccion', (0, -1, 0))
        kw.setdefault('dispersion', 0.15)
        kw.setdefault('color', pilas.colores.celeste)
        kw.setdefault('tamano', 3.0)
        return cls(pilas, **kw)

    @classmethod
    def explosion(cls, pilas, **kw):
        """Estallido único en todas direcciones (ciclico=False)."""
        kw.setdefault('cantidad', 80)
        kw.setdefault('vida', 0.9)
        kw.setdefault('velocidad', 6.0)
        kw.setdefault('direccion', (0, 0, 0))
        kw.setdefault('dispersion', 1.0)
        kw.setdefault('gravedad', 4.0)
        kw.setdefault('color', pilas.colores.amarillo)
        kw.setdefault('color_final', pilas.colores.rojo)
        kw.setdefault('tamano', 7.0)
        kw.setdefault('ciclico', False)
        return cls(pilas, **kw)
