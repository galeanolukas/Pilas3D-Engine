# -*- encoding: utf-8 -*-
"""Mini-juego completo: recolectar monedas.

Movés la esfera con flechas o WASD (habilidad MoverseConElTeclado);
las monedas rebotan (RebotarComoPelota) y giran (GirarConstantemente),
y aparecen nuevas cada 5 segundos con pilas.tareas.siempre.
"""

import random

import pilas3d
from pilas3d.actores.esfera import Esfera

AREA = 9
MAX_MONEDAS = 12


class Moneda(Esfera):
    def __init__(self, pilas, **kw):
        super(Moneda, self).__init__(pilas, radio=0.4, **kw)
        self.color = pilas.colores.amarillo
        self.aprender(pilas.habilidades.GirarConstantemente, velocidad=120)
        self.aprender(pilas.habilidades.RebotarComoPelota,
                      velocidad_inicial=6)
        self.reposicionar()

    def reposicionar(self):
        self.posicion = (
            random.uniform(-AREA, AREA),
            random.uniform(0.4, 3),
            random.uniform(-AREA, AREA),
        )


class Jugador(Esfera):
    def __init__(self, pilas, monedas, puntaje, **kw):
        super(Jugador, self).__init__(pilas, radio=0.7, **kw)
        self.color = pilas.colores.celeste
        self.monedas = monedas
        self.puntaje = puntaje
        self.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=8)

    def actualizar(self):
        for moneda in self.monedas:
            if self.colisiona_con(moneda):
                moneda.reposicionar()
                self.puntaje.aumentar()

        camara = self.pilas.escena_actual().camara
        camara.posicion = (self.x, 10, self.z + 12)
        camara.objetivo = (self.x, 0, self.z)


pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - recolectar")

pilas.actores.Piso(tamano=2 * AREA + 4, divisiones=2 * AREA + 4)

# El origen del overlay está abajo a la izquierda; usar posiciones
# bajas hace que el HUD no dependa del tamaño final de la ventana.
puntaje = pilas.actores.Puntaje(x=10, y=60, prefijo="Puntos: ")
pilas.actores.Texto(
    "Recolectá las monedas - flechas/WASD", x=10, y=30
)

monedas = [Moneda(pilas) for _ in range(6)]
Jugador(pilas, monedas, puntaje, y=0.7)


def crear_moneda():
    """Aparece una moneda nueva cada 5 segundos (hasta MAX_MONEDAS)."""
    if len(monedas) < MAX_MONEDAS:
        monedas.append(Moneda(pilas))


pilas.tareas.siempre(5, crear_moneda)
pilas.ejecutar()
