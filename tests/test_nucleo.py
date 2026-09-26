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


def test_colisiona_en_plano_ignora_y():
    pilas = crear_pilas()
    a = pilas.actores.Esfera(radio=0.4, y=0.4)
    b = pilas.actores.Esfera(radio=0.4, y=2.0)
    b.x = 0.5
    # En 3D no colisionan (distancia > radios), en el plano XZ sí.
    assert not a.colisiona_con(b)
    assert a.colisiona_en_plano_con(b)


def test_esfera_radio_de_colision_independiente():
    pilas = crear_pilas()
    e = pilas.actores.Esfera(radio=0.7, radio_de_colision=0.45)
    assert e.radio == 0.7
    assert e.radio_de_colision == 0.45
    # sin argumento, el radio de colisión sigue siendo el visual
    e2 = pilas.actores.Esfera(radio=0.7)
    assert e2.radio_de_colision == 0.7


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


def test_depurador_modos():
    pilas = crear_pilas()
    pilas.depurador.definir_modos(
        fps=True, radios_de_colision=True, puntos_de_control=True)
    assert pilas.depurador.activo()
    assert pilas._fps_visible
    pilas.depurador.definir_modos(
        fps=False, radios_de_colision=False, puntos_de_control=False)
    assert not pilas.depurador.activo()
    assert not pilas._fps_visible


def test_pared_dimensiones_y_piso():
    pilas = crear_pilas()
    pared = pilas.actores.Pared(ancho=4, alto=3, profundidad=0.3)
    assert pared.y == 1.5  # se apoya sobre el piso
    import math
    assert abs(pared.radio_de_colision -
               math.sqrt(16 + 9 + 0.09) / 2) < 0.01


# -- camara orbital y mouse --------------------------------------------------

def test_camara_orbital_calcula_posicion_inicial():
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara  # (0, 5, 12), objetivo origen
    camara.usar_control_orbital()          # sin ventana: no registra handlers
    assert abs(camara._orbital_distancia - 13.0) < 0.01
    assert abs(camara._orbital_pitch - 22.62) < 0.1
    assert abs(camara._orbital_yaw) < 0.01


def test_camara_orbital_drag_mueve_posicion():
    from pyglet.window import mouse
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara
    camara.usar_control_orbital()
    camara._on_mouse_drag(0, 0, 100, 0, mouse.LEFT, 0)
    assert abs(camara._orbital_yaw - 40) < 0.01
    assert camara.x != 0 or camara.z != 12


def test_camara_orbital_scroll_acerca():
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara
    camara.usar_control_orbital()
    d0 = camara._orbital_distancia
    camara._on_mouse_scroll(0, 0, 0, 1)
    assert camara._orbital_distancia < d0


def test_control_nulo_mouse():
    pilas = crear_pilas()
    assert pilas.control.mouse_x == 0
    assert pilas.control.boton_izquierdo is False


# -- colisiones con obstáculos ------------------------------------------------

def test_pared_es_obstaculo():
    pilas = crear_pilas()
    pared = pilas.actores.Pared(z=-5, ancho=4, profundidad=0.3)
    assert pared in pilas.escena_actual().obstaculos
    caja = pared.obtener_caja()
    assert caja == (-2.0, 2.0, -5.15, -4.85)


def test_pared_rotada_intercambia_dimensiones():
    pilas = crear_pilas()
    pared = pilas.actores.Pared(z=-5, ancho=4, profundidad=0.3)
    pared.rotacion_y = 90
    min_x, max_x, min_z, max_z = pared.obtener_caja()
    assert abs((max_x - min_x) - 0.3) < 0.01   # ahora es angosta en x
    assert abs((max_z - min_z) - 4.0) < 0.01   # y ancha en z


def test_resolver_circulo_empuja_fuera():
    from pilas3d import colisiones
    cajas = [(-2.0, 2.0, -5.0, -4.0)]
    # El círculo penetra la caja por abajo (z = -4.8 > min_z)
    x, z = colisiones.resolver_circulo_en_cajas(0, -4.8, 0.5, cajas)
    assert z <= -4.5 + 1e-6  # quedó fuera: dist >= radio del borde


def test_resolver_circulo_libre_no_mueve():
    from pilas3d import colisiones
    x, z = colisiones.resolver_circulo_en_cajas(0, 0, 0.5, [])
    assert (x, z) == (0, 0)


# -- rayo de cámara -------------------------------------------------------------

def test_disparar_rayo_acierta_al_centro():
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara  # mira al origen
    enemigo = pilas.actores.Esfera(radio=1.0)  # en el origen
    lejos = pilas.actores.Esfera(x=50, y=50, radio=1.0)
    assert camara.disparar_rayo([enemigo, lejos]) is enemigo


def test_disparar_rayo_falla_fuera_de_alcance():
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara
    enemigo = pilas.actores.Esfera(radio=0.5)
    assert camara.disparar_rayo([enemigo], alcance=1.0) is None


def test_primera_persona_posiciona_camara():
    pilas = crear_pilas()
    jugador = pilas.actores.Esfera(radio=0.4, y=0.4)
    jugador.aprender(pilas.habilidades.CaminarEnPrimeraPersona,
                     velocidad=6, altura=1.6)
    pilas.escena_actual().actualizar(1 / 60.0)
    camara = pilas.escena_actual().camara
    assert abs(camara.x - 0) < 0.01
    assert abs(camara.y - 2.0) < 0.01
    assert abs(camara.z - 0) < 0.01
    # objetivo a 1 unidad de distancia en la dirección de vista (-Z)
    assert abs(camara.objetivo[2] - (-1.0)) < 0.01


# -- mapa desde texto y texturas ------------------------------------------------

def test_mapa_desde_texto_crea_actores():
    pilas = crear_pilas()
    matriz = [
        "###",
        "#.#",
        "###",
    ]
    mapa = pilas.actores.Mapa(
        matriz,
        {'#': lambda p, x, z: p.actores.Pared(x=x, z=z, ancho=1)},
    )
    assert mapa.filas == 3 and mapa.columnas == 3
    assert len(mapa.creados) == 8          # 8 '#', el '.' queda vacío
    assert len(pilas.escena_actual().obstaculos) == 8
    assert mapa.celda(1, 1) == '.'


def test_mapa_acepta_string_multilinea():
    pilas = crear_pilas()
    posiciones = []
    mapa = pilas.actores.Mapa(
        "##\n#.",
        {'#': lambda p, x, z: posiciones.append((x, z))},
        tamano_celda=2.0,
    )
    assert len(posiciones) == 3
    # esquina superior-izquierda (fila 0, col 0) en -x/-z del centro
    assert (-1.0, -1.0) in posiciones


def test_mapa_simbolo_desconocido_se_ignora():
    pilas = crear_pilas()
    mapa = pilas.actores.Mapa("X#", {'#': lambda p, x, z: 'p'})
    assert mapa.creados == ['p']


def test_actor_imagen():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    assert cubo.imagen is None
    cubo.imagen = pilas3d.obtener_ruta('data/caja.png')
    assert cubo.imagen.endswith('caja.png')
    assert cubo._textura is None  # carga diferida hasta el primer dibujar


def test_obtener_ruta():
    ruta = pilas3d.obtener_ruta('data/pasto.png')
    assert ruta.endswith('/pilas3d/data/pasto.png')
    import os
    assert os.path.exists(ruta)


# -- sonidos y música ----------------------------------------------------------

def test_sonidos_cargar():
    pilas = crear_pilas()
    sonido = pilas.sonidos.cargar('tick.wav')
    assert sonido.ruta.endswith('tick.wav')
    # reproducir/detener no fallan con o sin placa de audio
    sonido.reproducir()
    sonido.reproducir(repetir=True)
    sonido.pausar()
    sonido.continuar()
    sonido.detener()


def test_sonidos_deshabilitar():
    from pilas3d.sonidos import Sonido, SonidoDeshabilitado
    pilas = crear_pilas()
    pilas.sonidos.deshabilitar()
    try:
        sonido = pilas.sonidos.cargar('tick.wav')
        assert isinstance(sonido, SonidoDeshabilitado)
        sonido.reproducir()
        sonido.detener_gradualmente(0.1)
    finally:
        pilas.sonidos.habilitar()
    assert Sonido.deshabilitado is False


def test_sonidos_ruta_inexistente():
    pilas = crear_pilas()
    try:
        pilas.sonidos.cargar('no_existe.wav')
        assert False, "debió lanzar IOError"
    except IOError:
        pass


def test_musica_cargar():
    pilas = crear_pilas()
    musica = pilas.musica.cargar('tick.wav')
    musica.reproducir()
    musica.volumen = 0.5
    musica.pausar()
    musica.continuar()
    musica.detener()
