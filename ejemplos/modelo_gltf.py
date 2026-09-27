# -*- encoding: utf-8 -*-
"""Ejemplo: modelo glTF con animación esquelética.

El lobo (Khronos Wolf, Blender 2.82a) tiene 5 animaciones de esqueleto
que se muestrean por CPU y se escriben en el vertex list cada frame.

Teclas 1-5 cambian la animación; ESPACIO pausa/continúa.
"""

import pilas3d
from pyglet.window import key

pilas = pilas3d.iniciar(titulo="pilas3d - glTF esqueletico")
pilas.escena.fondo = pilas.colores.gris_oscuro

pilas.actores.Piso(tamano=30, divisiones=30)
pilas.actores.Ejes()

lobo = pilas.actores.ModeloGLTF(
    'modelos/33-gltf-wolf/gltf/Wolf-Blender-2.82a.glb', y=0)
lobo.escala = 1.5
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
    if key._1 <= tecla <= key._5:
        i = tecla - key._1
        if i < len(nombres):
            lobo.animar(nombres[i], ciclica=True)
    elif tecla == key.SPACE:
        lobo.velocidad = 0.0 if lobo.velocidad else 1.0
    mostrar_nombre()


pilas.escena.cuando_pulsa_tecla = al_pulsar
mostrar_nombre()

camara = pilas.escena.camara
camara.posicion = (0, 2.5, 7)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital()

pilas.ejecutar()
