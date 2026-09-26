# -*- encoding: utf-8 -*-
"""Cámara orbital con el mouse + paredes + depurador.

- Arrastrar con botón izquierdo: orbitar alrededor del objetivo
- Rueda del mouse: zoom
- Se muestran los radios de colisión y puntos de control (depurador)
"""

import pilas3d

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="pilas3d - orbital")

pilas.actores.Piso(tamano=20, divisiones=20)

cubo = pilas.actores.Cubo(y=0.5)
cubo.color = pilas.colores.celeste

# Un "cuarto" con tres paredes
pilas.actores.Pared(z=-6, ancho=12)
pilas.actores.Pared(x=-6, ancho=12, profundidad=0.3).rotacion_y = 90
pilas.actores.Pared(x=6, ancho=12, profundidad=0.3).rotacion_y = 90

pilas.actores.Texto(
    "Botón izq + arrastrar: orbitar - rueda: zoom", x=10, y=30)

pilas.depurador.definir_modos(
    fps=True, radios_de_colision=True, puntos_de_control=True)

camara = pilas.escena_actual().camara
camara.posicion = (8, 8, 14)
camara.usar_control_orbital()

pilas.ejecutar()
