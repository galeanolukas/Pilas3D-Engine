# -*- encoding: utf-8 -*-
"""Galería de personajes predefinidos.

Como los actores de pilas original (Mono, Aceituna...) pero en 3D y
cada uno dibujado con un método distinto:

- Robot: cuboides combinados con color por vértice (mallas.combinar)
- Humanoide: bipedo estilo muñeco
- Mono: esferas + cuboides
- Arania: primitivas, sin recursos externos
- Espectro: esferas alambradas (GL_LINES)

Todos heredan de Personaje → Actor, así que pueden aprender
habilidades (acá giran con GirarConstantemente).
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - personajes")

pilas.actores.Piso(tamano=30, divisiones=30)

personajes = [
    ('Robot', pilas.actores.Robot),
    ('Humanoide', pilas.actores.Humanoide),
    ('Mono', pilas.actores.Mono),
    ('Arania', pilas.actores.Arania),
    ('Espectro', pilas.actores.Espectro),
]

x = -6
for nombre, fabrica in personajes:
    p = fabrica(x=x, y=1.2)
    p.aprender(pilas.habilidades.GirarConstantemente, velocidad=45)
    x += 3

cam = pilas.escena.camara
cam.posicion = (0, 3, 10)
cam.punto_de_mira = (0, 0.8, 0)

pilas.actores.Texto(
    "Robot - Humanoide - Mono - Arania - Espectro   "
    "(cada uno dibujado distinto)", x=10, y=10)

pilas.ejecutar()
