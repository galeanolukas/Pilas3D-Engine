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


def test_colisiona_con():
    pilas = crear_pilas()
    a = pilas.actores.Cubo()          # radio ~0.87
    b = pilas.actores.Esfera(radio=0.5)
    b.x = 5.0                         # lejos: no colisiona
    assert not a.colisiona_con(b)
    b.x = 1.0                         # 1.0 < 0.87 + 0.5 -> colisiona
    assert a.colisiona_con(b)


def test_distancia_con_es_3d():
    pilas = crear_pilas()
    a = pilas.actores.Cubo()
    b = pilas.actores.Cubo(x=3, z=4)  # distancia en el plano XZ
    assert a.distancia_con(b) == 5.0


def test_puntaje_sin_ventana():
    pilas = crear_pilas()
    puntaje = pilas.actores.Puntaje(prefijo="Puntos: ")
    assert puntaje.es_overlay
    assert puntaje.texto == "Puntos: 0"
    puntaje.aumentar()
    puntaje.aumentar(5)
    assert puntaje.valor == 6
    assert puntaje.texto == "Puntos: 6"


# -- tareas ------------------------------------------------------------------

def test_tarea_una_vez():
    pilas = crear_pilas()
    llamadas = []
    pilas.tareas.una_vez(0.5, lambda: llamadas.append(1))
    escena = pilas.escena_actual()
    escena.actualizar(0.3)
    escena.actualizar(0.3)   # contador llega a 0.6 > 0.5
    escena.actualizar(0.3)
    assert llamadas == [1]
    assert pilas.tareas.obtener_cantidad_de_tareas_planificadas() == 0


def test_tarea_siempre_se_repite():
    pilas = crear_pilas()
    llamadas = []
    pilas.tareas.siempre(0.5, lambda: llamadas.append(1))
    escena = pilas.escena_actual()
    for _ in range(6):
        escena.actualizar(0.5)  # ejecuta a los 0.5, 1.0, 1.5...
    assert len(llamadas) >= 3


def test_tarea_condicional_se_detiene():
    pilas = crear_pilas()
    llamadas = []

    def crecer():
        llamadas.append(1)
        return len(llamadas) < 3

    pilas.tareas.condicional(0.1, crecer)
    escena = pilas.escena_actual()
    for _ in range(10):
        escena.actualizar(0.1)
    assert len(llamadas) == 3


def test_tarea_eliminar():
    pilas = crear_pilas()
    llamadas = []
    tarea = pilas.tareas.siempre(0.1, lambda: llamadas.append(1))
    tarea.eliminar()
    pilas.escena_actual().actualizar(1.0)
    assert llamadas == []


# -- habilidades --------------------------------------------------------------

def test_aprender_y_tiene_habilidad():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.aprender(pilas.habilidades.GirarConstantemente, velocidad=90)
    assert cubo.tiene_habilidad(pilas.habilidades.GirarConstantemente)
    assert cubo.habilidades.GirarConstantemente is not None


def test_habilidad_girar_actualiza_rotacion():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.aprender(pilas.habilidades.GirarConstantemente, velocidad=90)
    pilas.escena_actual().actualizar(1.0)
    assert 89 < cubo.rotacion_y < 91


def test_habilidad_rebotar_aplica_gravedad():
    pilas = crear_pilas()
    bola = pilas.actores.Esfera(y=5)
    bola.aprender(pilas.habilidades.RebotarComoPelota,
                  velocidad_inicial=0)
    escena = pilas.escena_actual()
    for _ in range(360):  # 6 segundos a 60 fps: cae, rebota y se asienta
        escena.actualizar(1 / 60.0)
    assert abs(bola.y - bola.radio_de_colision) < 0.01


def test_eliminar_habilidad():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.aprender(pilas.habilidades.GirarConstantemente)
    cubo.eliminar_habilidad(pilas.habilidades.GirarConstantemente)
    pilas.escena_actual().actualizar(1.0)
    assert cubo.rotacion_y == 0


def test_aprender_por_nombre():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.aprender('GirarConstantemente')
    assert cubo.tiene_habilidad(pilas.habilidades.GirarConstantemente)


# -- debug -------------------------------------------------------------------

def test_fps_ver_y_ocultar():
    pilas = crear_pilas()
    pilas.fps.ver()
    assert pilas._fps_visible
    assert pilas.fps.visible
    pilas.fps.ocultar()
    assert not pilas._fps_visible


def test_mostrar_y_ocultar_ejes():
    pilas = crear_pilas()
    pilas.mostrar_ejes()
    assert pilas._actor_ejes in pilas.escena_actual().actores
    pilas.ocultar_ejes()
    assert pilas._actor_ejes is None
    assert all(
        type(a).__name__ != 'Ejes'
        for a in pilas.escena_actual().actores
    )
