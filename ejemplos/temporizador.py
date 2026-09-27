# -*- encoding: utf-8 -*-
"""Ejemplo: temporizadores — cuenta regresiva, ciclos y cronómetro.

Un cubo "bomba" explota a los 5 segundos (Temporizador visible),
un temporizador cíclico e invisible suelta esferas cada 2 segundos,
y un cronómetro cuenta el tiempo total en pantalla.
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - temporizador")
pilas.escena.fondo = pilas.colores.gris_oscuro

pilas.actores.Piso(tamano=40, divisiones=40)
pilas.actores.Ejes()

bomba = pilas.actores.Cubo(y=1.2)
bomba.escala = 1.5
bomba.color = pilas.colores.rojo

cartel = pilas.actores.Texto("la bomba explota en...", x=10, y=430)
aviso = pilas.actores.Texto("", x=10, y=460, tamano=24)
aviso.color = pilas.colores.rojo

bolas = []


def explotar():
    """Al llegar a cero: explosión de partículas y la bomba se va."""
    pilas.actores.Particulas.explosion(pilas, x=bomba.x, y=bomba.y, z=bomba.z)
    bomba.eliminar()
    cartel.texto = ""
    aviso.texto = "¡BOOM! (T para reiniciar)"


def a_la_mitad():
    aviso.texto = "¡se acaba!"

# cuenta regresiva visible: muestra el número en pantalla
reloj = pilas.actores.Temporizador(duracion=5, x=10, y=400, tamano=26,
                                   cuando_termina=explotar, color=pilas.colores.blanco)
reloj.avisar(2.5, a_la_mitad)      # aviso intermedio
reloj.iniciar()


def soltar_bola():
    bola = pilas.actores.Esfera(radio=0.4, x=6, y=8, z=0)
    bola.color = pilas.colores.naranja
    bolas.append(bola)
    if len(bolas) > 5:             # no acumular infinitas
        bolas.pop(0).eliminar()

# temporizador cíclico e invisible: suelta una bola cada 2 segundos
pilas.actores.Temporizador(duracion=2, ciclico=True, visible=False,
                           cuando_termina=soltar_bola).iniciar()

# cronómetro ascendente (sin duración): cuenta el tiempo total
pilas.actores.Temporizador(x=10, y=370, formato=lambda s: "t: %.0fs" % s,
                           color=pilas.colores.gris_claro).iniciar()


def explotar_cubo(cubo):
    pilas.actores.Particulas.explosion(pilas, x=cubo.x, y=cubo.y, z=cubo.z)
    cubo.eliminar()
    cartel.texto = ""
    aviso.texto = "¡BOOM! (T para reiniciar)"


def reiniciar():
    """Crea otra bomba con su propio temporizador."""
    if bomba in pilas.escena.actores:
        return
    nueva = pilas.actores.Cubo(y=1.2)
    nueva.escala = 1.5
    nueva.color = pilas.colores.rojo
    aviso.texto = ""
    cartel.texto = "la bomba explota en..."
    r = pilas.actores.Temporizador(duracion=5, x=10, y=400, tamano=26,
                                   cuando_termina=lambda: explotar_cubo(nueva),
                                   color=pilas.colores.blanco)
    r.avisar(2.5, a_la_mitad)
    r.iniciar()


def al_pulsar(tecla):
    if tecla == pilas.simbolos.t:
        reiniciar()

pilas.escena.cuando_pulsa_tecla = al_pulsar

camara = pilas.escena.camara
camara.posicion = (0, 6, 14)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital()

pilas.ejecutar()
