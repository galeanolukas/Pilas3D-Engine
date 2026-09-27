# -*- encoding: utf-8 -*-
"""Mini-juego de plataformas 3D (habilidad PisaPlataformas).

Un cubo salta de plataforma en plataforma hasta la cima. Demuestra:

- ``PisaPlataformas``: gravedad que aterriza sobre bloques (no solo
  en el piso) + salto con SPACE.
- ``MoverseConElTeclado`` para el movimiento en XZ.
- Cámara que sigue al jugador desde ``actualizar``.
- Monedas recolectables con ``Puntaje`` y ``Texto`` de HUD.

Controles: flechas o WASD para moverse, SPACE para saltar.
"""

import pilas3d
from pilas3d.actores.cubo import Cubo
from pilas3d.actores.esfera import Esfera

# Escalera de plataformas: (x, z, ancho, alto) — cada salto sube ~1.
PLATAFORMAS = [
    (0, 0, 6, 0.5),
    (6, 0, 3, 1.5),
    (10, -3, 3, 2.5),
    (10, -8, 3, 3.5),
    (5, -10, 3, 4.5),
    (0, -8, 3, 5.5),
    (-4, -5, 4, 6.5),          # plataforma final con la gema
]
ALTURA_SALTO_MAX = 1.2         # el salto alcanza ~1.5 de altura


class Moneda(Esfera):
    def __init__(self, pilas, **kw):
        super(Moneda, self).__init__(pilas, radio=0.35, **kw)
        self.color = pilas.colores.amarillo
        self.aprender(pilas.habilidades.GirarConstantemente,
                      velocidad=120)


class Jugador(Cubo):
    def __init__(self, pilas, monedas, puntaje, **kw):
        self.monedas = monedas
        self.puntaje = puntaje
        super(Jugador, self).__init__(pilas, **kw)
        self.color = pilas.colores.celeste
        self.aprender(pilas.habilidades.MoverseConElTeclado,
                      velocidad=6)
        self.aprender(pilas.habilidades.PisaPlataformas,
                      gravedad=25, salto=9)

    def actualizar(self):
        for moneda in self.monedas:
            if moneda.esta_en_escena() and self.colisiona_con(moneda):
                moneda.eliminar()
                self.monedas.remove(moneda)
                self.puntaje.aumentar()

        # Si cae del mundo, reaparece arriba de la primera plataforma.
        if self.y < -5:
            self.posicion = (0, 4, 0)
            self.habilidades.PisaPlataformas.vel_y = 0

        # La cámara lo sigue en perspectiva de tres cuartos.
        camara = self.pilas.escena_actual().camara
        camara.posicion = (self.x + 6, self.y + 10, self.z + 16)
        camara.objetivo = self.posicion


pilas = pilas3d.iniciar(ancho=800, alto=600,
                        titulo="pilas3d - plataformas")

pilas.actores.Cielo()
pilas.actores.Piso(tamano=60, divisiones=30)

plataformas = []
for i, (x, z, ancho, alto) in enumerate(PLATAFORMAS):
    p = pilas.actores.Pared(x=x, z=z, ancho=ancho, alto=alto,
                            profundidad=ancho)
    p.color = (pilas.colores.gris if i < len(PLATAFORMAS) - 1
               else pilas.colores.verde)   # la última, distinta
    plataformas.append(p)

# Monedas flotando sobre algunas plataformas + gema en la cima.
monedas = []
for i in (1, 2, 4, 5):
    x, z, ancho, alto = PLATAFORMAS[i]
    monedas.append(Moneda(pilas, x=x, y=alto + 1.2, z=z))

gema = pilas.actores.Esfera(x=-4, y=8.5, z=-5, radio=0.5)
gema.color = pilas.colores.violeta
gema.aprender(pilas.habilidades.GirarConstantemente, velocidad=90)

puntaje = pilas.actores.Puntaje(x=10, y=60, prefijo="Monedas: ")
pilas.actores.Texto("WASD/flechas: mover - SPACE: saltar", x=10, y=35,
                    tamano=13)

jugador = Jugador(pilas, monedas, puntaje, x=0, y=3, z=0)
pilas.actores.Sombra(jugador)

# Aviso de victoria cuando agarró la gema (está sobre la plataforma
# final): alcanza con tocarla.
def revisar_gema():
    if gema.esta_en_escena() and jugador.colisiona_con(gema):
        gema.eliminar()
        cartel = pilas.actores.Texto("¡LLEGASTE A LA CIMA!",
                                   x=280, y=300, tamano=32)
        cartel.color = pilas.colores.amarillo

pilas.tareas.siempre(0.1, revisar_gema)

pilas.ejecutar()
