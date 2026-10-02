# -*- encoding: utf-8 -*-
"""Una lámpara alumbra TODO: el escenario y los personajes.

Escena nocturna con una lámpara en el centro. Caminá al robot con
las flechas: cuando se acerca a la luz se ilumina él, el piso y las
paredes a la vez — la LuzPuntual no distingue "personaje" de
"escenario", ilumina cualquier cosa que esté a su alcance.

flechas: caminar - L: prender/apagar - E/Q: más o menos alcance
M: mover la lámpara al robot - ESC: salir
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - lámpara: ilumina todo")

# Casi sin luz ambiental para que se note qué alcanza la lámpara.
pilas.luces.direccional.ambiente = 0.07
pilas.actores.Cielo()                      # noche estrellada
pilas.actores.Piso()

# Algo de escenario para ver la luz caer sobre distintas cosas.
for x, z in [(-4, -4), (4, -4), (-4, 4), (4, 4)]:
    pilas.actores.Pared(x=x, z=z, ancho=0.6, alto=2.2)
caja = pilas.actores.Cubo(x=-2, z=-2)
caja.escala = 0.6

# La lámpara: foco + luz puntual que lo acompaña.
lampara = pilas.actores.Lampara(x=0, y=3, z=0,
                                color=pilas.colores.naranja,
                                alcance=8)

# El personaje: se ilumina igual que el piso cuando entra al alcance.
jugador = pilas.actores.Robot(x=-6, z=6)
jugador.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)
pilas.camara.seguir_a(jugador, modo='tercera')

texto = pilas.actores.Texto(
    'flechas: caminar - L: prender/apagar - E/Q: alcance - '
    'M: traer lámpara', x=10, y=10)


def al_pulsar(tecla):
    if tecla == pilas.simbolos.l:
        lampara.encendida = not lampara.encendida
    elif tecla == pilas.simbolos.m:
        # la lámpara es un actor común: se mueve y la luz lo sigue
        lampara.x, lampara.z = jugador.x, jugador.z
    elif tecla == pilas.simbolos.e:
        lampara.alcance = min(20, lampara.alcance + 1)
    elif tecla == pilas.simbolos.q:
        lampara.alcance = max(2, lampara.alcance - 1)


pilas.escena.cuando_pulsa_tecla = al_pulsar

pilas.ejecutar()
