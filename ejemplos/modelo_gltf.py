# -*- encoding: utf-8 -*-
"""Ejemplo: modelo glTF con animación esquelética.

El lobo (Khronos Wolf, Blender 2.82a) tiene 5 animaciones de esqueleto
que se muestrean por CPU y se escriben en el vertex list cada frame.

Teclas 1-5 cambian la animación; ESPACIO pausa/continúa.
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - glTF esqueletico")

pilas.actores.Cielo('dia')                     # celeste con nubes
pilas.escena.fondo = pilas.colores.celeste

piso = pilas.actores.Piso(tamano=30, divisiones=30)
piso.color = pilas.colores.verde            # grilla clara tipo pasto
pilas.actores.Ejes()
pilas.luces.direccional.ambiente = 0.6         # luz de día suave

lobo = pilas.actores.ModeloGLTF(
    'modelos/personajes/wolf/Wolf-Blender-2.82a.glb', y=0)
lobo.escala = 2.5
lobo.animar('02_walk_Armature_0', ciclica=True)

# la lista de clips que trae el archivo:
nombres = lobo.animaciones()
print("animaciones del modelo:", nombres)

info = pilas.actores.Texto(
    "1-5: cambiar animacion - ESPACIO: pausa - mouse: orbitar",
    x=10, y=440, tamano=13)
actual = pilas.actores.Texto("", x=10, y=415, tamano=16)
actual.color = pilas.colores.amarillo


def mostrar_nombre():
    actual.texto = "animacion: " + (lobo.animacion or "(ninguna)")


def al_pulsar(tecla):
    if pilas.simbolos._1 <= tecla <= pilas.simbolos._5:
        i = tecla - pilas.simbolos._1
        if i < len(nombres):
            lobo.animar(nombres[i], ciclica=True)
    elif tecla == pilas.simbolos.ESPACIO:
        lobo.velocidad = 0.0 if lobo.velocidad else 1.0
    mostrar_nombre()


pilas.escena.cuando_pulsa_tecla = al_pulsar
mostrar_nombre()

camara = pilas.escena.camara
camara.posicion = (0, 2.2, 4.5)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital()

pilas.ejecutar()
