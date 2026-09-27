# -*- encoding: utf-8 -*-
"""Modelo animado por secuencia de .obj (técnica estilo Quake II/MD2).

Como no tenemos un modelo animado real a mano, el ejemplo genera una
secuencia propia: una "pelota" que se aplasta y estira (squash &
stretch) exportada a archivos .obj temporales, y luego la reproduce.

WASD orbita la cámara (drag con mouse, rueda zoom).
"""

import math
import os
import tempfile

import pilas3d


def generar_cuadros(directorio, cantidad=12):
    """Escribe `cantidad` .obj de un cubo aplastándose/estirándose."""
    rutas = []
    for i in range(cantidad):
        # squash & stretch: achata al tocar el piso, se estira en el aire
        fase = math.sin(math.pi * i / cantidad)      # 0 → 1 → 0
        sy = 0.6 + 0.7 * fase                        # escala vertical
        sxz = 1.3 - 0.35 * fase                      # compensa volumen
        y = 0.2 + 1.8 * fase                         # altura del salto
        verts = []
        for vx, vy, vz in [(-1, -1, -1), (1, -1, -1), (1, 1, -1),
                           (-1, 1, -1), (-1, -1, 1), (1, -1, 1),
                           (1, 1, 1), (-1, 1, 1)]:
            verts.append("v %f %f %f" % (vx * sxz, vy * sy + y, vz * sxz))
        caras = ["f 1 4 3 2", "f 5 6 7 8", "f 1 2 6 5",
                 "f 2 3 7 6", "f 4 8 7 3", "f 5 8 4 1"]
        ruta = os.path.join(directorio, "salto_%02d.obj" % i)
        with open(ruta, "w") as f:
            f.write("\n".join(verts + caras) + "\n")
        rutas.append(ruta)
    return rutas


pilas = pilas3d.iniciar(titulo="pilas3d - modelo animado")
pilas.actores.Piso()
pilas.actores.Cielo()

directorio = tempfile.mkdtemp(prefix="pilas3d_anim_")
cuadros = generar_cuadros(directorio)
print("cuadros generados en", directorio)

# izquierda: stop-motion (cambia de cuadro entero)
bola1 = pilas.actores.ModeloAnimado(cuadros, velocidad=12, x=-3,
                                    suavizar=False)
bola1.color = pilas.colores.rojo
pilas.actores.Sombra(bola1)

# derecha: suavizado (interpola vértices entre cuadros, como MD2)
bola2 = pilas.actores.ModeloAnimado(cuadros, velocidad=12, x=3,
                                    suavizar=True)
bola2.color = pilas.colores.verde
pilas.actores.Sombra(bola2)

pilas.actores.Texto("izquierda: por cuadros   derecha: suavizada",
                    x=10, y=10)
pilas.escena_actual().camara.usar_control_orbital()
pilas.ejecutar()
