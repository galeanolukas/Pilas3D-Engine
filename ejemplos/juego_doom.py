# -*- encoding: utf-8 -*-
"""Mini-FPS estilo Doom con mapa ASCII y texturas.

- El laberinto se define como texto: '#' pared, 'E' enemigo, 'J' jugador
- WASD/flechas: caminar (las paredes bloquean)
- Mouse: mirar alrededor
- Click izquierdo: disparar (rayo desde la cámara)
- Si un enemigo te toca: volvés al inicio y perdés una vida
"""

import pilas3d
from pilas3d.actores.esfera import Esfera

# 13 filas x 14 columnas; cada celda mide 2 unidades.
MAPA = """
##############
#............#
#.E..........#
#....####....#
#....#...E...#
#....#.......#
#.E..#....E..#
#............#
#....####....#
#........E...#
#.....J......#
##############
"""

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - mini doom")

TEX_PARED = pilas3d.obtener_ruta('data/caja.png')
TEX_PISO = pilas3d.obtener_ruta('data/pasto.png')

puntaje = pilas.actores.Puntaje(x=10, y=60, prefijo="Puntos: ")
vidas = pilas.actores.Puntaje(x=200, y=60, prefijo="Vidas: ")
vidas.valor = 3
vidas.texto = "Vidas: 3"
pilas.actores.Texto("WASD moverse - mouse mirar - click disparar",
                    x=10, y=30)


class Enemigo(Esfera):
    """Esfera roja que persigue al jugador por el plano XZ."""

    def __init__(self, pilas, jugador=None, **kw):
        super(Enemigo, self).__init__(pilas, radio=0.7, **kw)
        self.color = pilas.colores.rojo
        self.jugador = jugador

    def actualizar(self):
        j = self.jugador
        dx, dz = j.x - self.x, j.z - self.z
        d = (dx ** 2 + dz ** 2) ** 0.5
        if d > 0.1:
            v = 2.5 * self.pilas.dt
            self.x += dx / d * v
            self.z += dz / d * v
        self.rotacion_y += 60 * self.pilas.dt

        # Si toca al jugador: una vida menos y vuelta al inicio.
        if self.colisiona_con(j):
            j.posicion = jugador_inicio
            vidas.valor -= 1
            vidas.texto = "Vidas: %d" % vidas.valor
            if vidas.valor <= 0:
                pilas.actores.Texto("PERDISTE!", x=320, y=200, tamano=40)
                self.pilas.tareas.una_vez(2, pilas.terminar)


class Jugador(Esfera):
    """El cuerpo del jugador (se ve al mirar hacia abajo)."""

    def __init__(self, pilas, enemigos, **kw):
        super(Jugador, self).__init__(pilas, radio=0.4, **kw)
        self.color = pilas.colores.celeste
        self.enemigos = enemigos
        self.espera_disparo = 0.0
        self.aprender(pilas.habilidades.CaminarEnPrimeraPersona,
                      velocidad=6, altura=1.6)

    def actualizar(self):
        self.espera_disparo -= self.pilas.dt
        if self.pilas.control.boton_izquierdo and \
                self.espera_disparo <= 0:
            self.espera_disparo = 0.3
            blanco = self.pilas.escena_actual().camara.disparar_rayo(
                self.enemigos, alcance=40)
            if blanco:
                blanco.eliminar()
                self.enemigos.remove(blanco)
                puntaje.aumentar()
                if not self.enemigos:
                    pilas.actores.Texto("GANASTE!", x=340, y=200,
                                        tamano=40)


# -- construcción del mapa desde texto ---------------------------------------

enemigos = []
spawn = {}
jugador_inicio = (0, 0.4, 0)


def hacer_pared(p, x, z):
    pared = p.actores.Pared(x=x, z=z, ancho=2, alto=3, profundidad=2)
    pared.imagen = TEX_PARED
    return pared


def hacer_enemigo(p, x, z):
    enemigo = Enemigo(p, x=x, y=0.7, z=z)
    enemigos.append(enemigo)
    return enemigo


def marcar_jugador(p, x, z):
    spawn['pos'] = (x, 0.4, z)


mapa = pilas.actores.Mapa(MAPA, {
    '#': hacer_pared,
    'E': hacer_enemigo,
    'J': marcar_jugador,
})

piso = pilas.actores.Plano(ancho=30, profundidad=30)
piso.imagen = TEX_PISO

jugador = Jugador(pilas, enemigos)
jugador_inicio = spawn['pos']
jugador.posicion = jugador_inicio
for enemigo in enemigos:
    enemigo.jugador = jugador

pilas.ejecutar()
