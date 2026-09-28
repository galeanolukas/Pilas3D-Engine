# -*- encoding: utf-8 -*-
"""Globos de diálogo sobre los actores (sin IA).

Dos personajes conversan con bocadillos que los siguen:

    1  -> el robot dice algo (el globo se borra solo a los 4s)
    2  -> el mono dice algo (idem)
    3  -> el robot cuenta un texto LARGO: se reparte en varios
          globos que avanzan solos a ritmo de lectura
    ESC -> salir

    python3 ejemplos/globos.py
"""

import pilas3d

pilas = pilas3d.iniciar(titulo="pilas3d - globos de dialogo")
pilas.escena.fondo = pilas.colores.gris_oscuro
pilas.actores.Piso(tamano=20, divisiones=20)

robi = pilas.actores.Robot(x=-3)
mono = pilas.actores.Mono(x=3)

# cada actor lleva su globo enganchado: lo sigue solo
globo_robi = pilas.actores.Globo(robi, alto=2.4)
globo_mono = pilas.actores.Globo(mono, alto=2.0)

TEXTO_LARGO = (
    "Este es un texto largo de prueba. Cuando un globo tiene que "
    "mostrar muchas palabras, se reparte en varios bocadillos que "
    "van pasando de a uno, para no tapar toda la escena. Asi un "
    "personaje puede contar una historia completa sin problemas."
)


def al_pulsar(tecla):
    s = pilas.simbolos
    if tecla == s._1:
        globo_robi.decir('hola! soy un robot', duracion=4)
    elif tecla == s._2:
        globo_mono.decir('y yo un mono que habla', duracion=4)
    elif tecla == s._3:
        globo_robi.decir(TEXTO_LARGO)   # paginas a ritmo lectura


pilas.escena.cuando_pulsa_tecla = al_pulsar
pilas.ejecutar()
