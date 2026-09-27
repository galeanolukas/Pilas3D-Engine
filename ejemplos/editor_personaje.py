# -*- encoding: utf-8 -*-
"""Editor de personajes articulados (v1).

Carga un modelo glTF riggeado y permite posar sus huesos:

- Flechas ARRIBA/ABAJO: elegir hueso
- X / Y / Z: elegir eje de rotación
- IZQUIERDA/DERECHA: rotar el hueso ±10°
- G: guardar pose en 'pose.json'   C: cargarla   R: reiniciar
- Botón derecho + drag: orbitar la cámara
- La esfera roja marca la articulación seleccionada
"""

import os

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - editor de personaje")

MODELO = 'modelos/33-gltf-wolf/gltf/Wolf-Blender-2.82a.glb'
POSE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'pose.json')

pilas.escena.fondo = pilas.colores.gris_oscuro   # fondo de estudio
piso = pilas.actores.Piso(tamano=30, divisiones=30)
piso.color = pilas.colores.gris
pilas.luces.direccional.ambiente = 0.6

modelo = pilas.actores.ModeloGLTF(MODELO, escala=2.0)
huesos = modelo.huesos()
if not huesos:
    raise SystemExit("el modelo no tiene esqueleto (skin)")

marcador = pilas.actores.Esfera(radio=0.08)
marcador.color = pilas.colores.rojo

sel = [0]            # índice dentro de la lista huesos
eje = ['y']

lista = pilas.actores.Texto("", x=10, y=170, tamano=13)
info = pilas.actores.Texto("", x=10, y=420, tamano=15)
info.color = pilas.colores.amarillo
pilas.actores.Texto(
    "arriba/abajo: hueso - X/Y/Z: eje - <-/->: rotar - "
    "G guardar - C cargar - R reset",
    x=10, y=10)


def refrescar_ui():
    i, nombre = huesos[sel[0]]
    info.texto = "hueso: %s  eje: %s" % (nombre, eje[0])
    # ventana de 14 huesos alrededor del seleccionado
    ini = max(0, min(sel[0] - 7, len(huesos) - 14))
    lineas = []
    for k, (j, n) in enumerate(huesos[ini:ini + 14]):
        marca = '>> ' if ini + k == sel[0] else '   '
        lineas.append('%s%s' % (marca, n))
    lista.texto = '\n'.join(lineas)


class MarcadorHueso(object):
    """Actualiza la esfera a la posición del hueso elegido."""

    def actualizar(self):
        marcador.posicion = modelo.posicion_hueso(huesos[sel[0]][0])


marco = MarcadorHueso()
pilas.tareas.siempre(0, marco.actualizar)


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s.ARRIBA:
        sel[0] = (sel[0] - 1) % len(huesos)
    elif tecla == s.ABAJO:
        sel[0] = (sel[0] + 1) % len(huesos)
    elif tecla == s.x:
        eje[0] = 'x'
    elif tecla == s.y:
        eje[0] = 'y'
    elif tecla == s.z:
        eje[0] = 'z'
    elif tecla in (s.IZQUIERDA, s.DERECHA):
        grados = -10 if tecla == s.IZQUIERDA else 10
        modelo.detener()
        modelo.rotar_hueso(huesos[sel[0]][0], eje[0], grados)
        modelo.refrescar_pose()
    elif tecla == s.g:
        modelo.guardar_pose(POSE)
        info.texto = "pose guardada en pose.json"
        return
    elif tecla == s.c:
        if os.path.exists(POSE):
            modelo.detener()
            modelo.cargar_pose(POSE)
    elif tecla == s.r:
        modelo.reiniciar_pose()
    refrescar_ui()


pilas.escena.cuando_pulsa_tecla = al_pulsar
refrescar_ui()

camara = pilas.escena.camara
camara.posicion = (0, 2.5, 6)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

pilas.ejecutar()
