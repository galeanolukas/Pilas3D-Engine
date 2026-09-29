# -*- encoding: utf-8 -*-
"""Juego completo: 'El templo de las antorchas'.

Recolectá las 6 monedas del templo y salí por el portal violeta.
Los espectros patrullan sus sectores y te persiguen si te ven; si te
tocan, te lastiman. La zona verde cura. Sobrevivilos.

    flechas / WASD : moverse        ESPACIO : saltar
    click          : disparar       F5 / F9 : guardar / cargar
"""

import pilas3d
from pilas3d.simbolos import F5, F9

pilas = pilas3d.iniciar()

# -- atmósfera: noche iluminada a antorchas --------------------------------
pilas.luces.direccional.ambiente = 0.1
pilas.luces.direccional.color = pilas.colores.azul
pilas.actores.Cielo()
pilas.actores.Piso()

LIMITE = 10
for i in range(-LIMITE, LIMITE + 1, 4):
    for x, z in [(-LIMITE, i), (LIMITE, i), (i, -LIMITE), (i, LIMITE)]:
        pilas.actores.Pared(x=x, z=z, ancho=4, alto=3)

for x, z in [(-LIMITE + 1, -LIMITE + 1), (LIMITE - 1, -LIMITE + 1),
             (-LIMITE + 1, LIMITE - 1), (LIMITE - 1, LIMITE - 1)]:
    a = pilas.actores.Lampara(x=x, y=3.5, z=z,
                              color=pilas.colores.naranja, alcance=8)
    a.aprender(pilas.habilidades.Parpadear, intensidad=0.3, velocidad=8)

# -- jugador ----------------------------------------------------------------
jugador = pilas.actores.Robot()
jugador.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)
jugador.aprender(pilas.habilidades.PisaPlataformas, salto=8)
jugador.aprender(pilas.habilidades.Vida, vida=100)
pilas.camara.seguir_a(jugador, modo='tercera')
pilas.actores.Barra(de=jugador, x=10, y=40)
puntaje = pilas.actores.Puntaje(x=10, y=10, prefijo='monedas: ')

# -- enemigos: patrullan, persiguen, lastiman -------------------------------
espectros = []
for casa in [(-6, -6), (6, -6), (0, 6)]:
    e = pilas.actores.Bot('Espectro', x=casa[0], z=casa[1], casa=casa,
                          objetivo=jugador, radio_vision=6,
                          velocidad=2.2)
    e.aprender(pilas.habilidades.Vida, vida=60)
    espectros.append(e)

def al_morir_espectro(esp):
    pilas.sonidos.cargar('explosion.wav').reproducir()
    pilas.camara.temblor(0.5, 0.4)
    esp.eliminar()

def al_tocar_jugador(esp):
    jugador.recibir_dano(10)
    pilas.sonidos.cargar('grito.wav').reproducir()
    pilas.camara.temblor(0.3, 0.25)
    jugador.decir('¡au!', duracion=1)

for e in espectros:
    e.al_morir = lambda esp=e: al_morir_espectro(esp)
    pilas.colisiones.cuando_colisionan(
        jugador, e, lambda esp=e: al_tocar_jugador(esp), cada=0.6)

jugador.aprender(
    pilas.habilidades.Disparar, con_click=True,
    objetivos=espectros,
    cuando_impacta=lambda proy, esp: esp.recibir_dano(30))

# -- monedas ----------------------------------------------------------------
monedas = []
for x, z in [(-7, 0), (7, 0), (0, -7), (4, 4), (-4, -8), (8, 8)]:
    m = pilas.actores.Esfera(x=x, y=0.5, z=z, radio=0.35)
    m.color = pilas.colores.amarillo
    m.sin_luz = True                    # brillan en la oscuridad
    monedas.append(m)

def al_agarrar(moneda):
    puntaje.aumentar(1)
    pilas.sonidos.cargar('tick.wav').reproducir()
    moneda.eliminar()
    if puntaje.valor >= 6:
        jugador.decir('¡el portal está abierto!', duracion=3)

for m in monedas:
    pilas.colisiones.cuando_colisionan(
        jugador, m, lambda m2=m: al_agarrar(m2))

# -- zonas ------------------------------------------------------------------
cura = pilas.actores.Zona(x=0, z=0, radio=2, visible=True,
                        color=pilas.colores.verde)
cura.cuando_entra(jugador, lambda: (jugador.curar(30),
                                    jugador.decir('me curé', duracion=1)))

portal = pilas.actores.Zona(x=0, z=-9, radio=1.5, visible=True,
                            color=pilas.colores.violeta)

def al_portal():
    if puntaje.valor >= 6:
        pilas.actores.Texto('¡GANASTE!', x=250, y=300, tamano=48)
        jugador.decir('escapé del templo')
    else:
        jugador.decir('faltan monedas', duracion=2)
portal.cuando_entra(jugador, al_portal)

# -- guardar / cargar --------------------------------------------------------
def al_pulsar(simbolo):
    if simbolo == F5:
        pilas.guardar_partida('templo.json',
                              datos={'monedas': puntaje.valor})
        jugador.decir('partida guardada', duracion=1)
    elif simbolo == F9:
        datos = pilas.cargar_partida('templo.json', limpiar=False)
        puntaje.valor = datos.get('monedas', 0)
        puntaje._armar()
        jugador.decir('partida cargada', duracion=1)

pilas.escena_actual().cuando_pulsa_tecla = al_pulsar

pilas.actores.Texto('flechas: moverse · ESPACIO: saltar · '
                    'click: disparar · F5/F9: guardar/cargar',
                    x=10, y=70)

pilas.ejecutar()
