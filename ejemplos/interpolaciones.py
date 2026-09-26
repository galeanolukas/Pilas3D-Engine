# -*- encoding: utf-8 -*-
"""Interpolaciones: animar propiedades con la sintaxis de pilas.

- actor.x = [3]                 -> lineal, 1 segundo
- actor.y = ([0, 3, 0], 2)      -> (valores, duración)
- actor.escala = ReboteFinal(2) -> con easing
- pilas.interpolar(actor, 'x', 5, duracion=2)
"""

import pilas3d

pilas = pilas3d.iniciar(ancho=800, alto=600, titulo="interpolaciones")
pilas.fps.ver()
pilas.actores.Piso()
pilas.actores.Texto("Cada actor usa una interpolación distinta",
                    x=10, y=10)

interp = pilas.interpolaciones

# Lineal: velocidad constante (equivale a `a.x = [6]` con 1 segundo)
a = pilas.actores.Cubo(x=-6, y=0.5)
a.color = pilas.colores.celeste
a.x = interp.Lineal([6], duracion=4)

# ReboteFinal: rebota al llegar
b = pilas.actores.Cubo(x=-2, y=0.5)
b.color = pilas.colores.rojo
b.y = interp.ReboteFinal([3], duracion=2)

# ElasticoInicial: resorte al arrancar
c = pilas.actores.Esfera(x=2, y=0.5, radio=0.5)
c.color = pilas.colores.verde
c.escala = interp.ElasticoFinal([2.5], duracion=3)

# Varios valores seguidos + pilas.interpolar con demora
d = pilas.actores.Esfera(x=6, y=0.5, radio=0.5)
d.color = pilas.colores.amarillo
d.z = ([0, 4, -4, 0], 4)
pilas.interpolar(d, 'rotacion', 360, duracion=4, demora=1)

pilas.ejecutar()
