import pilas3d
from pilas3d.actores.actor import Actor
from pilas3d import mallas

pilas = pilas3d.iniciar()

# ============ CONFIGURACION ============
TITULO = "{{TITULO}}"
PUNTAJE_META = {{PUNTAJE_META}}

# ============ ACTORES ============


class Jugador(Actor):
    def _generar_geometria(self):
        return {{GEOMETRIA_JUGADOR}}

    def iniciar(self):
        self.aprender(pilas.habilidades.MoverseConElTeclado)
        self.radio_de_colision = 0.8

    def actualizar(self):
        {{LOGICA_JUGADOR}}


class Enemigo(Actor):
    def _generar_geometria(self):
        return {{GEOMETRIA_ENEMIGO}}

    def actualizar(self):
        {{LOGICA_ENEMIGO}}


# ============ ESCENA ============


def iniciar_juego():
    pilas.actores.Piso()
    pilas.actores.Ejes()
    jugador = Jugador(pilas, x=0, y=1, z=0)
    {{SPAWN_ENEMIGOS}}
    return jugador


jugador = iniciar_juego()

if __name__ == "__main__":
    pilas.ejecutar()
