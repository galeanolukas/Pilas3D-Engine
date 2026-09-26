# -*- encoding: utf-8 -*-
"""Tests del núcleo de pilas3d (sin ventana ni contexto OpenGL)."""

import pilas3d
from pilas3d import colores


def crear_pilas():
    return pilas3d.iniciar(sin_ventana=True)


def test_iniciar_crea_escena_normal():
    pilas = crear_pilas()
    assert pilas.escena_actual() is not None
    assert pilas.ventana is None
    assert pilas.control.izquierda is False


def test_actor_se_agrega_a_la_escena():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo(x=1, y=2, z=3)
    assert cubo in pilas.escena_actual().actores
    assert (cubo.x, cubo.y, cubo.z) == (1, 2, 3)


def test_actor_eliminar():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.eliminar()
    assert cubo not in pilas.escena_actual().actores


def test_transformaciones_afectan_la_matriz():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    m0 = tuple(cubo.matriz_modelo())
    cubo.rotacion_y = 90
    cubo.escala = 2
    m1 = tuple(cubo.matriz_modelo())
    assert m0 != m1


def test_posicion_en_matriz_modelo():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo(x=5, y=-2, z=7)
    m = cubo.matriz_modelo()
    # En Mat4 de pyglet (column-major) la traslación está en m[12:15]
    assert (m[12], m[13], m[14]) == (5.0, -2.0, 7.0)


def test_rotacion_alias_es_rotacion_y():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.rotacion = 45
    assert cubo.rotacion_y == 45
    assert cubo.rotacion == 45


def test_camara_valores_iniciales():
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara
    assert camara.posicion == (0, 5, 12)
    vista = camara.matriz_vista()
    assert len(tuple(vista)) == 16


def test_actores_disponibles():
    pilas = crear_pilas()
    pilas.actores.Esfera(radio=2)
    pilas.actores.Piso()
    pilas.actores.Ejes()
    assert len(pilas.escena_actual().actores) == 3


def test_actualizar_de_la_escena_llama_a_actores():
    pilas = crear_pilas()
    llamadas = []
    cubo = pilas.actores.Cubo()
    cubo.actualizar = lambda: llamadas.append(1)
    pilas.escena_actual().actualizar(1 / 60.0)
    assert llamadas == [1]


def test_colores_normalizar():
    assert colores.normalizar((255, 0, 0)) == (1.0, 0.0, 0.0)
