# -*- encoding: utf-8 -*-
"""Colores predefinidos, como tuplas (rojo, verde, azul) en rango 0-255."""

blanco = (255, 255, 255)
negro = (0, 0, 0)
gris = (128, 128, 128)
gris_oscuro = (50, 50, 50)
gris_claro = (200, 200, 200)

rojo = (255, 0, 0)
rojo_oscuro = (150, 0, 0)
verde = (0, 255, 0)
verde_oscuro = (0, 150, 0)
azul = (0, 0, 255)
azul_oscuro = (0, 0, 150)

amarillo = (255, 255, 0)
celeste = (0, 255, 255)
naranja = (255, 128, 0)
rosa = (255, 0, 255)
violeta = (128, 0, 255)
marron = (150, 75, 0)


def normalizar(color):
    """Convierte una tupla 0-255 a (r, g, b) en rango 0.0-1.0."""
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
