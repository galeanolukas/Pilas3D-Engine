# -*- encoding: utf-8 -*-
"""Editor de personajes articulados (v1).

Carga un modelo glTF riggeado y permite posar sus huesos:

- Flechas ARRIBA/ABAJO: elegir hueso
- X / Y / Z: elegir eje de rotación
- IZQUIERDA/DERECHA: rotar el hueso ±10°
- N: siguiente modelo (recorre los .glb de modelos/)
- G: guardar pose en 'pose-<modelo>.json'   C: cargarla   R: reiniciar
- Botón derecho + drag: orbitar la cámara
- La esfera roja marca la articulación seleccionada
"""

import glob
import os

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - editor de personaje")

pilas.escena.fondo = pilas.colores.gris_oscuro   # fondo de estudio
piso = pilas.actores.Piso(tamano=30, divisiones=30)
piso.color = pilas.colores.gris
pilas.luces.direccional.ambiente = 0.6

# modelos .glb disponibles en el directorio modelos/ (local, no se
# publica): wolf, fox, cesium-man... los que hayas bajado.
DIR_EJ = os.path.dirname(os.path.abspath(__file__))
MODELOS = sorted(
    glob.glob(os.path.join(DIR_EJ, '..', 'modelos', '**', '*.glb'),
              recursive=True) +
    glob.glob(os.path.join(DIR_EJ, '..', 'modelos', '*.glb')))
if not MODELOS:
    raise SystemExit("no hay .glb en modelos/ - bajá alguno de "
                     "KhronosGroup/glTF-Sample-Assets")


def ruta_pose(ruta_modelo):
    base = os.path.splitext(os.path.basename(ruta_modelo))[0]
    return os.path.join(DIR_EJ, 'pose-%s.json' % base)


def autoescala(modelo, objetivo=1.8):
    """Normaliza el modelo a ~``objetivo`` unidades de alto
    (los .glb vienen en unidades arbitrarias: el Fox está en cm)."""
    pos = modelo._pos
    if not pos:
        return 1.0
    ys = pos[1::3]
    alto = max(ys) - min(ys) or 1.0
    return objetivo / alto


estado = {'modelo': None, 'huesos': [], 'sel': 0, 'eje': 'y',
          'indice': 0}

marcador = pilas.actores.Esfera(radio=0.08)
marcador.color = pilas.colores.rojo

lista = pilas.actores.Texto("", x=10, y=170, tamano=13)
info = pilas.actores.Texto("", x=10, y=420, tamano=15)
info.color = pilas.colores.amarillo
pilas.actores.Texto(
    "N: modelo - arriba/abajo: hueso - X/Y/Z: eje - <-/->: rotar - "
    "G guardar - C cargar - R reset",
    x=10, y=10)


def cargar_modelo(i):
    """Instancia el modelo i de MODELOS, recrea lista de huesos."""
    if estado['modelo'] is not None:
        estado['modelo'].eliminar()
    ruta = MODELOS[i]
    modelo = pilas.actores.ModeloGLTF(ruta)
    modelo.escala = autoescala(modelo)
    estado['modelo'] = modelo
    estado['huesos'] = modelo.huesos()
    estado['sel'] = 0
    refrescar_ui()


def refrescar_ui():
    huesos, sel = estado['huesos'], estado['sel']
    if not huesos:
        info.texto = "este modelo no tiene esqueleto"
        lista.texto = ""
        return
    i, nombre = huesos[sel]
    base = os.path.basename(MODELOS[estado['indice']])
    info.texto = "%s  |  hueso: %s  eje: %s" % (base, nombre,
                                               estado['eje'])
    ini = max(0, min(sel - 7, len(huesos) - 14))
    lineas = []
    for k, (j, n) in enumerate(huesos[ini:ini + 14]):
        marca = '>> ' if ini + k == sel else '   '
        lineas.append('%s%s' % (marca, n))
    lista.texto = '\n'.join(lineas)


class MarcadorHueso(object):
    """Actualiza la esfera a la posición del hueso elegido."""

    def actualizar(self):
        if estado['huesos']:
            marcador.posicion = estado['modelo'].posicion_hueso(
                estado['huesos'][estado['sel']][0])


pilas.tareas.siempre(0, MarcadorHueso().actualizar)


def al_pulsar(tecla):
    s = pilas.simbolos
    modelo = estado['modelo']
    huesos = estado['huesos']
    if tecla == s.n:
        estado['indice'] = (estado['indice'] + 1) % len(MODELOS)
        cargar_modelo(estado['indice'])
        return
    if not huesos:
        refrescar_ui()
        return
    if tecla == s.ARRIBA:
        estado['sel'] = (estado['sel'] - 1) % len(huesos)
    elif tecla == s.ABAJO:
        estado['sel'] = (estado['sel'] + 1) % len(huesos)
    elif tecla == s.x:
        estado['eje'] = 'x'
    elif tecla == s.y:
        estado['eje'] = 'y'
    elif tecla == s.z:
        estado['eje'] = 'z'
    elif tecla in (s.IZQUIERDA, s.DERECHA):
        grados = -10 if tecla == s.IZQUIERDA else 10
        modelo.detener()
        modelo.rotar_hueso(huesos[estado['sel']][0], estado['eje'],
                           grados)
        modelo.refrescar_pose()
    elif tecla == s.g:
        pose = ruta_pose(MODELOS[estado['indice']])
        modelo.guardar_pose(pose)
        info.texto = "pose guardada: " + os.path.basename(pose)
        return
    elif tecla == s.c:
        pose = ruta_pose(MODELOS[estado['indice']])
        if os.path.exists(pose):
            modelo.detener()
            modelo.cargar_pose(pose)
    elif tecla == s.r:
        modelo.reiniciar_pose()
    refrescar_ui()


pilas.escena.cuando_pulsa_tecla = al_pulsar
cargar_modelo(0)

camara = pilas.escena.camara
camara.posicion = (0, 2.2, 4.5)
camara.objetivo = (0, 1, 0)
camara.usar_control_orbital(boton=pilas.simbolos.BOTON_DERECHO)

pilas.ejecutar()
