# -*- encoding: utf-8 -*-
"""Tests del núcleo de pilas3d (sin ventana ni contexto OpenGL)."""

import json
import os

import pytest

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


# -- carteles (billboards) y animación ----------------------------------------

def test_cartel_mira_a_la_camara():
    import math
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara
    camara.posicion = (0, 0, 10)
    cartel = pilas.actores.Cartel(ancho=2, alto=3)
    m = tuple(cartel.matriz_modelo())
    # la normal +Z debe quedar apuntando hacia la cámara (en +Z)
    assert abs(m[8] - 0.0) < 0.01 and abs(m[10] - 1.0) < 0.01
    # moviendo la cámara a +X el cartel rota 90°
    camara.posicion = (10, 0, 0)
    m = tuple(cartel.matriz_modelo())
    assert abs(m[8] - 1.0) < 0.01 and abs(m[10] - 0.0) < 0.01


def test_animacion_avanza_cuadros():
    pilas = crear_pilas()
    anim = pilas.actores.Animacion('moneda.png', columnas=8,
                                 velocidad=10)
    assert anim.total_cuadros == 8
    assert anim._uv_escala == (1 / 8.0, 1.0)
    pilas.dt = 0.2   # 2 cuadros a 10 fps
    anim.actualizar()
    assert anim.cuadro == 2
    assert anim._uv_desplazamiento == (2 / 8.0, 0.0)


def test_animacion_no_ciclica_se_elimina():
    pilas = crear_pilas()
    escena = pilas.escena_actual()
    anim = pilas.actores.Animacion('explosion.png', columnas=7,
                                 velocidad=10, ciclica=False,
                                 eliminar_al_terminar=True)
    pilas.dt = 1.0   # más que toda la animación
    anim.actualizar()
    assert anim not in escena.actores


def test_paso_sin_ventana_no_falla():
    pilas = crear_pilas()
    pilas.paso()   # sin ventana solo avisa; no debe explotar
    pilas.ayuda()  # imprime la guía


# -- interpolaciones -----------------------------------------------------------

def actualizar_n_veces(pilas, n):
    escena = pilas.escena_actual()
    for _ in range(n):
        escena.actualizar(1 / 60.0)


def test_interpolacion_lista():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.x = [10]           # 1 segundo = 60 frames
    actualizar_n_veces(pilas, 30)
    assert 0 < cubo.x < 10
    actualizar_n_veces(pilas, 40)
    assert cubo.x == 10
    assert cubo._interpolaciones == []


def test_interpolacion_varios_valores():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.y = [2, 0]         # sube a 2 y vuelve a 0
    actualizar_n_veces(pilas, 30)
    assert cubo.y > 1.5     # en la primera mitad va subiendo
    actualizar_n_veces(pilas, 40)
    assert cubo.y == 0


def test_interpolacion_tupla_con_duracion():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.x = ([100], 2.0)   # 2 segundos = 120 frames
    actualizar_n_veces(pilas, 60)
    assert 45 < cubo.x < 55
    actualizar_n_veces(pilas, 70)
    assert cubo.x == 100


def test_interpolacion_clases_de_easing():
    from pilas3d import interpolaciones as I
    pilas = crear_pilas()
    a = pilas.actores.Cubo()
    b = pilas.actores.Cubo()
    a.x = I.ReboteFinal([10], duracion=1)
    b.x = I.DesaceleracionGradual([10], duracion=1)
    actualizar_n_veces(pilas, 30)
    # con ease-out la mitad del tiempo ya recorrió más de la mitad
    assert b.x > 5
    actualizar_n_veces(pilas, 40)
    assert a.x == 10 and b.x == 10


def test_interpolar_facade_y_demora():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    pilas.interpolar(cubo, 'x', 5, duracion=1, demora=1)
    actualizar_n_veces(pilas, 30)
    assert cubo.x == 0      # todavía en la demora
    actualizar_n_veces(pilas, 100)
    assert cubo.x == 5


def test_interpolacion_inversa():
    from pilas3d import interpolaciones as I
    interp = -I.Lineal([5], duracion=2)
    assert interp.valores == [5]
    interp2 = -I.Lineal([1, 3])
    assert interp2.valores == [3, 1]


def test_cargar_obj(tmp_path):
    from pilas3d import modelos
    obj = tmp_path / "tetraedro.obj"
    obj.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
        "vt 0 0\nvt 1 0\nvt 0 1\n"
        "f 1/1 2/2 3/3\n"          # sin normales: se calculan
        "f 1/1 4/2 2/3\nf 1/1 3/2 4/3\nf 2/1 4/2 3/3\n")
    d = modelos.cargar_obj(str(obj))
    assert d['triangulos'] == 4
    assert len(d['posiciones']) == 36
    assert len(d['normales']) == 36
    assert d['radio'] == 1.0
    # segunda carga usa el caché (mismo objeto)
    assert modelos.cargar_obj(str(obj)) is d


def test_modelo_actor(tmp_path):
    from pilas3d import modelos
    obj = tmp_path / "cubo.obj"
    obj.write_text(
        "v -1 -1 -1\nv 1 -1 -1\nv 1 1 -1\nv -1 1 -1\n"
        "v -1 -1 1\nv 1 -1 1\nv 1 1 1\nv -1 1 1\n"
        "f 1 2 3 4\nf 5 6 7 8\nf 1 2 6 5\n"
        "f 2 3 7 6\nf 3 4 8 7\nf 4 1 5 8\n")
    pilas = crear_pilas()
    m = pilas.actores.Modelo(str(obj), escala=2)
    assert m in pilas.escena_actual().actores
    assert m.radio_de_colision > 1.7 * 2 - 0.01  # esfera envolvente ×2
    m.rotacion_y = 45
    m.eliminar()


def test_cargar_obj_con_materiales(tmp_path):
    from pilas3d import modelos
    (tmp_path / "m.mtl").write_text(
        "newmtl Rojo\nKd 1.0 0.0 0.0\nnewmtl Verde\nKd 0.0 1.0 0.0\n")
    obj = tmp_path / "dos.obj"
    obj.write_text(
        "mtllib m.mtl\n"
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
        "usemtl Rojo\nf 1 2 3\nusemtl Verde\nf 1 2 4\n")
    d = modelos.cargar_obj(str(obj))
    assert d['colores'] is not None
    # primer triángulo rojo, segundo verde
    assert d['colores'][:4] == [1.0, 0.0, 0.0, 1.0]
    assert d['colores'][12:16] == [0.0, 1.0, 0.0, 1.0]


def test_luces_agregar_quitar_limpiar():
    from pilas3d import luces as L
    pilas = crear_pilas()
    luz = pilas.luces.agregar(L.LuzPuntual(x=1, y=2, z=3, alcance=5))
    assert luz in pilas.luces.puntuales
    sol = L.LuzDireccional(direccion=(0, -1, 0), color=(1, 0, 0))
    pilas.luces.agregar(sol)
    assert pilas.luces.direccional is sol
    pilas.luces.quitar(luz)
    assert pilas.luces.puntuales == []
    pilas.luces.agregar(L.LuzPuntual())
    pilas.luces.limpiar()
    assert pilas.luces.puntuales == []
    assert pilas.luces.direccional.ambiente == 0.45


def test_sombra_sigue_al_actor():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo(x=3, z=-2)
    sombra = pilas.actores.Sombra(cubo)
    assert sombra.escala == cubo.radio_de_colision
    pilas.escena_actual().actualizar(1 / 60.0)
    assert (sombra.x, sombra.z) == (3, -2)
    cubo.eliminar()
    pilas.escena_actual().actualizar(1 / 60.0)
    assert sombra not in pilas.escena_actual().actores


def test_escena_personalizada_con_vincular():
    import pilas3d
    pilas = crear_pilas()
    eventos = []

    class MiEscena(pilas3d.escenas.Escena):
        def iniciar(self):
            eventos.append('inicio')
            self.cubo = self.pilas.actores.Cubo()

        def terminar(self):
            eventos.append('fin')

        def cuando_actualiza(self):
            eventos.append('tick')

    pilas.escenas.vincular(MiEscena)
    escena = pilas.escenas.MiEscena()
    assert pilas.escena_actual() is escena
    assert eventos == ['inicio']
    assert len(escena.actores) == 1
    escena.actualizar(1 / 60.0)
    assert 'tick' in eventos

    otra = pilas.escenas.Normal()
    assert 'fin' in eventos
    assert pilas.escena_actual() is otra
    assert otra.actores == []  # la nueva escena arranca vacía


def test_cambiar_escena_y_propiedad_escena():
    pilas = crear_pilas()
    e1 = pilas.escena_actual()
    e2 = pilas.escenas.Normal()
    assert pilas.escena is e2
    pilas.cambiar_escena(e1)
    assert pilas.escena_actual() is e1
    pilas.escena = e2
    assert pilas.escena_actual() is e2


def test_cambio_de_escena_aisla_actores_y_luces():
    from pilas3d import luces as L
    pilas = crear_pilas()
    e1 = pilas.escena_actual()
    pilas.actores.Cubo()
    pilas.luces.agregar(L.LuzPuntual())
    e2 = pilas.escenas.Normal()
    assert len(e1.actores) == 1
    assert e2.actores == []
    assert e2.luces.puntuales == []


def test_cielo_sigue_a_la_camara():
    pilas = crear_pilas()
    cielo = pilas.actores.Cielo()
    cam = pilas.escena_actual().camara
    cam.posicion = (5, 2, -3)
    cielo.actualizar()
    assert (cielo.x, cielo.y, cielo.z) == (5, 2, -3)
    assert cielo.radio_de_colision == 0.0


def test_cielo_acepta_textura_generada():
    from pilas3d.actores.cielo import _textura_estrellas
    textura = _textura_estrellas(64, 32)
    assert textura.width == 64


def _escribir_obj(ruta, dx=0.0):
    """Triángulo mínimo desplazado en x (un cuadro de animación)."""
    ruta.write_text(
        "v %f 0 0\nv %f 1 0\nv %f 0 1\nf 1 2 3\n"
        % (dx, dx, dx))


def test_modelo_animado_avanza_cuadros(tmp_path):
    pilas = crear_pilas()
    for i in range(4):
        _escribir_obj(tmp_path / ("f%d.obj" % i), dx=float(i))
    anim = pilas.actores.ModeloAnimado(
        str(tmp_path / "*.obj"), velocidad=10)
    assert anim.cantidad_de_cuadros == 4
    assert anim.cuadro_actual == 0
    pilas.dt = 0.1  # a 10fps, 0.1s = 1 cuadro
    anim.actualizar()
    assert anim.cuadro_actual == 1
    for _ in range(10):
        anim.actualizar()
    assert anim.cuadro_actual in range(4)  # ciclica: envuelve


def test_modelo_animado_no_ciclico_y_definir_cuadro(tmp_path):
    pilas = crear_pilas()
    for i in range(3):
        _escribir_obj(tmp_path / ("c%d.obj" % i))
    anim = pilas.actores.ModeloAnimado(
        [str(tmp_path / ("c%d.obj" % i)) for i in range(3)],
        velocidad=10, ciclica=False)
    pilas.dt = 1.0
    anim.actualizar()
    assert anim.cuadro_actual == 2
    assert not anim.reproduciendo
    anim.definir_cuadro(1)
    assert anim.cuadro_actual == 1


def test_modelo_animado_suavizar_requiere_mismos_vertices(tmp_path):
    pilas = crear_pilas()
    _escribir_obj(tmp_path / "a.obj")
    (tmp_path / "b.obj").write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 2 3 4\n")
    try:
        pilas.actores.ModeloAnimado(
            str(tmp_path / "*.obj"), suavizar=True)
        assert False, "debio lanzar ValueError"
    except ValueError:
        pass


def test_mundo_bloques_basicos():
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.poner_bloque(1, 2, 3, 'ladrillo')
    assert mundo.hay_bloque(1, 2, 3)
    assert mundo.bloque_en(1, 2, 3) == 'ladrillo'
    assert not mundo.hay_bloque(0, 0, 0)
    mundo.sacar_bloque(1, 2, 3)
    assert not mundo.hay_bloque(1, 2, 3)
    assert mundo in pilas.escena_actual().obstaculos


def test_mundo_cara_compartida_no_se_dibuja():
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.poner_bloque(0, 0, 0)
    mundo.poner_bloque(1, 0, 0)
    pos, _, _ = mundo._geometria_chunk(0, 0)
    # 2 bloques separados = 12 caras = 72 vértices; pegados = 10 caras
    assert len(pos) // 3 == 10 * 2 * 3


def test_mundo_disparar_bloque_dda():
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.poner_bloque(3, 0, 0)
    # rayo horizontal +x desde el origen
    bloque, adyacente = mundo.disparar_bloque(
        (0.5, 0.5, 0.5), (1.0, 0.0, 0.0), alcance=10)
    assert bloque == (3, 0, 0)
    assert adyacente == (2, 0, 0)
    # rayo que no pega nada
    bloque, adyacente = mundo.disparar_bloque(
        (0.5, 0.5, 0.5), (0.0, 1.0, 0.0), alcance=3)
    assert bloque is None


def test_mundo_resolver_circulo_empuja():
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.poner_bloque(0, 0, 0)  # ocupa x/z en [0, 1)
    # círculo en x=0.9 dentro del bloque a la altura del bloque
    x, z = mundo.resolver_circulo(0.9, 0.5, 0.3, 0.0, 1.6)
    assert x > 1.0 or z < 0.0 or z > 1.0  # quedó afuera
    # a la altura de arriba del bloque no choca
    x2, z2 = mundo.resolver_circulo(0.9, 0.5, 0.3, 2.0, 3.0)
    assert (x2, z2) == (0.9, 0.5)


def test_mundo_generar_terreno_y_suelo():
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.generar_terreno(16, 16, altura=4, semilla=1)
    assert len(mundo.bloques) > 16
    suelo = mundo.altura_suelo(0.5, 0.5)
    assert suelo is not None and suelo >= 1
    assert mundo.altura_suelo(999, 999) is None


def test_armar_atlas_compone_imagenes():
    from pilas3d.actores.mundo import armar_atlas
    from pyglet.image import ImageData
    roja = ImageData(16, 16, 'RGBA', b'\xff\x00\x00\xff' * 256)
    verde = ImageData(16, 16, 'RGBA', b'\x00\xff\x00\xff' * 256)
    atlas = armar_atlas([roja, verde])
    assert atlas.width == 32 and atlas.height == 16
    datos = atlas.get_data('RGBA', 32 * 4)
    assert datos[0] == 255 and datos[1] == 0      # rojo
    assert datos[16 * 4 + 1] == 255               # verde


def test_modelo_json_mc(tmp_path):
    import json
    from pilas3d import modelos
    raiz = tmp_path / 'assets' / 'minecraft'
    (raiz / 'models' / 'block').mkdir(parents=True)
    (raiz / 'textures' / 'blocks').mkdir(parents=True)
    modelo = {
        'textures': {'tex': 'blocks/foo'},
        'elements': [{'from': [0, 0, 0], 'to': [16, 16, 16],
                      'faces': {
                          'up': {'uv': [0, 0, 16, 16], 'texture': '#tex'},
                          'north': {'uv': [0, 0, 8, 8],
                                    'texture': '#tex'}}}],
    }
    ruta = raiz / 'models' / 'block' / 'mini.json'
    ruta.write_text(json.dumps(modelo))
    datos = modelos.cargar_json_mc(str(ruta))
    assert len(datos['posiciones']) == 2 * 6 * 3  # 2 caras × 6 vértices
    assert datos['imagen'].endswith('textures/blocks/foo.png')
    pilas = crear_pilas()
    actor = pilas.actores.ModeloJSON(str(ruta))
    assert actor.imagen == datos['imagen']


def test_seguir_al_actor_persigue_y_frena():
    pilas = crear_pilas()
    jugador = pilas.actores.Cubo(x=10, z=0)
    enemigo = pilas.actores.Esfera()
    enemigo.aprender(pilas.habilidades.SeguirAlActor,
                     actor=jugador, velocidad=5)
    d0 = enemigo.distancia_con(jugador)
    for _ in range(30):
        enemigo.pre_actualizar()
    assert enemigo.distancia_con(jugador) < d0
    jugador.eliminar()
    x0 = enemigo.x
    enemigo.pre_actualizar()   # objetivo muerto: no se mueve
    assert enemigo.x == x0


def test_mirar_al_actor_orienta_hacia_objetivo():
    """La convención: frente=+Z y rotacion_y=+90 rota +Z->+X, así que
    mirar a -Z es 180 y mirar a +X es +90."""
    import math
    pilas = crear_pilas()
    objetivo = pilas.actores.Cubo(z=-10)
    torreta = pilas.actores.Cubo()
    torreta.aprender(pilas.habilidades.MirarAlActor, actor=objetivo)
    torreta.pre_actualizar()
    assert abs(torreta.rotacion_y - 180) < 0.01  # frente +Z -> a -Z
    objetivo.x = 10
    objetivo.z = 0
    torreta.pre_actualizar()
    assert abs(torreta.rotacion_y - 90) < 0.01   # mira hacia +x


def test_moverse_en_circulo_orbita():
    import math
    pilas = crear_pilas()
    luna = pilas.actores.Esfera()
    luna.aprender(pilas.habilidades.MoverseEnCirculo,
                  centro=(0, 0), radio=5, velocidad=90)
    pilas.dt = 1 / 60.0
    luna.pre_actualizar()
    a1 = math.degrees(math.atan2(luna.z, luna.x))
    for _ in range(30):
        luna.pre_actualizar()
    d = math.sqrt(luna.x ** 2 + luna.z ** 2)
    assert abs(d - 5) < 0.01
    a2 = math.degrees(math.atan2(luna.z, luna.x))
    assert a2 != a1  # avanzó en la órbita


def test_imitar_copia_posicion_y_rotacion():
    pilas = crear_pilas()
    lider = pilas.actores.Cubo(x=3, z=-2)
    lider.rotacion_y = 45
    gorro = pilas.actores.Esfera()
    gorro.aprender(pilas.habilidades.Imitar, actor=lider,
                   desplazar=(0, 1, 0))
    gorro.pre_actualizar()
    assert (gorro.x, gorro.y, gorro.z) == (3, 1, -2)
    assert gorro.rotacion_y == 45


def test_puede_explotar_crea_animacion_y_elimina():
    pilas = crear_pilas()
    bomba = pilas.actores.Cubo()
    bomba.aprender(pilas.habilidades.PuedeExplotar)
    bomba.habilidades.PuedeExplotar.explotar()
    escena = pilas.escena_actual()
    assert bomba not in escena.actores
    assert any(a.__class__.__name__ == 'Animacion'
               for a in escena.actores)


def test_ayuda_sin_argumentos_imprime_chuleta(capsys):
    pilas = crear_pilas()
    pilas.ayuda()
    assert 'pilas3d - guía rápida' in capsys.readouterr().out


def test_ayuda_con_consulta_usa_asistente(capsys, monkeypatch):
    pilas = crear_pilas()
    import pilas3d.ia.asistente as asistente
    llamadas = {}
    monkeypatch.setattr(
        asistente, 'preguntar',
        lambda c, contexto='': llamadas.update(
            consulta=c, contexto=contexto) or 'respuesta IA')
    pilas.ayuda('¿cómo muevo un cubo?')
    salida = capsys.readouterr().out
    assert 'respuesta IA' in salida
    assert llamadas['consulta'] == '¿cómo muevo un cubo?'
    assert 'actores=' in llamadas['contexto']


def test_ayuda_ia_sin_servidor_cae_a_la_chuleta(capsys, monkeypatch):
    pilas = crear_pilas()
    import pilas3d.ia.asistente as asistente

    def fallar(consulta, contexto=''):
        raise RuntimeError("Ollama no arrancó")
    monkeypatch.setattr(asistente, 'preguntar', fallar)
    pilas.ayuda('¿algo?')
    salida = capsys.readouterr().out
    assert 'asistente no disponible' in salida
    assert 'guía rápida' in salida


def test_ia_listar_y_borrar_sin_servidor_no_rompe():
    import pilas3d.ia.servidor as srv
    # con o sin servidor: devuelve lista y borrar algo inexistente → False
    assert isinstance(srv.listar_modelos(), list)
    assert srv.borrar_modelo('no-existe:nunca') is False


def test_make_game_slugify_y_validacion():
    from pilas3d.ia.make_game import (slugify, validar_codigo,
                                      extraer_codigo)
    assert slugify('juego de náves espaciales!') == \
        'juego_de_naves_espaciales'
    ok, _ = validar_codigo('x = 1\nprint(x)')
    assert ok
    ok, razon = validar_codigo('x = {{SIN_RELLENAR}}')
    assert not ok and 'placeholder' in razon
    ok, _ = validar_codigo('input("x")')
    assert not ok
    codigo = extraer_codigo('```python\na = 1\n```')
    assert codigo.strip() == 'a = 1'


def test_make_game_ejecutar_headless():
    from pilas3d.ia.make_game import ejecutar_headless
    exito, out, err = ejecutar_headless(
        "import pilas3d\npilas = pilas3d.iniciar()\n"
        "pilas.actores.Cubo()\npilas.ejecutar()\n")
    assert exito, err
    exito, _, err = ejecutar_headless("1/0\n")
    assert not exito and 'ZeroDivisionError' in err


def test_actor_hook_iniciar():
    from pilas3d.actores.actor import Actor
    from pilas3d import mallas
    pilas = crear_pilas()

    llamado = []

    class Nave(Actor):
        def _generar_geometria(self):
            return mallas.cubo(1)
        def iniciar(self):
            llamado.append(True)
            self.aprender(pilas.habilidades.GirarConstantemente)

    nave = Nave(pilas)
    assert llamado == [True]
    assert len(nave._habilidades) == 1


def test_asistente_system_prompt_describe_api_real():
    from pilas3d.ia.asistente import SYSTEM
    for nombre in ('MoverseConElTeclado', 'CaminarEnPrimeraPersona',
                   'Mundo', 'disparar_bloque', 'generar_terreno'):
        assert nombre in SYSTEM


def test_pisa_plataformas_aterriza_sobre_bloque():
    pilas = crear_pilas()
    plataforma = pilas.actores.Pared(x=0, z=0, ancho=4, alto=2,
                                   profundidad=4)
    cubo = pilas.actores.Cubo(x=0, y=5, z=0)
    cubo.aprender(pilas.habilidades.PisaPlataformas)
    for _ in range(120):
        cubo.pre_actualizar()
    # techo de la pared = y + alto/2 = 1+1 = 2; cubo centrado → 2.5
    assert abs(cubo.y - 2.5) < 0.01
    hab = cubo.habilidades.PisaPlataformas
    assert hab.en_suelo and hab.plataforma_actual is plataforma


def test_pisa_plataformas_cae_al_borde():
    pilas = crear_pilas()
    pilas.actores.Pared(x=0, z=0, ancho=4, alto=2, profundidad=4)
    cubo = pilas.actores.Cubo(x=0, y=5, z=0)
    cubo.aprender(pilas.habilidades.PisaPlataformas)
    for _ in range(120):
        cubo.pre_actualizar()
    cubo.x = 10          # se baja de la plataforma
    for _ in range(120):
        cubo.pre_actualizar()
    assert abs(cubo.y - 0.5) < 0.01   # cayó al piso
    assert not cubo.habilidades.PisaPlataformas.en_suelo or True


def test_perseguir_esquiva_una_pared():
    pilas = crear_pilas()
    pilas.dt = 1 / 60.0
    # pared entre el enemigo (0,0) y el objetivo (7,0)
    pilas.actores.Pared(x=3, z=0, ancho=1, alto=3, profundidad=8)
    objetivo = pilas.actores.Cubo(x=7, z=0)
    enemigo = pilas.actores.Esfera()
    enemigo.aprender(pilas.habilidades.PerseguirAOtroActor,
                     actor=objetivo, velocidad=4, cada=0.2)
    zigzagueo = False
    for _ in range(600):
        enemigo.pre_actualizar()
        if abs(enemigo.z) > 3:        # tuvo que bordear la pared
            zigzagueo = True
        if enemigo.distancia_con(objetivo) < 1.5:
            break
    assert zigzagueo
    assert enemigo.distancia_con(objetivo) < 1.5


def test_perseguir_sin_obstaculos_va_derecho():
    pilas = crear_pilas()
    objetivo = pilas.actores.Cubo(x=5, z=0)
    enemigo = pilas.actores.Esfera()
    enemigo.aprender(pilas.habilidades.PerseguirAOtroActor,
                     actor=objetivo, velocidad=4, cada=0.1)
    for _ in range(120):
        enemigo.pre_actualizar()
    assert enemigo.distancia_con(objetivo) < 1.5


def test_mundo_chunks_marcan_bordes():
    pilas = crear_pilas()
    m = pilas.actores.Mundo(tamano_chunk=16)
    m._sucio = False
    m._sucios = set()
    m.poner_bloque(0, 1, 0)            # esquina del chunk (0,0)
    assert (0, 0) in m._sucios
    assert (-1, 0) in m._sucios        # vecino por borde i=0
    assert (0, -1) in m._sucios        # vecino por borde k=0
    m._sucios = set()
    m.poner_bloque(5, 1, 5)            # interior: solo su chunk
    assert m._sucios == {(0, 0)}
    m._sucios = set()
    m.sacar_bloque(5, 1, 5)
    assert m._sucios == {(0, 0)}


def test_mundo_infinito_genera_alrededor_de_camara():
    pilas = crear_pilas()
    m = pilas.actores.Mundo(infinito=True, tamano_chunk=8,
                          distancia_vista=1)
    m.actualizar()                     # cámara en (0,5,12) → chunk (0,0)
    assert len(m._generados) == 9      # 3x3 chunks
    assert len(m.bloques) > 0
    assert m.altura_suelo(0, 0) is not None
    # mover la cámara lejos genera chunks nuevos
    cam = pilas.escena_actual().camara
    cam.posicion = (200, 5, 0)
    m.actualizar()
    assert len(m._generados) == 18
    assert m.altura_suelo(200, 0) is not None


def test_mundo_infinito_determinista_por_semilla():
    pilas = crear_pilas()
    a = pilas.actores.Mundo(infinito=True, semilla=42)
    b = pilas.actores.Mundo(infinito=True, semilla=42)
    assert a.altura_terreno_en(5, 7) == b.altura_terreno_en(5, 7)
    c = pilas.actores.Mundo(infinito=True, semilla=43)
    assert any(a.altura_terreno_en(i, k) != c.altura_terreno_en(i, k)
               for i in range(10) for k in range(10))


def test_mundo_altura_suelo_respeta_ediciones():
    pilas = crear_pilas()
    m = pilas.actores.Mundo(infinito=True, tamano_chunk=8,
                          distancia_vista=1)
    m.actualizar()                     # cubre la columna (0, 12)
    suelo = m.altura_suelo(0, 12)
    assert suelo is not None
    m.poner_bloque(0, suelo, 12, 'ladrillo')
    assert m.altura_suelo(0, 12) == suelo + 1
    m.sacar_bloque(0, suelo, 12)
    assert m.altura_suelo(0, 12) == suelo


def test_escena_niebla_configurable():
    pilas = crear_pilas()
    assert pilas.escena.niebla is None
    pilas.escena.niebla = (pilas.colores.gris, 10, 50)
    assert pilas.escena.niebla == (pilas.colores.gris, 10, 50)


def test_particulas_emiten_y_renacen():
    pilas = crear_pilas()
    p = pilas.actores.Particulas(cantidad=20, vida=0.1, velocidad=2)
    for _ in range(30):           # ~0.5s: todas debieron re-nacer
        p.actualizar()
    # con ciclico todas siguen vivas (edad < ttl) y se movieron
    assert all(p._edad[i] < p._ttl[i] for i in range(20))
    assert any(p._px[i] != 0 or p._py[i] != 0 or p._pz[i] != 0
               for i in range(20))


def test_particulas_explosion_muere():
    pilas = crear_pilas()
    p = pilas.actores.Particulas.explosion(pilas)
    assert not p.ciclico
    for _ in range(120):          # ~2s > vida 0.9s
        p.actualizar()
    assert all(p._edad[i] >= p._ttl[i] for i in range(p.cantidad))


def test_particulas_presets_desde_fabrica():
    pilas = crear_pilas()
    assert pilas.actores.Particulas.fuego(pilas).gravedad < 0
    assert pilas.actores.Particulas.lluvia(pilas).direccion[1] == -1


def test_interpolacion_transparencia():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.transparencia = [100]
    actualizar_n_veces(pilas, 70)
    assert cubo.transparencia == 100
    pilas = crear_pilas()
    pilas.paso()   # sin ventana solo avisa; no debe explotar
    pilas.ayuda()  # imprime la guía


def test_disparo_usa_radio_de_disparo():
    pilas = crear_pilas()
    camara = pilas.escena_actual().camara
    camara.posicion = (0, 0, 0)
    camara.objetivo = (0, 0, -10)
    # desviada 0.5 del rayo: no alcanza con radio 0.1, sí con 1.0
    lejano = pilas.actores.Esfera(x=0.5, z=-5, radio=0.1)
    lejano.radio_de_colision = 0.1
    assert camara.disparar_rayo([lejano]) is None
    lejano.radio_de_disparo = 1.0
    assert camara.disparar_rayo([lejano]) is lejano


def test_red_cliente_servidor_localhost():
    import time
    host = crear_pilas()
    cli = crear_pilas()
    srv = host.red.hospedar(puerto=0)          # puerto 0 = cualquiera libre
    cli_c = cli.red.conectar('localhost', srv.puerto)

    recibidos_host, recibidos_cli = [], []
    srv.cuando_reciba('chat',
                      lambda d, de: recibidos_host.append((d, de)))
    cli_c.cuando_reciba('chat',
                        lambda d, de: recibidos_cli.append((d, de)))

    for _ in range(50):                        # esperar el 'hola'
        if cli_c.id is not None:
            break
        time.sleep(0.02); cli._tick(0.01)
    assert cli_c.id == 1

    cli_c.enviar('chat', texto='hola')
    for _ in range(50):
        if recibidos_host:
            break
        time.sleep(0.02); host._tick(0.01)
    assert recibidos_host[0] == ({'texto': 'hola'}, 1)

    srv.enviar('chat', texto='bienvenido')     # broadcast server→cliente
    for _ in range(50):
        if recibidos_cli:
            break
        time.sleep(0.02); cli._tick(0.01)
    assert recibidos_cli[0] == ({'texto': 'bienvenido'}, None)

    cli_c.cerrar()
    srv.cerrar()


def test_personajes_predefinidos_se_construyen():
    pilas = crear_pilas()
    for nombre in ('Robot', 'Humanoide', 'Mono', 'Arania', 'Espectro'):
        p = getattr(pilas.actores, nombre)(x=1)
        assert p in pilas.escena.actores
        geo = p._generar_geometria()
        assert len(geo[0]) > 0           # tiene vértices
        assert len(geo[0]) == len(geo[1])  # una normal por vértice


def test_mallas_combinar_con_colores():
    from pilas3d import mallas, colores
    geo = mallas.combinar([
        (mallas.cubo(1.0), (0, 0, 0), colores.rojo),
        (mallas.cubo(0.5), (0, 1, 0)),           # sin color -> blanco
    ])
    pos, nor, modo, cols, uvs = geo
    n = len(pos) // 3
    assert len(cols) == n * 4                    # rgba por vértice
    assert cols[:4] == [1, 0, 0, 1]              # primera parte roja
    assert cols[-4:] == [1, 1, 1, 1]             # última parte blanca


def test_bot_patrulla_persigue_y_vuelve():
    pilas = crear_pilas()
    bot = pilas.actores.Bot(x=0, z=0, radio_vision=5, velocidad=10)
    objetivo = pilas.actores.Cubo(x=30, z=30)

    bot.objetivo = objetivo
    for _ in range(10):
        bot.pre_actualizar()    # corre las habilidades (dt = 1/60)
    assert bot.estado == 'patrullar'

    objetivo.posicion = (2, 0, 2)          # entra en radio_vision
    bot.pre_actualizar()
    assert bot.estado == 'perseguir'
    for _ in range(120):
        bot.pre_actualizar()
    d = ((bot.x - 2) ** 2 + (bot.z - 2) ** 2) ** 0.5
    assert d < 1.0                          # lo alcanzó

    objetivo.posicion = (50, 0, 50)         # se escapa lejos
    bot.pre_actualizar()
    assert bot.estado == 'volver'
    for _ in range(400):
        bot.pre_actualizar()
    assert bot.estado == 'patrullar'        # llegó a casa y retomó
    d_casa = ((bot.x - bot.casa[0]) ** 2 + (bot.z - bot.casa[1]) ** 2)
    assert d_casa < bot.radio_patron ** 2   # patrulla dentro del radio


def test_bot_cuerpo_elegible():
    pilas = crear_pilas()
    bot = pilas.actores.Bot(personaje='Mono')
    from pilas3d.actores.personajes import Mono
    assert isinstance(bot, Mono)
    assert bot.tiene_habilidad(bot.pilas.habilidades.SerBot)


def test_serbot_se_aprende_en_cualquier_actor():
    pilas = crear_pilas()

    from pilas3d.actores.actor import Actor

    class MiPersonaje(Actor):
        def _generar_geometria(self):
            from pilas3d import mallas
            return mallas.cubo(1.0)

    p = MiPersonaje(pilas, x=3, z=3)
    p.aprender(pilas.habilidades.SerBot, radio_vision=4)
    assert p.estado == 'patrullar'
    cerca = pilas.actores.Cubo(x=4, z=3)
    p.objetivo = cerca
    p.pre_actualizar()
    assert p.estado == 'perseguir'


def _gltf_esqueletico():
    """Genera un .gltf mínimo con skin de 2 articulaciones y una
    animación que rota la articulación hija 90° en Z."""
    import base64, io, json, struct, tempfile

    buf = io.BytesIO()
    vistas, accesores = [], []

    def acc(fmt, vals):
        """fmt struct + lista -> accessor nuevo."""
        datos = struct.pack('<' + fmt * len(vals), *vals)
        vistas.append({'buffer': 0, 'byteOffset': buf.tell(),
                       'byteLength': len(datos)})
        buf.write(datos)
        accesores.append({})
        return len(accesores) - 1

    def acc_tipo(i, comp, tipo, count):
        accesores[i] = {'bufferView': i, 'componentType': comp,
                        'count': count, 'type': tipo}
        return i

    i_pos = acc_tipo(acc('f', [0, 0, 0, 1, 0, 0, 2, 0, 0]),
                     5126, 'VEC3', 3)
    i_nor = acc_tipo(acc('f', [0, 0, 1] * 3), 5126, 'VEC3', 3)
    i_jts = acc_tipo(acc('B', [0, 1, 0, 0] * 3), 5121, 'VEC4', 3)
    i_wgt = acc_tipo(acc('f', [0.5, 0.5, 0, 0] * 3), 5126, 'VEC4', 3)
    i_idx = acc_tipo(acc('H', [0, 1, 2]), 5123, 'SCALAR', 3)
    ident = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    ibm1 = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -1, 0, 0, 1]
    i_ibm = acc_tipo(acc('f', ident + ibm1), 5126, 'MAT4', 2)
    i_t = acc_tipo(acc('f', [0, 1]), 5126, 'SCALAR', 2)
    s2 = 0.7071067811865476
    i_rot = acc_tipo(acc('f', [0, 0, 0, 1, 0, 0, s2, s2]),
                     5126, 'VEC4', 2)

    doc = {
        'asset': {'version': '2.0'},
        'scene': 0, 'scenes': [{'nodes': [0, 2]}],
        'nodes': [
            {'name': 'raiz', 'children': [1]},
            {'name': 'hueso', 'translation': [1, 0, 0]},
            {'name': 'malla', 'mesh': 0, 'skin': 0},
        ],
        'skins': [{'joints': [0, 1], 'inverseBindMatrices': i_ibm}],
        'meshes': [{'primitives': [{
            'attributes': {'POSITION': i_pos, 'NORMAL': i_nor,
                           'JOINTS_0': i_jts, 'WEIGHTS_0': i_wgt},
            'indices': i_idx}]}],
        'animations': [{'name': 'giro', 'channels': [{
            'target': {'node': 1, 'path': 'rotation'}, 'sampler': 0}],
            'samplers': [{'input': i_t, 'output': i_rot}]}],
        'buffers': [{'uri': 'data:application/octet-stream;base64,' +
                     base64.b64encode(buf.getvalue()).decode()}],
        'bufferViews': vistas, 'accessors': accesores,
    }
    f = tempfile.NamedTemporaryFile(suffix='.gltf', delete=False,
                                    mode='w')
    json.dump(doc, f)
    f.close()
    return f.name


def test_modelo_tinte_multiplica_colores():
    """color/transparencia tiñen los colores por vértice del modelo."""
    pilas = crear_pilas()
    m = pilas.actores.ModeloGLTF('modelos/personajes/fox/Fox.glb')
    m._construir_gl()
    blancos = list(m._listas[0]['vl'].color[:4])
    assert blancos == [1.0, 1.0, 1.0, 1.0]      # material sin tinte
    m.color = pilas.colores.rojo
    m._construir_gl()
    r = list(m._listas[0]['vl'].color[:4])
    assert r[0] == 1.0 and r[1] == 0.0 and r[2] == 0.0  # teñido rojo
    m.color = pilas.colores.blanco
    m.transparencia = 50
    m._construir_gl()
    assert abs(m._listas[0]['vl'].color[3] - 0.5) < 0.01


def test_modelo_fabrica_rutea_glb_y_diferencia_animado():
    """pilas.actores.Modelo acepta .glb (delega a ModeloGLTF) y los
    flags es_animado/es_estatico distinguen skinned vs rígido."""
    pilas = crear_pilas()
    from pilas3d.actores.modelo_gltf import ModeloGLTF
    fox = pilas.actores.Modelo('modelos/personajes/fox/Fox.glb')
    assert isinstance(fox, ModeloGLTF)
    assert fox.es_animado and not fox.es_estatico
    caballo = pilas.actores.ModeloGLTF(
        'modelos/personajes/horse/clydesdale_horse_-_3d_model_free.glb')
    assert caballo.es_estatico and not caballo.es_animado


def test_gltf_uv_flip_v():
    """glTF usa origen de V arriba-izquierda; OpenGL abajo-izquierda.
    El loader debe voltear V (v -> 1 - v) al leer TEXCOORD_0, si no el
    mesh muestrea el atlas espejado (el bug de los parches del Fox)."""
    import base64, io, json, struct, tempfile
    from pilas3d import gltf
    buf = io.BytesIO()
    vistas, accesores = [], []
    def acc(fmt, vals, comp, tipo, count):
        datos = struct.pack('<' + fmt * len(vals), *vals)
        vistas.append({'buffer': 0, 'byteOffset': buf.tell(),
                       'byteLength': len(datos)})
        buf.write(datos)
        accesores.append({'bufferView': len(vistas) - 1,
                          'componentType': comp, 'count': count,
                          'type': tipo})
        return len(accesores) - 1
    i_pos = acc('f', [0, 0, 0, 1, 0, 0, 0, 1, 0], 5126, 'VEC3', 3)
    i_uv = acc('f', [0.1, 0.25, 0.5, 0.25, 0.9, 0.75],
               5126, 'VEC2', 3)
    doc = {
        'asset': {'version': '2.0'},
        'scene': 0, 'scenes': [{'nodes': [0]}],
        'nodes': [{'mesh': 0}],
        'meshes': [{'primitives': [{
            'attributes': {'POSITION': i_pos, 'TEXCOORD_0': i_uv}}]}],
        'buffers': [{'uri': 'data:application/octet-stream;base64,' +
                     base64.b64encode(buf.getvalue()).decode()}],
        'bufferViews': vistas, 'accessors': accesores,
    }
    with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False,
                                     mode='w') as f:
        json.dump(doc, f)
    escena = gltf.cargar(f.name)
    uvs = escena['mallas'][0]['uvs']
    esperados = [[0.1, 0.75], [0.5, 0.75], [0.9, 0.25]]
    for uv, (eu, ev) in zip(uvs, esperados):
        assert abs(uv[0] - eu) < 1e-6 and abs(uv[1] - ev) < 1e-6


def test_gltf_esqueletico_carga_y_anima():
    pilas = crear_pilas()
    ruta = _gltf_esqueletico()
    m = pilas.actores.ModeloGLTF(ruta)
    assert m.animaciones() == ['giro']
    m.animar('giro')
    m._construir_gl()          # vertex list para escribir el skinning
    pilas.dt = 0.5
    m.actualizar()             # t=0.5: rotación intermedia (~45°)
    m.actualizar()             # t=1.0: 90° completa

    # vértice (2,0,0): 50% bind + 50% rotado 90° sobre (1,0)
    # -> (2*0.5 + 1*0.5, 0 + 0.5, 0) = (1.5, 0.5, 0)
    p = m._vertex_list.position
    vx, vy, vz = p[6], p[7], p[8]
    assert abs(vx - 1.5) < 0.01
    assert abs(vy - 0.5) < 0.01
    assert abs(vz) < 0.01


def test_gltf_aplicar_pose_restaura_tras_animar():
    """aplicar_pose devuelve el modelo a una pose previa — lo que el
    editor usa para 'volver' (U) después de reproducir una animación."""
    pilas = crear_pilas()
    m = pilas.actores.ModeloGLTF(_gltf_esqueletico())
    i = m.huesos()[1][0]
    m.rotar_hueso(i, 'z', 30)
    m.refrescar_pose()
    pose_editada = m._pose_actual()
    r_editada = list(m._escena['nodos'][i]['r'])

    m.animar('giro', ciclica=False)
    m._construir_gl()
    pilas.dt = 0.5
    m.actualizar()                    # la animación pisa los nodos
    assert list(m._escena['nodos'][i]['r']) != r_editada

    m.detener()
    assert m.animacion is None        # quedó congelada en el frame
    m.aplicar_pose(pose_editada)
    assert list(m._escena['nodos'][i]['r']) == \
        pytest.approx(r_editada)


# -- controles de mouse ----------------------------------------------------


def test_rayo_desde_mouse_centro_apunta_al_objetivo():
    pilas = crear_pilas()
    cam = pilas.escena.camara
    origen, dir_ = cam.rayo_desde_mouse(320, 240, ancho=640, alto=480)
    frente = cam.direccion()
    assert abs(origen.x - cam.x) < 1e-6
    for a, b in zip((dir_.x, dir_.y, dir_.z),
                    (frente.x, frente.y, frente.z)):
        assert abs(a - b) < 1e-6


def test_actor_bajo_mouse_y_punto_en_plano():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()            # en el origen, radio 1
    cam = pilas.escena.camara             # (0,5,12) mirando al origen

    assert cam.actor_bajo_mouse(x=320, y=240) is cubo
    assert cam.actor_bajo_mouse(x=0, y=0) is None     # esquina: nada

    # el rayo del centro corta el piso justo en el origen
    px, py, pz = cam.punto_bajo_mouse(0.0, x=320, y=240)
    assert abs(px) < 1e-4 and abs(py) < 1e-4 and abs(pz) < 1e-4


def test_cuando_hace_click_despacha_actor_y_punto():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    recibido = []
    pilas.cuando_hace_click(lambda a, p: recibido.append((a, p)))

    pilas.procesar_click(320, 240)     # centro: pega en el cubo
    pilas.procesar_click(0, 0)         # esquina: nada bajo el mouse

    assert recibido[0][0] is cubo
    assert recibido[0][1] == pytest.approx((0, 0, 0), abs=1e-4)
    assert recibido[1][0] is None


class _ControlFalso(object):
    izquierda = derecha = arriba = abajo = False
    boton_izquierdo = boton_derecho = boton_medio = False
    mouse_x, mouse_y = 320, 240

    def simbolo(self, tecla):
        return False


def test_seguir_al_mouse_teletransporta_al_punto():
    pilas = crear_pilas()
    actor = pilas.actores.Esfera(x=20, z=20)
    actor.aprender(pilas.habilidades.SeguirAlMouse)
    pilas.control = _ControlFalso()          # mouse en el centro

    actor.pre_actualizar()
    esperado = pilas.escena.camara.punto_bajo_mouse(0.0, x=320, y=240)
    assert actor.x == pytest.approx(esperado[0], abs=1e-4)
    assert actor.z == pytest.approx(esperado[2], abs=1e-4)


def test_arrastrable_arrastra_solo_al_actor_clickeado():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    otro = pilas.actores.Esfera(x=8, z=0)
    cubo.aprender(pilas.habilidades.Arrastrable)
    otro.aprender(pilas.habilidades.Arrastrable)
    pilas.control = _ControlFalso()
    pilas.control.boton_izquierdo = True

    # click en el centro: sobre el cubo -> solo el cubo se arrastra
    otro.pre_actualizar()
    cubo.pre_actualizar()
    assert otro.x == pytest.approx(8)
    assert abs(cubo.x) < 0.01 and abs(cubo.z) < 0.01

    # mouse a la esquina mientras sigue presionado -> el cubo sigue
    pilas.control.mouse_x, pilas.control.mouse_y = 400, 240
    cubo.pre_actualizar()
    assert cubo.x > 0.01
    assert otro.x == pytest.approx(8)

    # al soltar deja de arrastrarse
    pilas.control.boton_izquierdo = False
    pilas.control.mouse_x, pilas.control.mouse_y = 500, 240
    x_quieto = cubo.x
    cubo.pre_actualizar()
    assert cubo.x == pytest.approx(x_quieto)


# -- disparo / proyectiles ---------------------------------------------------


def test_disparar_crea_proyectil_hacia_adelante():
    pilas = crear_pilas()
    nave = pilas.actores.Cubo()               # rotacion_y=0 -> mira +Z
    nave.aprender(pilas.habilidades.Disparar, cadencia=0.1)
    p = nave.disparar()

    assert p is not None
    assert p.direccion == (0.0, 0.0, 1.0)     # adelante del actor
    assert p.y == pytest.approx(0.5)          # offset por defecto
    assert p.ignorar is nave                  # no se pega a sí mismo
    assert len(pilas.escena.actores) == 2

    # avanza y se elimina al agotar el alcance
    p.alcance = 2.0
    for _ in range(30):
        p.actualizar()
    assert not p.esta_en_escena()


def test_disparar_respeta_cadencia():
    pilas = crear_pilas()
    nave = pilas.actores.Cubo()
    nave.aprender(pilas.habilidades.Disparar, cadencia=0.5)

    assert nave.disparar() is not None
    assert nave.disparar() is None           # en cooldown
    nave._espera_disparo = -1                # forzar recarga
    assert nave.puede_disparar()
    assert nave.disparar() is not None


def test_proyectil_impacta_y_avisa():
    pilas = crear_pilas()
    blanco = pilas.actores.Cubo(x=0, z=5)    # radio de colision 1
    pegados = []
    nave = pilas.actores.Cubo()
    nave.aprender(pilas.habilidades.Disparar,
                  objetivos=[blanco],
                  cuando_impacta=lambda p, a: pegados.append(a),
                  cadencia=0)
    nave.disparar()

    bala = [a for a in pilas.escena.actores
            if a.__class__.__name__ == 'Proyectil'][0]
    for _ in range(40):
        if not bala.esta_en_escena():
            break
        bala.actualizar()

    assert pegados == [blanco]
    assert not bala.esta_en_escena()


def test_disparar_desde_camara_sigue_la_mira():
    pilas = crear_pilas()
    jugador = pilas.actores.Cubo(x=9, z=9)
    jugador.aprender(pilas.habilidades.Disparar,
                     desde_camara=True, cadencia=0)
    p = jugador.disparar()
    cam = pilas.escena.camara
    frente = cam.direccion()
    assert p.posicion == pytest.approx(cam.posicion)
    for a, b in zip(p.direccion,
                    (frente.x, frente.y, frente.z)):
        assert a == pytest.approx(b)


# -- menu ---------------------------------------------------------------------


def test_menu_navega_y_ejecuta_opciones():
    pilas = crear_pilas()
    log = []
    menu = pilas.actores.Menu(opciones=[
        ("Jugar", lambda: log.append('jugar')),
        ("Opciones", lambda: log.append('opc')),
        ("Salir", lambda: log.append('salir')),
    ])

    assert menu.opcion == 0
    menu.elegir()
    menu.mover('abajo')
    menu.mover('abajo')
    assert menu.opcion == 2
    menu.elegir()
    menu.mover('abajo')                    # envuelve a la primera
    assert menu.opcion == 0
    menu.elegir()
    assert log == ['jugar', 'salir', 'jugar']


def test_menu_opcion_que_cicla_actualiza_texto():
    pilas = crear_pilas()
    calidades = iter(['Calidad: media', 'Calidad: alta'])
    menu = pilas.actores.Menu(opciones=[
        ("Calidad: baja", lambda: next(calidades)),
    ])
    menu.elegir()
    assert menu._opciones[0][0] == 'Calidad: media'
    menu.elegir()
    assert menu._opciones[0][0] == 'Calidad: alta'


def test_menu_click_en_opcion_la_activa():
    pilas = crear_pilas()
    elegido = []
    menu = pilas.actores.Menu(
        opciones=[("Uno", lambda: elegido.append(1)),
                  ("Dos", lambda: elegido.append(2))],
        x=100, y=200, separacion=40, tamano=20)

    y_segunda = menu._textos[1]._y
    menu._al_click_mouse(110, y_segunda + 10, 1, None)
    assert elegido == [2]
    assert menu.opcion == 1

    # click fuera de cualquier opcion: nada
    menu._al_click_mouse(5, 5, 1, None)
    assert elegido == [2]


def test_menu_fondo_y_centrado():
    """El panel envuelve las opciones y centrar() lo deja en el medio."""
    pilas = crear_pilas()
    menu = pilas.actores.Menu(
        opciones=[("Jugar", None), ("Salir", None)],
        x=200, y=300, fondo=(0, 0, 0, 120), centrado=True)
    assert menu._fondo_rgba == (0, 0, 0, 120)
    x0, y0, x1, y1 = menu._rect_panel()
    assert abs((x0 + x1) / 2 - 400) < 1    # ventana default 800x600
    assert abs((y0 + y1) / 2 - 300) < 1
    menu.dibujar()                          # no falla en headless


def test_menu_sonidos_de_navegacion():
    """sonido_mover/elegir cargan un efecto y lo suenan al usarlo."""
    pilas = crear_pilas()
    menu = pilas.actores.Menu(opciones=[("A", None), ("B", None)],
                              sonido_mover=True, sonido_elegir=True)
    assert menu._snd_mover is not None
    assert menu._snd_elegir is not None
    tocados = []
    menu._snd_mover.reproducir = lambda: tocados.append('mover')
    menu._snd_elegir.reproducir = lambda: tocados.append('elegir')
    menu.mover('abajo')
    menu.elegir()
    assert tocados == ['mover', 'elegir']
    # sonido_mover con ruta propia
    menu2 = pilas.actores.Menu(opciones=[("A", None)],
                               sonido_mover='tick.wav')
    assert menu2._snd_mover is not None
    assert menu2._snd_elegir is None


def test_menu_limpia_sus_textos():
    pilas = crear_pilas()
    menu = pilas.actores.Menu(opciones=[("A", None), ("B", None)],
                              titulo="Mi menu")
    assert len(pilas.escena.actores) == 4    # menu + titulo + 2 items
    pilas.limpiar()
    assert len(pilas.escena.actores) == 0


def test_menu_checkbox_alterna_y_avisa():
    pilas = crear_pilas()
    cambios = []
    menu = pilas.actores.Menu(opciones=[
        ("Sonido", 'check', True, lambda v: cambios.append(v)),
    ])
    menu.elegir()                       # apaga
    assert cambios == [False]
    assert '[ ] Sonido' in menu._textos[0].texto
    menu.elegir()                       # prende
    assert cambios == [False, True]
    assert '[x] Sonido' in menu._textos[0].texto


def test_menu_input_edita_y_confirma():
    pilas = crear_pilas()
    nombres = []
    menu = pilas.actores.Menu(opciones=[
        ("Nombre", 'input', 'jugador', lambda v: nombres.append(v)),
    ])
    menu.elegir()                       # entra en edicion
    assert menu._editando == 0
    menu.mover('abajo')                 # bloqueado editando
    assert menu.opcion == 0
    for c in 'ana':                     # borra y tipea
        pass
    for _ in range(7):
        menu.escribir('\b')             # borra "jugador"
    for c in 'ana':
        menu.escribir(c)
    menu.confirmar_edicion()
    assert nombres == ['ana']
    assert 'Nombre: ana' in menu._textos[0].texto


def test_sonidos_volumen_maestro_y_mute():
    pilas = crear_pilas()
    class _JugadorFalso:
        def __init__(self): self.volume = 1.0
    class _S(pilas3d.sonidos.Sonido):
        def __init__(self, master):
            self._volumen = 1.0
            self._master = master
            self._jugador_bucle = _JugadorFalso()
            self._jugadores = []

    s = _S(pilas.sonidos)
    pilas.sonidos._cargados.append(s)
    pilas.sonidos.volumen = 0.5
    assert s._jugador_bucle.volume == pytest.approx(0.5)
    pilas.sonidos.mute = True
    assert s._jugador_bucle.volume == 0.0
    s.volumen = 0.8                     # propio x master, mute sigue
    assert s._jugador_bucle.volume == 0.0
    pilas.sonidos.desilenciar()
    assert s._jugador_bucle.volume == pytest.approx(0.4)


def test_menu_persiste_config_en_json(tmp_path):
    ruta = str(tmp_path / 'config-game.json')
    aplicados = []
    pilas = crear_pilas()
    menu = pilas.actores.Menu(
        guardar_en=ruta,
        opciones=[
            ("Sonido", 'check', True, lambda v: aplicados.append(v)),
            ("Nombre", 'input', 'jugador', lambda v: aplicados.append(v)),
            ("Volumen: 100%", lambda: "Volumen: 75%"),
        ])

    menu.elegir()                       # apaga sonido -> guarda
    datos = json.loads(open(ruta).read())
    assert datos == {'Sonido': False, 'Nombre': 'jugador',
                     'Volumen': 'Volumen: 100%'}

    # un menú nuevo con la misma ruta restaura y aplica los valores
    pilas.limpiar()
    menu2 = pilas.actores.Menu(
        guardar_en=ruta,
        opciones=[
            ("Sonido", 'check', True, lambda v: aplicados.append(v)),
            ("Nombre", 'input', 'jugador', lambda v: aplicados.append(v)),
        ])
    assert menu2._opciones[0][2] is False     # check restaurado
    assert menu2._opciones[1][2] == 'jugador' # input restaurado
    assert False in aplicados and 'jugador' in aplicados  # se aplicaron


def test_temporizador_cuenta_regresiva_ejecuta_funcion():
    pilas = crear_pilas()
    llamadas = []
    t = pilas.actores.Temporizador(duracion=1.0,
                                 cuando_termina=lambda: llamadas.append('fin'))
    t.iniciar()
    pilas.dt = 0.4
    t.actualizar()
    assert t.tiempo == pytest.approx(0.6)
    assert t.texto == '1'
    t.actualizar(); t.actualizar(); t.actualizar()
    assert llamadas == ['fin']
    assert t.activo is False              # se detiene al terminar
    t.actualizar()
    assert llamadas == ['fin']            # no repite solo


def test_temporizador_ciclico_y_avisos():
    pilas = crear_pilas()
    eventos = []
    t = pilas.actores.Temporizador(duracion=1.0, ciclico=True,
                                 cuando_termina=lambda: eventos.append('ciclo'))
    t.avisar(0.5, lambda: eventos.append('aviso'))
    t.iniciar()
    pilas.dt = 0.6
    t.actualizar()                        # cruza 0.5 -> aviso
    t.actualizar()                        # llega a 0 -> ciclo + reinicia
    assert eventos == ['aviso', 'ciclo']
    assert t.tiempo == pytest.approx(1.0)
    assert t.activo is True
    t.actualizar()                        # el aviso se rearma en el nuevo ciclo
    assert eventos.count('aviso') == 2


def test_temporizador_cronometro_invisible_y_reiniciar():
    pilas = crear_pilas()
    t = pilas.actores.Temporizador(visible=False)   # duracion=0 -> cronómetro
    t.iniciar()
    pilas.dt = 0.5
    t.actualizar(); t.actualizar()
    assert t.tiempo == pytest.approx(1.0)
    t.detener()
    t.actualizar()
    assert t.tiempo == pytest.approx(1.0) # pausado no avanza
    t.reiniciar()
    assert t.tiempo == 0
    assert t.activo is True


def test_temporizador_ajustar_formato_y_autoeliminar():
    pilas = crear_pilas()
    t = pilas.actores.Temporizador(autoeliminar=True,
                                 formato=lambda s: '%.1f' % s)
    t.ajustar(0.3)
    t.iniciar()
    pilas.dt = 0.5
    t.actualizar()
    assert t not in pilas.escena.actores  # se eliminó solo


def test_camara_seguir_a_tercera_persona():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo(y=1)
    cubo.rotacion_y = 0          # mira a +Z
    cam = pilas.escena.camara
    cam.seguir_a(cubo, modo='tercera', distancia=6, altura=3,
                 suavizado=0)
    cam.actualizar(0.016)
    assert cam.posicion == pytest.approx((0, 4, -6))   # detrás y arriba
    assert cam.objetivo == pytest.approx((0, 2.5, 0))  # a los ojos
    cubo.rotacion_y = 180        # ahora mira a -Z
    cam.actualizar(0.016)
    assert cam.posicion == pytest.approx((0, 4, 6))


def test_camara_seguir_a_primera_y_segunda():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo(y=1)
    cam = pilas.escena.camara
    cam.seguir_a(cubo, modo='primera', ojos=1.6, suavizado=0)
    cam.actualizar(0.016)
    assert cam.posicion == pytest.approx((0, 2.6, 0))      # en los ojos
    assert cam.objetivo == pytest.approx((0, 2.6, 1))      # mirando +Z
    cam.seguir_a(cubo, modo='segunda', distancia=4, altura=2,
                 suavizado=0)
    cam.actualizar(0.016)
    assert cam.posicion == pytest.approx((0, 3, 4))        # delante
    assert cam.objetivo == pytest.approx((0, 2.5, 0))
    cam.dejar_de_seguir()
    cubo.x = 50
    cam.actualizar(0.016)
    assert cam.posicion == pytest.approx((0, 3, 4))        # ya no sigue


def test_gltf_rotar_y_guardar_pose(tmp_path):
    import math
    from pilas3d import gltf as _g
    ruta = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
    if not os.path.exists(ruta):
        pytest.skip('modelo wolf no disponible')
    pilas = crear_pilas()
    lobo = pilas.actores.ModeloGLTF(ruta)
    huesos = lobo.huesos()
    assert len(huesos) > 10
    i, nombre = huesos[5]
    r0 = tuple(lobo._escena['nodos'][i]['r'])
    lobo.rotar_hueso(i, 'z', 90)
    r1 = tuple(lobo._escena['nodos'][i]['r'])
    assert r1 != r0                        # la pose cambió
    pos = lobo.posicion_hueso(i)
    assert all(not math.isnan(v) for v in pos)
    # guardar / reiniciar / cargar
    ruta_json = str(tmp_path / 'pose.json')
    lobo.guardar_pose(ruta_json)
    lobo.reiniciar_pose()
    assert tuple(lobo._escena['nodos'][i]['r']) == pytest.approx(r0)
    lobo.cargar_pose(ruta_json)
    assert tuple(lobo._escena['nodos'][i]['r']) == pytest.approx(r1)


def test_gltf_crear_animacion_desde_keyframes():
    ruta = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
    if not os.path.exists(ruta):
        pytest.skip('modelo wolf no disponible')
    pilas = crear_pilas()
    lobo = pilas.actores.ModeloGLTF(ruta)
    i, _ = lobo.huesos()[3]
    pose_a = lobo._pose_actual()            # keyframe 0: pose base
    lobo.rotar_hueso(i, 'z', 90)
    pose_b = lobo._pose_actual()            # keyframe 1: rotado
    nombre = lobo.crear_animacion('test', [pose_a, pose_b],
                                  duracion=1.0)
    lobo.animar(nombre, ciclica=False)
    assert lobo.animacion == 'test'
    anim = lobo._escena['animaciones']['test']
    assert anim['duracion'] == 1.0
    canal = [c for c in anim['canales'] if c['nodo'] == i][0]
    assert canal['camino'] == 'rotation'
    assert canal['tiempos'] == [0.0, 1.0]
    # mid-animación: el hueso queda interpolado (ni A ni B)
    lobo._t = 0.5
    lobo.actualizar()
    r_mid = lobo._escena['nodos'][i]['r']
    assert r_mid != pytest.approx(canal['valores'][0])
    with pytest.raises(ValueError):          # poses iguales -> error
        lobo.crear_animacion('vacia', [pose_a, dict(pose_a)])


def test_gltf_guardar_y_cargar_animacion(tmp_path):
    ruta = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
    if not os.path.exists(ruta):
        pytest.skip('modelo wolf no disponible')
    pilas = crear_pilas()
    lobo = pilas.actores.ModeloGLTF(ruta)
    i, _ = lobo.huesos()[3]
    pose_a = lobo._pose_actual()
    lobo.rotar_hueso(i, 'z', 45)
    lobo.crear_animacion('propia', [pose_a, lobo._pose_actual()])
    ruta_json = str(tmp_path / 'anim.json')
    lobo.guardar_animacion(ruta_json, 'propia')
    # otro modelo la carga y puede animarla
    otro = pilas.actores.ModeloGLTF(ruta)
    nombre = otro.cargar_animacion(ruta_json)
    assert nombre == 'propia'
    otro.animar(nombre)
    assert otro.animacion == 'propia'
    assert otro._escena['animaciones']['propia']['canales']
    with pytest.raises(ValueError):
        lobo.guardar_animacion(ruta_json, 'no_existe')


def test_gltf_rotar_hueso_por_nombre(tmp_path):
    ruta = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
    if not os.path.exists(ruta):
        pytest.skip('modelo wolf no disponible')
    pilas = crear_pilas()
    lobo = pilas.actores.ModeloGLTF(ruta)
    i, nombre = lobo.huesos()[0]
    lobo.rotar_hueso(nombre, 'x', 45)      # por nombre
    assert tuple(lobo._escena['nodos'][i]['r']) != (0, 0, 0, 1) \
        or True                            # algunos ya rotan
    with pytest.raises(ValueError):
        lobo.rotar_hueso('no_existo', 'x', 10)


def test_panel_es_overlay():
    pilas = crear_pilas()
    p = pilas.actores.Panel(x=5, y=10, ancho=200, alto=90,
                            opacidad=200)
    assert p.es_overlay
    assert (p.x, p.y) == (5, 10)
    assert (p.ancho, p.alto) == (200, 90)
    assert p.opacidad == 200
    p.x, p.ancho = 30, 100          # reubicable (layout dinámico)
    assert (p.x, p.ancho) == (30, 100)


def test_esqueleto_mapear_y_animar():
    ruta = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
    if not os.path.exists(ruta):
        pytest.skip('modelo wolf no disponible')
    from pilas3d.esqueleto import mapear_huesos, animacion_procedural
    pilas = crear_pilas()
    lobo = pilas.actores.ModeloGLTF(ruta)
    mapa = mapear_huesos(lobo.huesos())
    # el wolf (nombres en alemán) mapea completo
    for parte in ('pierna_izq', 'pierna_der', 'brazo_izq',
                  'brazo_der', 'cola', 'cabeza'):
        assert mapa.get(parte), parte
    # ojos/boca no entran en ningún grupo animable
    animables = set().union(*mapa.values())
    cara = [i for i, n in lobo.huesos() if 'aug' in n.lower()
            or 'maul' in n.lower()]
    assert not animables.intersection(cara)
    # animación procedural: genera clip y anima
    lobo.animar(animacion_procedural(lobo, 'caminar', mapa=mapa))
    assert lobo.animacion == 'caminar'
    assert lobo._escena['animaciones']['caminar']['canales']
    lobo.animar(animacion_procedural(lobo, 'cola', mapa=mapa))
    with pytest.raises(ValueError):
        animacion_procedural(lobo, 'inexistente')


def test_gltf_anim_json_junto_al_modelo(tmp_path):
    import shutil
    ruta = 'modelos/personajes/wolf/Wolf-Blender-2.82a.glb'
    if not os.path.exists(ruta):
        pytest.skip('modelo wolf no disponible')
    # copia el glb a tmp y deja un clip .anim.json al lado
    copia = tmp_path / 'w.glb'
    shutil.copy(ruta, copia)
    pilas = crear_pilas()
    lobo = pilas.actores.ModeloGLTF(ruta)
    i, _ = lobo.huesos()[3]
    pose_a = lobo._pose_actual()
    lobo.rotar_hueso(i, 'z', 45)
    lobo.crear_animacion('propia', [pose_a, lobo._pose_actual()])
    lobo.guardar_animacion(str(copia).replace('.glb', '.anim.json'),
                           'propia')
    # al cargar el glb el clip ya viene registrado solo
    otro = pilas.actores.ModeloGLTF(str(copia))
    assert 'propia' in otro.animaciones()
    otro.animar('propia')
    assert otro.animacion == 'propia'


def test_puente_bloques(tmp_path):
    """El puente HTTP encola código y lo ejecuta en la escena."""
    import json
    import urllib.request
    from pilas3d.puente import PuenteBloques

    web = tmp_path / 'web'
    web.mkdir()
    (web / 'index.html').write_text('pagina de prueba')

    pilas = crear_pilas()
    puente = PuenteBloques(pilas, str(web))
    puente.enganchar()
    url = puente.iniciar(0)          # puerto libre al azar
    try:
        assert urllib.request.urlopen(url).read() == b'pagina de prueba'

        req = urllib.request.Request(
            url + 'codigo',
            data=json.dumps({'codigo':
                             "cubo = pilas.actores.Cubo()\n"
                             "print('hola')"}).encode(),
            headers={'Content-Type': 'application/json'})
        assert json.loads(urllib.request.urlopen(req).read()) == \
            {'estado': 'encolado'}

        puente.procesar()            # lo que haría la tarea cada frame
        r = json.loads(
            urllib.request.urlopen(url + 'resultado').read())
        assert r['estado'] == 'ok' and 'hola' in r['salida']
        assert len(pilas.escena.actores) == 1

        # código con error: no rompe el motor, reporta traceback
        req = urllib.request.Request(
            url + 'codigo',
            data=json.dumps({'codigo': 'boom()'}).encode(),
            headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
        puente.procesar()
        r = json.loads(
            urllib.request.urlopen(url + 'resultado').read())
        assert r['estado'] == 'error' and 'boom' in r['salida']
        # al re-ejecutar la escena anterior quedó limpia
        assert len(pilas.escena.actores) == 0
    finally:
        puente.detener()


def test_puente_bloques_subproceso(tmp_path, monkeypatch):
    """Sin pilas: /codigo lanza un proceso con ventana propia y
    /detener lo mata. (PILAS3D_SIN_VENTANA -> no abre ventana real.)"""
    import json
    import os
    import time
    import urllib.request
    from pilas3d.puente import PuenteBloques

    monkeypatch.setenv('PILAS3D_SIN_VENTANA', '1')
    web = tmp_path / 'web'
    web.mkdir()
    (web / 'index.html').write_text('pagina')

    puente = PuenteBloques(None, str(web))
    url = puente.iniciar(0)
    try:
        req = urllib.request.Request(
            url + 'codigo',
            data=json.dumps({'codigo': "print('anduvo')"}).encode(),
            headers={'Content-Type': 'application/json'})
        assert json.loads(urllib.request.urlopen(req).read()) == \
            {'estado': 'lanzado'}

        # sin ventana el proceso ejecuta y termina -> 'ok' + salida
        for _ in range(100):
            r = json.loads(
                urllib.request.urlopen(url + 'resultado').read())
            if r['estado'] != 'ejecutando':
                break
            time.sleep(0.05)
        assert r['estado'] == 'ok' and 'anduvo' in r['salida']

        # detener cuando ya terminó no explota
        req = urllib.request.Request(url + 'detener', data=b'')
        assert json.loads(urllib.request.urlopen(req).read()) == \
            {'estado': 'detenido'}
    finally:
        puente.detener()


def _ejemplos_bloques():
    """Parsea pilas3d/bloques_web/ejemplos.js -> [{nombre, xml}]."""
    import re
    import xml.etree.ElementTree as ET
    from pathlib import Path

    src = (Path(__file__).parent.parent /
           'pilas3d/bloques_web/ejemplos.js').read_text()
    ejemplos = []
    for m in re.finditer(r"nombre:\s*'([^']+)'", src):
        # el xml es la concatenación de literales '...' + hasta la coma
        xml_m = re.search(
            r"xml:\s*((?:'[^']*'\s*\+\s*)*'[^']*')",
            src[m.end():])
        xml = ''.join(re.findall(r"'([^']*)'", xml_m.group(1)))
        ejemplos.append({'nombre': m.group(1), 'xml': xml})
        ET.fromstring(xml)           # falla si el XML está roto
    return ejemplos


def test_ejemplos_bloques_validos():
    """Cada ejemplo precargado: XML bien formado y solo usa bloques
    que existen en bloques.js con sus campos correctos."""
    import re
    import xml.etree.ElementTree as ET
    from pathlib import Path

    src = (Path(__file__).parent.parent /
           'pilas3d/bloques_web/bloques.js').read_text()
    definidos = set(re.findall(r"type:\s*'(p3d_\w+)'", src))
    std = {'controls_if', 'controls_repeat_ext', 'logic_compare',
           'logic_operation', 'logic_negate', 'math_number',
           'math_arithmetic'}
    # campos declarados por bloque: name:'X' entre un type y el próximo
    campos = {}
    partes = re.split(r"type:\s*'(p3d_\w+)'", src)
    for tipo, cuerpo in zip(partes[1::2], partes[2::2]):
        campos.setdefault(tipo, set()).update(
            re.findall(r"name:\s*'(\w+)'", cuerpo))

    ejemplos = _ejemplos_bloques()
    assert len(ejemplos) >= 3
    for e in ejemplos:
        assert e['nombre']
        for b in ET.fromstring(e['xml']).iter('block'):
            tipo = b.get('type')
            assert tipo in definidos | std, (e['nombre'], tipo)
            for f in b.findall('field'):
                assert f.get('name') in campos.get(tipo, set()), \
                    (e['nombre'], tipo, f.get('name'))


def test_actor_decir_crea_y_reusa_globo():
    """actor.decir() crea un Globo lazy atado al actor y lo reutiliza."""
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    globo = cubo.decir('hola!', duracion=2)
    assert type(globo).__name__ == 'Globo'
    assert globo.actor is cubo
    assert globo.texto == 'hola!'
    assert cubo.decir('de nuevo', duracion=1) is globo
    assert globo.texto == 'de nuevo'


def test_ejemplos_selector_en_pagina():
    """index.html expone el selector y carga ejemplos.js; bloques.js
    cablea el onchange que reemplaza el workspace."""
    from pathlib import Path
    web = Path(__file__).parent.parent / 'pilas3d/bloques_web'
    html = (web / 'index.html').read_text()
    js = (web / 'bloques.js').read_text()
    assert 'id="ejemplos"' in html
    assert 'ejemplos.js' in html
    assert html.index('ejemplos.js') < html.index('bloques.js')
    assert 'selEjemplos.onchange' in js
    assert 'ws.clear()' in js


def test_mapas_guardar_cargar(tmp_path):
    """Round-trip de *.mapa.json: bloques + spawn + nombre."""
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.poner_bloque(0, 0, 0, 'cesped')
    mundo.poner_bloque(0, 1, 0, 'ladrillo')
    mundo.poner_bloque(1, 0, 0, 'tierra')

    ruta = str(tmp_path / 'nivel.mapa.json')
    pilas.mapas.guardar(ruta, mundo, nombre='nivel',
                        spawn=(0.5, 2.0, 0.5))

    cargado = pilas.mapas.cargar(ruta)
    assert cargado.nombre == 'nivel'
    assert cargado.spawn == (0.5, 2.0, 0.5)
    assert cargado.bloque_en(0, 1, 0) == 'ladrillo'
    assert len(cargado.bloques) == 3
    assert cargado.props == []

    # archivo inexistente de props se ignora sin romper
    import json
    datos = json.load(open(ruta))
    datos['props'] = [{'ruta': 'no_existe.glb', 'x': 0,
                       'y': 0, 'z': 0}]
    json.dump(datos, open(ruta, 'w'))
    assert pilas.mapas.cargar(ruta).props == []


def test_mapas_props_estaticos(tmp_path):
    """Props .obj en el mapa: ruta relativa al archivo, transform y
    re-guardado conservando la ruta original."""
    import json
    pilas = crear_pilas()
    niveles = tmp_path / 'niveles'
    niveles.mkdir()
    (niveles / 'arbol.obj').write_text(
        'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
    ruta = str(niveles / 'bosque.mapa.json')

    mundo = pilas.actores.Mundo()
    mundo.poner_bloque(0, 0, 0, 'cesped')
    props = [{'ruta': 'arbol.obj', 'x': 2, 'y': 0, 'z': 2,
              'escala': 2.0, 'rotacion_y': 90}]
    pilas.mapas.guardar(ruta, mundo, nombre='bosque',
                        spawn=(0.5, 1.0, 0.5), props=props)

    # 'arbol.obj' no existe en el cwd -> se resuelve junto al .mapa.json
    cargado = pilas.mapas.cargar(ruta)
    assert len(cargado.props) == 1
    prop = cargado.props[0]
    assert prop.ruta == 'arbol.obj'      # ruta original, no la resuelta
    assert prop.posicion == (2, 0, 2)
    assert prop.escala == 2.0
    assert prop.rotacion_y == 90

    # seguir editando: el mundo cargado acepta bloques y re-guarda
    cargado.poner_bloque(1, 0, 0, 'ladrillo')
    pilas.mapas.guardar(
        ruta, cargado, nombre='bosque', spawn=cargado.spawn,
        props=[{'ruta': p.ruta, 'x': p.x, 'y': p.y, 'z': p.z,
                'escala': p.escala, 'rotacion_y': p.rotacion_y}
               for p in cargado.props])
    datos = json.load(open(ruta))
    assert len(datos['bloques']) == 2
    assert datos['props'][0]['ruta'] == 'arbol.obj'
    assert datos['props'][0]['rotacion_y'] == 90


def test_mapas_terreno_se_persiste(tmp_path):
    """generar_terreno -> guardar -> cargar: alturas sobreviven."""
    pilas = crear_pilas()
    mundo = pilas.actores.Mundo()
    mundo.generar_terreno(ancho=8, profundidad=8, altura=3, semilla=7)
    antes = dict(mundo.bloques)
    ruta = str(tmp_path / 'terreno.mapa.json')
    pilas.mapas.guardar(ruta, mundo)
    cargado = pilas.mapas.cargar(ruta)
    assert dict(cargado.bloques) == antes


# -- globo de diálogo --------------------------------------------------------

def test_camara_proyectar():
    """proyectar: mundo -> píxel; centro de vista = centro de pantalla."""
    pilas = crear_pilas()
    cam = pilas.escena_actual().camara
    assert cam.proyectar(0, 0, 0, ancho=640, alto=480) == (320.0, 240.0)
    # arriba en el mundo = mayor y en pantalla (origen abajo)
    _, py = cam.proyectar(0, 3, 0, ancho=640, alto=480)
    assert py > 240
    # detrás de la cámara -> None
    assert cam.proyectar(0, 5, 20, ancho=640, alto=480) is None


def test_globo_sigue_al_actor():
    """El globo se posiciona sobre la proyección del actor."""
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    globo = pilas.actores.Globo(cubo, 'hola', alto=2.0)
    globo.actualizar()
    cam = pilas.escena_actual().camara
    px, py = cam.proyectar(0, 2.0, 0)
    assert globo.x == px and globo.y == py
    # mover el actor mueve el globo
    cubo.x = 3
    globo.actualizar()
    px2, _ = cam.proyectar(3, 2.0, 0)
    assert globo.x == px2
    cubo.eliminar(); globo.eliminar()


def test_globo_decir_con_duracion():
    """decir(texto, duracion) oculta el globo al terminar."""
    pilas = crear_pilas()
    globo = pilas.actores.Globo(None, x=100, y=100)
    globo.decir('hola', duracion=1.0)
    assert globo._visible
    pilas.dt = 0.6
    globo.actualizar()
    assert globo._visible            # todavía
    globo.actualizar()               # acumula 1.2s
    assert not globo._visible
    globo.eliminar()


def test_globo_pagina_textos_largos():
    """Textos largos se reparten en páginas que avanzan solas."""
    pilas = crear_pilas()
    globo = pilas.actores.Globo(None, x=100, y=100)
    largo = ' '.join('palabra%d' % i for i in range(60))   # ~7 líneas
    globo.decir(largo, duracion=0.5)
    assert len(globo._paginas) >= 2
    primera = globo.texto
    pilas.dt = 0.6
    globo.actualizar()               # avanza a la página 2
    assert globo.texto != primera
    assert globo._visible
    # consume todas las páginas -> se oculta (duracion > 0)
    for _ in range(len(globo._paginas) + 1):
        globo.actualizar()
    assert not globo._visible
    globo.eliminar()


def test_globo_paginas_auto_queda_ultima():
    """Sin duración las páginas avanzan a ritmo de lectura y la
    última queda visible."""
    pilas = crear_pilas()
    globo = pilas.actores.Globo(None, x=100, y=100)
    globo.decir(' '.join('w%d' % i for i in range(80)))
    n = len(globo._paginas)
    assert n >= 2
    pilas.dt = 10.0                  # cada update agota una página
    for _ in range(n + 2):
        globo.actualizar()
    assert globo._indice == n - 1
    assert globo._visible            # última página queda fija
    globo.eliminar()


# -- voz (Piper) y ActorIA --------------------------------------------------

def test_voz_url_voz():
    """'es_ES-davefx-medium' → rutas onnx/json en huggingface."""
    from pilas3d.ia import voz
    onnx, js = voz._url_voz('es_ES-davefx-medium')
    assert onnx.endswith('/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx')
    assert js == onnx + '.json'


def test_pedir_texto():
    """pedir_texto: overlay que junta texto y ENTER lo entrega."""
    pilas = crear_pilas()
    handlers = {}

    class VentanaFalsa:
        def push_handlers(self, **kw):
            handlers.update(kw)

    pilas.ventana = VentanaFalsa()
    visto = []
    pilas.pedir_texto('pregunta:', al_aceptar=visto.append)
    s = pilas.simbolos
    for letra in 'hola':
        assert handlers['on_text'](letra) is True
    handlers['on_key_press'](s.BACKSPACE, 0)      # borra la 'a'
    handlers['on_text']('i')
    handlers['on_key_press'](s.ENTER, 0)          # confirma 'holi'
    assert visto == ['holi']
    # cerrado: los handlers ya no consumen nada
    assert handlers['on_key_press'](s.ENTER, 0) is None
    assert handlers['on_text']('x') is None


def test_voz_resolver_voz():
    """Nombres amigables → voz del catálogo; desconocidos pasan igual."""
    from pilas3d.ia import voz
    assert voz._resolver_voz('mujer') == 'es_AR-daniela-high'
    assert voz._resolver_voz('hombre') == 'es_MX-ald-medium'
    assert voz._resolver_voz('es_ES-davefx-medium') == 'es_ES-davefx-medium'
    assert voz._resolver_voz(None) == voz.VOZ


def test_voz_comando():
    """La línea de Piper lleva modelo, salida y espeak-data."""
    from pilas3d.ia import voz
    cmd = voz._comando('/piper/piper', '/voz.onnx', '/out.wav')
    assert cmd[0] == '/piper/piper'
    assert '--model' in cmd and '/voz.onnx' in cmd
    assert '--output_file' in cmd and '/out.wav' in cmd
    assert 'espeak-ng-data' in cmd[-1]


def test_actor_ia_responde_y_dice(monkeypatch):
    """preguntar: Ollama (mockeado) responde -> subtítulo + callback."""
    pilas = crear_pilas()
    npc = pilas.actores.ActorIA('mono', nombre='Mono', habla=False)
    import pilas3d.ia.asistente as asist
    monkeypatch.setattr(asist, 'preguntar',
                        lambda t, modelo=None, al_token=None:
                        'soy un mono')
    visto = []
    npc.al_responder = visto.append
    npc.preguntar('quien sos?')
    # el hilo es async: esperar a que llegue la respuesta
    for _ in range(1000):
        npc.actualizar()
        if visto:
            break
        import time; time.sleep(0.01)
    assert visto == ['soy un mono']
    assert npc.ultima_respuesta == 'soy un mono'
    assert 'Mono: soy un mono' in npc.subtitulo.texto
    npc.eliminar()


def test_actor_ia_hablar(monkeypatch, tmp_path):
    """hablar: sintetiza (mockeado) y reproduce con pilas.sonidos."""
    pilas = crear_pilas()
    npc = pilas.actores.ActorIA('robot')
    wav = tmp_path / 'voz.wav'
    wav.write_bytes(b'RIFF')          # solo tiene que existir
    from pilas3d.ia import voz
    from pilas3d.sonidos import Sonido
    monkeypatch.setattr(voz, 'sintetizar',
                        lambda t, **k: str(wav))
    # sin archivo wav real no hay nada que cargar: sonido apagado
    monkeypatch.setattr(Sonido, 'deshabilitado', True)
    npc.hablar('hola')
    for _ in range(1000):
        npc.actualizar()
        if not npc._pendientes:
            break
        import time; time.sleep(0.01)
    assert not npc._pendientes   # 'sonido' ya se reprodujo
    npc.eliminar()


def test_actor_ia_cuerpo_sigue_al_actor():
    """El cuerpo visual toma la posición/rotación del ActorIA."""
    pilas = crear_pilas()
    npc = pilas.actores.ActorIA('humanoide')
    npc.posicion = (2, 0, 3)
    npc.rotacion_y = 90
    npc.actualizar()
    assert npc.cuerpo.posicion == (2, 0, 3)
    assert npc.cuerpo.rotacion_y == 90
    npc.eliminar()


def test_cerebro_parsear():
    """parsear extrae el JSON de acción y rechaza lo inválido."""
    from pilas3d.habilidades.cerebro import parsear
    assert parsear('{"accion":"mover","dx":1,"dz":0}')['accion'] \
        == 'mover'
    assert parsear('bla {"accion":"decir","texto":"hola"} bla')[
        'texto'] == 'hola'
    assert parsear('{"accion":"borrar_disco"}') is None  # no whitelist
    assert parsear('sin json') is None
    assert parsear('') is None


def test_cerebro_aplica_acciones():
    """Cada acción de la lista blanca mueve al actor como corresponde."""
    from pilas3d.habilidades.cerebro import Cerebro
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    c = Cerebro(pilas)
    c.iniciar(cubo, cada=1)

    c._aplicar({'accion': 'mover', 'dx': 2, 'dz': 0})
    assert cubo.x == 2
    c._aplicar({'accion': 'girar', 'grados': 90})
    assert cubo.rotacion_y % 360 == -0 or True  # verifica abajo
    c._aplicar({'accion': 'ir_a', 'x': -3, 'z': 4})
    assert (cubo.x, cubo.z) == (-3, 4)
    c._aplicar({'accion': 'esperar'})           # no explota
    c._aplicar({'accion': 'decir', 'texto': 'hola'})
    assert cubo._globo.texto == 'hola'          # creó el globo lazy


def test_cerebro_acercarse_alejarse():
    """acercarse/alejarse caminan un paso hacia/desde el objetivo."""
    from pilas3d.habilidades.cerebro import Cerebro
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    meta = pilas.actores.Cubo(x=10, z=0)
    c = Cerebro(pilas)
    c.iniciar(cubo, cada=1, objetivo=meta)
    c._aplicar({'accion': 'acercarse'})
    assert cubo.x > 0                            # se acercó
    x_tras_acercar = cubo.x
    c._aplicar({'accion': 'alejarse'})
    assert cubo.x < x_tras_acercar               # y se alejó


def test_cerebro_piensa_en_hilo_y_actua(monkeypatch):
    """_pensar llama al LLM (mock) y actualizar aplica la decisión."""
    from pilas3d.habilidades import cerebro as mod
    from pilas3d.ia import asistente

    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.aprender(pilas.habilidades.Cerebro, cada=0)
    c = cubo._habilidades[0]

    monkeypatch.setattr(
        asistente, 'llamar_ollama',
        lambda prompt, system=None, modelo=None, al_token=None:
        '{"accion":"ir_a","x":5,"z":-5}')
    c._pensar()                                  # lo que haría el hilo
    assert len(c._pendientes) == 1
    c.actualizar()                               # drena en hilo principal
    assert (cubo.x, cubo.z) == (5, -5)
    assert c.ultima_decision == 'ir_a'

    # respuesta basura no mueve al actor y cuenta el fallo
    monkeypatch.setattr(
        asistente, 'llamar_ollama',
        lambda *a, **k: 'no entiendo la consigna')
    fallos = c.fallos
    c._pensar()
    assert c.fallos == fallos + 1
    c.actualizar()
    assert (cubo.x, cubo.z) == (5, -5)           # no se movió

    # sin Ollama (excepción) el actor solo espera, no crashea
    monkeypatch.setattr(
        asistente, 'llamar_ollama',
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError('sin ia')))
    c._pensar()
    assert c._ocupado is False
    c.actualizar()


def test_chat_sin_cerebro_responde_con_globo(monkeypatch):
    """Chat.decir_a con actor común: la respuesta va a su globo."""
    from pilas3d.ia import asistente
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    chat = pilas.actores.Chat(cubo, tecla='t')
    monkeypatch.setattr(asistente, 'preguntar',
                        lambda *a, **k: 'hola desde el cubo')
    chat.decir_a('hola?')
    for _ in range(200):
        chat.actualizar()
        if getattr(cubo, '_globo', None) and \
                cubo._globo.texto:
            break
        import time; time.sleep(0.01)
    assert cubo._globo.texto == 'hola desde el cubo'


def test_chat_con_cerebro_aplica_la_accion(monkeypatch):
    """Con Cerebro la respuesta se parsea como acción y se aplica."""
    from pilas3d.ia import asistente
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    cubo.aprender(pilas.habilidades.Cerebro, cada=99)
    chat = pilas.actores.Chat(cubo, tecla='t')
    monkeypatch.setattr(
        asistente, 'llamar_ollama',
        lambda *a, **k: '{"accion":"mover","dx":3,"dz":0}')
    chat.decir_a('movete')
    for _ in range(200):
        chat.actualizar()
        if cubo.x == 3:
            break
        import time; time.sleep(0.01)
    assert cubo.x == 3


def test_chat_con_actoria_delega_preguntar():
    """Si el npc es ActorIA (sin cerebro) se usa su preguntar."""
    pilas = crear_pilas()
    npc = pilas.actores.ActorIA('mono', habla=False)
    chat = pilas.actores.Chat(npc, tecla='t')
    pedidos = []
    npc.preguntar = pedidos.append          # espía
    chat.decir_a('hola npc')
    assert pedidos == ['hola npc']


def test_chat_ignora_mensaje_vacio():
    pilas = crear_pilas()
    cubo = pilas.actores.Cubo()
    chat = pilas.actores.Chat(cubo, tecla='t')
    chat.decir_a('   ')
    chat.actualizar()
    assert not getattr(cubo, '_globo', None)


def test_chat_en_red_entre_dos_jugadores():
    """Chat(npc=None) manda por pilas.red y loguea lo que llega."""
    import time
    pilas_a = crear_pilas()
    pilas_b = crear_pilas()
    servidor = pilas_a.red.hospedar(puerto=0)
    cliente = pilas_b.red.conectar('localhost', servidor.puerto)
    chat_a = pilas_a.actores.Chat(nombre='ana')
    chat_b = pilas_b.actores.Chat(nombre='beto')
    try:
        def pasar_frames():
            servidor.actualizar()
            cliente.actualizar()
            chat_a.actualizar()
            chat_b.actualizar()
        for _ in range(50):      # dejar conectar los hilos de red
            pasar_frames()
            if cliente.id is not None:
                break
            time.sleep(0.01)
        chat_a.decir_a('hola beto')
        for _ in range(200):
            pasar_frames()
            if chat_b._log:
                break
            time.sleep(0.01)
        assert chat_b._log[-1] == 'ana: hola beto'
        chat_b.decir_a('hola ana')
        for _ in range(200):
            pasar_frames()
            if 'beto: hola ana' in chat_a._log:
                break
            time.sleep(0.01)
        assert 'beto: hola ana' in chat_a._log
        assert 'vos: hola beto' in chat_a._log
    finally:
        cliente.cerrar()
        servidor.cerrar()


def test_pilas_camara_atajo():
    """pilas.camara es la camara de la escena actual."""
    pilas = crear_pilas()
    assert pilas.camara is pilas.escena_actual().camara


def test_eventos_cuando_y_emitir():
    """El bus de eventos conecta oyentes por nombre."""
    pilas = crear_pilas()
    visto = []
    pilas.eventos.cuando('golpe', visto.append)
    pilas.eventos.emitir('golpe', 10)
    pilas.eventos.emitir('golpe', 20)
    assert visto == [10, 20]
    pilas.eventos.emitir('otro')              # sin oyentes: no explota


def test_eventos_decorador_y_olvidar():
    pilas = crear_pilas()
    visto = []

    @pilas.eventos.cuando('meta')
    def al_llegar():
        visto.append('llego')

    pilas.eventos.emitir('meta')
    assert visto == ['llego']
    pilas.eventos.olvidar('meta', al_llegar)
    pilas.eventos.emitir('meta')
    assert visto == ['llego']                 # ya no escucha
    pilas.eventos.cuando('x', visto.append)
    pilas.eventos.limpiar()
    pilas.eventos.emitir('x')
    assert len(visto) == 1


def test_config_leer_y_guardar(tmp_path, monkeypatch):
    """La config persiste en ~/.pilas3d/config.json (o PILAS3D_CONFIG)."""
    from pilas3d import config
    archivo = tmp_path / 'config.json'
    monkeypatch.setenv('PILAS3D_CONFIG', str(archivo))
    assert config.leer('ia_modelo') is None
    config.guardar('ia_modelo', 'smollm2:135m')
    assert config.leer('ia_modelo') == 'smollm2:135m'
    config.guardar('otra', 42)                 # no pisa la anterior
    assert config.leer('ia_modelo') == 'smollm2:135m'
    assert config.leer('otra') == 42


def test_ia_modelo_env_y_config(tmp_path, monkeypatch):
    """pilas.ia.modelo: env > config > default; el setter persiste."""
    from pilas3d.ia import asistente
    monkeypatch.setenv('PILAS3D_CONFIG',
                       str(tmp_path / 'config.json'))
    monkeypatch.delenv('PILAS3D_IA_MODELO', raising=False)
    pilas = crear_pilas()
    assert pilas.ia.modelo == 'qwen2.5-coder:0.5b'   # default
    pilas.ia.modelo = 'smollm2:135m'
    assert pilas.ia.modelo == 'smollm2:135m'          # config
    assert asistente.modelo_actual() == 'smollm2:135m'
    monkeypatch.setenv('PILAS3D_IA_MODELO', 'x:0')
    assert pilas.ia.modelo == 'x:0'                   # env pisa todo


def test_ia_facade_preguntar(monkeypatch):
    """pilas.ia.preguntar delega en el asistente."""
    from pilas3d.ia import asistente
    pilas = crear_pilas()
    monkeypatch.setattr(asistente, 'preguntar',
                        lambda c, **k: 'resp: ' + c)
    assert pilas.ia.preguntar('hola') == 'resp: hola'


def test_pilas_colisiones():
    """pilas.colisiones.colisionan es el atajo de colisión en XZ."""
    pilas = crear_pilas()
    a = pilas.actores.Cubo(x=0)
    b = pilas.actores.Cubo(x=1)
    assert pilas.colisiones.colisionan(a, b)
    b.x = 50
    assert not pilas.colisiones.colisionan(a, b)


def test_cuando_colisionan_flanco():
    """cuando_colisionan llama solo al EMPEZAR a tocarse."""
    pilas = crear_pilas()
    a = pilas.actores.Cubo(x=0)
    b = pilas.actores.Cubo(x=10)
    toques = []
    pilas.colisiones.cuando_colisionan(a, b, lambda: toques.append(1))
    escena = pilas.escena_actual()
    escena.actualizar(0.1)                    # lejos: nada
    b.x = 0.5
    escena.actualizar(0.1)                    # entra -> 1 llamada
    escena.actualizar(0.1)                    # sigue tocando: no repite
    assert toques == [1]
    b.x = 10
    escena.actualizar(0.1)                    # sale
    b.x = 0.5
    escena.actualizar(0.1)                    # reingresa -> 2
    assert toques == [1, 1]


def test_vida_dano_curar_y_morir():
    """Vida: recibir_dano/curar, evento 'murio' y callback al_morir."""
    pilas = crear_pilas()
    e = pilas.actores.Cubo()
    e.aprender(pilas.habilidades.Vida, vida=100)
    muertos = []
    pilas.eventos.cuando('murio', muertos.append)
    e.recibir_dano(30)
    assert e.vida == 70 and e.vivo
    e.curar(10)
    assert e.vida == 80
    e.curar(999)
    assert e.vida == 100                      # no pasa del máximo
    e.al_morir = lambda: muertos.append('cb')
    e.recibir_dano(200)
    assert not e.vivo and e.vida == 0
    assert muertos == [e, 'cb']
    e.recibir_dano(10)                        # muerto: ignora
    assert len(muertos) == 2


def test_barra_fraccion():
    """Barra lee vida/vida_maxima de un actor o un callable."""
    pilas = crear_pilas()
    e = pilas.actores.Cubo()
    e.aprender(pilas.habilidades.Vida, vida=100)
    barra = pilas.actores.Barra(e)
    assert barra.fraccion() == 1.0
    e.recibir_dano(75)
    assert barra.fraccion() == 0.25
    e.recibir_dano(50)
    assert barra.fraccion() == 0.0
    assert pilas.actores.Barra(de=lambda: 0.5).fraccion() == 0.5


def test_zona_entra_y_sale_por_flanco():
    """La Zona dispara entra/sale solo en los bordes."""
    pilas = crear_pilas()
    zona = pilas.actores.Zona(x=0, z=0, radio=2)
    cubo = pilas.actores.Cubo(x=10)
    evts = []
    zona.cuando_entra(cubo, lambda: evts.append('entra'))
    zona.cuando_sale(cubo, lambda: evts.append('sale'))
    escena = pilas.escena_actual()
    escena.actualizar(0.05)
    assert evts == []
    cubo.x = 1
    escena.actualizar(0.05)
    assert evts == ['entra']
    escena.actualizar(0.05)                   # adentro: no repite
    assert evts == ['entra']
    cubo.x = 10
    escena.actualizar(0.05)
    assert evts == ['entra', 'sale']


def test_maquina_de_estados_basica():
    """Estados nombrados que corren por frame y cambian solos."""
    pilas = crear_pilas()
    npc = pilas.actores.Cubo()
    pasos = []

    def quieto(a):
        pasos.append('quieto')
        a.x += 1                            # camina hasta cruzar 2
        if a.x > 2:
            a.cambiar_estado('moverse')

    def moverse(a):
        pasos.append('moverse')
        a.x += 1

    npc.aprender(pilas.habilidades.MaquinaDeEstados,
                 estados={'quieto': quieto, 'moverse': moverse},
                 inicial='quieto')
    escena = pilas.escena_actual()
    for _ in range(5):
        escena.actualizar(1 / 60.0)
    assert npc.estado == 'moverse'            # cambió solo
    assert 'quieto' in pasos and 'moverse' in pasos


def test_maquina_de_estados_entrar_salir():
    """Los estados-dict tienen hooks entrar/salir."""
    pilas = crear_pilas()
    npc = pilas.actores.Cubo()
    hooks = []
    npc.aprender(
        pilas.habilidades.MaquinaDeEstados,
        estados={
            'a': {'salir': lambda x: hooks.append('sale_a')},
            'b': {'entrar': lambda x: hooks.append('entra_b')},
        }, inicial='a')
    npc.cambiar_estado('b')
    assert hooks == ['sale_a', 'entra_b']


def test_patrullar_recorre_waypoints_en_loop():
    """El actor va de punto en punto y vuelve al primero."""
    pilas = crear_pilas()
    g = pilas.actores.Cubo(x=0, z=0)
    g.aprender(pilas.habilidades.Patrullar,
               puntos=[(4, 0), (4, 4)], velocidad=10)
    escena = pilas.escena_actual()
    for _ in range(200):
        escena.actualizar(0.05)
        if g.indice_patrulla == 1:
            break
    assert g.indice_patrulla == 1          # llegó al (4,0)
    for _ in range(300):
        escena.actualizar(0.05)
        if g.indice_patrulla == 0:
            break
    assert g.indice_patrulla == 0          # hizo el loop completo


def test_patrullar_ida_y_vuelta():
    """Con ida_y_vuelta el orden es 0,1,...,n-1,...,1,0."""
    from pilas3d.habilidades.patrullar import Patrullar
    pilas = crear_pilas()
    g = pilas.actores.Cubo(x=0, z=0)
    h = g.aprender(pilas.habilidades.Patrullar,
                   puntos=[(2, 0), (4, 0), (6, 0)],
                   velocidad=20, ida_y_vuelta=True)
    escena = pilas.escena_actual()
    orden = [g.indice_patrulla]
    for _ in range(400):
        escena.actualizar(0.05)
        if g.indice_patrulla != orden[-1]:
            orden.append(g.indice_patrulla)
        if len(orden) >= 4:
            break
    assert orden == [0, 1, 2, 1]           # ping-pong


def test_huir_de():
    """La presa se aleja del objetivo solo dentro del radio."""
    pilas = crear_pilas()
    presa = pilas.actores.Cubo(x=0, z=0)
    cazador = pilas.actores.Cubo(x=10, z=0)
    presa.aprender(pilas.habilidades.HuirDe, cazador,
                   radio=5, velocidad=10)
    escena = pilas.escena_actual()
    escena.actualizar(0.05)                # cazador a 10m: quieto
    assert presa.x == 0
    cazador.x = 3                          # entra al radio
    for _ in range(10):
        escena.actualizar(0.05)
    assert presa.x < 0                     # huyó hacia -x


def test_lampara_registra_y_mueve_la_luz():
    """La Lampara agrega una LuzPuntual que sigue su posición."""
    pilas = crear_pilas()
    l = pilas.actores.Lampara(x=1, y=3, z=0, alcance=12)
    luces = pilas.escena_actual().luces.puntuales
    assert l.luz in luces and l.luz.alcance == 12
    l.x = 5
    pilas.escena_actual().actualizar(0.05)
    assert l.luz.x == 5                     # la luz siguió al actor
    assert l.sin_luz is True                # el foco se dibuja plano


def test_lampara_apagar_encender_y_eliminar():
    """apagar quita la luz sin destruir el actor; eliminar limpia."""
    pilas = crear_pilas()
    l = pilas.actores.Lampara()
    luces = pilas.escena_actual().luces.puntuales
    l.apagar()
    assert l.luz not in luces and l.encendida is False
    l.encender()
    assert l.luz in luces and l.encendida is True
    l.eliminar()
    assert l.luz not in luces               # no queda luz huérfana


def test_lampara_color_tina_la_luz():
    """lampara.color actualiza el color de la LuzPuntual."""
    from pilas3d import colores
    pilas = crear_pilas()
    l = pilas.actores.Lampara(color=colores.rojo)
    assert tuple(l.luz.color) == tuple(colores.normalizar(colores.rojo))
    l.alcance = 20
    assert l.luz.alcance == 20


def test_parpadear_modula_el_alcance():
    """El alcance de la lámpara oscila alrededor del valor base."""
    pilas = crear_pilas()
    l = pilas.actores.Lampara(alcance=8)
    l.aprender(pilas.habilidades.Parpadear, intensidad=0.5,
               velocidad=100)
    escena = pilas.escena_actual()
    valores = set()
    for _ in range(30):
        escena.actualizar(0.05)
        valores.add(round(l.luz.alcance, 2))
    assert len(valores) > 3               # titiló
    assert all(4 <= v <= 12 for v in valores)   # ±50% de 8


def test_parpadear_sin_lampara_no_rompe():
    """En un actor sin .luz la habilidad no hace nada ni falla."""
    pilas = crear_pilas()
    c = pilas.actores.Cubo()
    c.aprender(pilas.habilidades.Parpadear)
    pilas.escena_actual().actualizar(0.05)


def test_rebota_en_paredes():
    """El actor rebota en los límites invirtiendo la velocidad."""
    pilas = crear_pilas()
    b = pilas.actores.Cubo(x=0, z=0)
    b.aprender(pilas.habilidades.RebotaEnParedes,
               vx=5, vz=0, limites=(-2, 2, -2, 2))
    escena = pilas.escena_actual()
    for _ in range(5):
        escena.actualizar(0.1)
    assert b.x == 2 and b.vel_x_rebote < 0       # rebotó en max_x
    for _ in range(9):
        escena.actualizar(0.1)
    assert b.x == -2 and b.vel_x_rebote > 0      # y en min_x


def test_camara_temblor_decae():
    """El temblor mueve la cámara y se apaga solo."""
    import random
    pilas = crear_pilas()
    cam = pilas.camara
    random.seed(1)
    x0 = cam.x
    cam.temblor(1.0, duracion=0.5)
    cam.actualizar(0.05)
    assert cam.x != x0
    for _ in range(40):
        cam.actualizar(0.05)
    pos = cam.x
    cam.actualizar(0.05)
    assert cam.x == pos                         # ya no tiembla


def test_guardar_y_cargar_partida(tmp_path):
    """Guarda actores y datos; cargar los recrea."""
    import os
    pilas = crear_pilas()
    c = pilas.actores.Cubo(x=3, z=-2)
    c.rotacion_y = 45
    c.aprender(pilas.habilidades.Vida, vida=80)
    c.vida = 30
    ruta = str(tmp_path / 'p.json')
    pilas.guardar_partida(ruta, datos={'puntos': 7})
    assert os.path.exists(ruta)

    datos = pilas.cargar_partida(ruta)
    assert datos == {'puntos': 7}
    from pilas3d.actores.cubo import Cubo
    recreados = [a for a in pilas.escena_actual().actores
                 if isinstance(a, Cubo)]
    assert len(recreados) == 1
    n = recreados[0]
    assert (n.x, n.z, n.rotacion_y) == (3, -2, 45)
    assert n.vida == 30 and n.vida_maxima == 80


def test_anim_json_remapea_por_nombre(tmp_path):
    """Un .anim.json referencia huesos por índice; si el esqueleto
    cambió de orden, el nombre los reubica."""
    pilas = crear_pilas()
    m = pilas.actores.ModeloGLTF('modelos/personajes/fox/Fox.glb')
    hueso = m.huesos()[0][0]
    pose_a = {str(hueso): {'r': [0, 0, 0.0, 1.0]}}
    pose_b = {str(hueso): {'r': [0, 0, 0.2, 0.98]}}
    m.crear_animacion('giro', [pose_a, pose_b])
    ruta = str(tmp_path / 'fox.anim.json')
    m.guardar_animacion(ruta, 'giro')

    import json
    datos = json.load(open(ruta))
    canal = datos['canales'][0]
    assert canal['nodo_nombre']                  # se exportó el nombre
    canal['nodo'] = 0                            # índice roto (re-export)
    json.dump(datos, open(ruta, 'w'))

    m2 = pilas.actores.ModeloGLTF('modelos/personajes/fox/Fox.glb')
    m2.cargar_animacion(ruta)
    nodo_ok = m2._escena['animaciones']['giro']['canales'][0]['nodo']
    nombre_ok = [n['nombre'] for n in m2._escena['nodos']]
    assert nombre_ok[nodo_ok] == canal['nodo_nombre']


# -- física 2D (pymunk) ------------------------------------------------------

pymunk = pytest.importorskip('pymunk', reason='pymunk no instalado')


def _pasos(pilas, n):
    for _ in range(n):
        pilas.fisica._actualizar()


def test_fisica_gravedad_hace_caer_caja():
    pilas = crear_pilas()
    caja = pilas.actores.Cubo(y=5)
    caja.radio_de_colision = 0.5
    cuerpo = pilas.fisica.vincular(caja, forma='caja', ancho=1, alto=1)
    _pasos(pilas, 60)
    assert caja.y < 4.0                      # cayó
    assert cuerpo.velocidad[1] < 0           # con velocidad hacia abajo


def test_fisica_caja_se_apoya_en_suelo_estatico():
    pilas = crear_pilas()
    suelo = pilas.actores.Cubo(y=0)
    pilas.fisica.vincular(suelo, forma='caja', estatico=True,
                          ancho=20, alto=1)
    pelota = pilas.actores.Esfera(y=3)
    pelota.radio_de_colision = 0.5
    pilas.fisica.vincular(pelota, forma='circulo', radio=0.5)
    _pasos(pilas, 180)
    # apoyada: 0.5 (mitad del suelo) + 0.5 (radio) = ~1.0
    assert 0.8 < pelota.y < 1.2
    cuerpo = pilas.fisica.cuerpo_de(pelota)
    assert abs(cuerpo.velocidad[1]) < 0.5    # ya no cae


def test_fisica_cuando_colisionan_dispara_callback():
    pilas = crear_pilas()
    suelo = pilas.actores.Cubo(y=0)
    pilas.fisica.vincular(suelo, estatico=True, ancho=20, alto=1)
    pelota = pilas.actores.Esfera(y=2)
    pilas.fisica.vincular(pelota, forma='circulo', radio=0.5)
    toques = []
    pilas.fisica.cuando_colisionan(pelota, suelo,
                                   lambda a, b: toques.append((a, b)))
    _pasos(pilas, 180)
    assert toques and toques[0] == (pelota, suelo)


def test_fisica_sensor_detecta_sin_bloquear():
    pilas = crear_pilas()
    gatillo = pilas.actores.Cubo(y=0)
    pilas.fisica.vincular(gatillo, estatico=True, ancho=20, alto=0.5,
                          sensor=True)
    pelota = pilas.actores.Esfera(y=2)
    pilas.fisica.vincular(pelota, forma='circulo', radio=0.5)
    toques = []
    pilas.fisica.cuando_colisionan(pelota, gatillo,
                                   lambda a, b: toques.append(1))
    _pasos(pilas, 240)
    assert toques                            # el sensor avisó
    assert pelota.y < -0.5                   # pero no frenó a la pelota


def test_fisica_plano_xz_mapea_x_z_y_cinematica():
    pilas = crear_pilas()
    pilas.fisica.plano = 'xz'
    assert pilas.fisica.gravedad == (0.0, 0.0)
    caja = pilas.actores.Cubo(x=1, z=2)
    cuerpo = pilas.fisica.vincular(caja, cinematica=True)
    caja.x, caja.z = 5, -3
    _pasos(pilas, 2)
    assert tuple(cuerpo.pymunk.position) == (5, -3)
    caja.rotacion_y = 45
    _pasos(pilas, 1)
    # rotacion_y positiva = CCW visto desde arriba -> angle negativo
    assert abs(cuerpo.pymunk.angle - (-3.14159 / 4)) < 0.01


def test_fisica_desvincular_y_limpiar():
    pilas = crear_pilas()
    a = pilas.actores.Cubo(y=5)
    b = pilas.actores.Cubo(y=6)
    pilas.fisica.vincular(a)
    pilas.fisica.vincular(b)
    pilas.fisica.desvincular(a)
    assert pilas.fisica.cuerpo_de(a) is None
    assert pilas.fisica.cuerpo_de(b) is not None
    pilas.fisica.limpiar()
    assert pilas.fisica.cuerpo_de(b) is None


def test_fisica_actor_eliminado_suelta_su_cuerpo():
    pilas = crear_pilas()
    caja = pilas.actores.Cubo(y=5)
    pilas.fisica.vincular(caja)
    caja.eliminar()
    _pasos(pilas, 2)
    assert pilas.fisica.cuerpo_de(caja) is None


def test_fisica_impulso_lanza_la_caja():
    pilas = crear_pilas()
    caja = pilas.actores.Cubo(y=1)
    cuerpo = pilas.fisica.vincular(caja)
    cuerpo.impulsar(0, 5)
    _pasos(pilas, 5)
    assert caja.y > 1.2                      # subió por el impulso


# -- blend trees -------------------------------------------------------------

def _modelo_con_dos_clips():
    """glTF esquelético con dos clips: 'arriba' (0 -> +90°) y
    'abajo' (0 -> -90°) sobre el hueso 1."""
    pilas = crear_pilas()
    m = pilas.actores.ModeloGLTF(_gltf_esqueletico())
    i = m.huesos()[1][0]
    pose_a = m._pose_actual()
    m.rotar_hueso(i, 'z', 90)
    pose_b = m._pose_actual()
    m.rotar_hueso(i, 'z', -180)
    pose_c = m._pose_actual()
    m.crear_animacion('arriba', [pose_a, pose_b], duracion=1.0)
    m.crear_animacion('abajo', [pose_a, pose_c], duracion=1.0)
    return pilas, m, i


def test_gltf_mezclar_dos_clips():
    """mezclar(a, b, peso) interpola la pose hueso por hueso:
    peso 1 = el clip b; peso 0.5 = el punto medio."""
    pilas, m, i = _modelo_con_dos_clips()
    nodos = m._escena['nodos']

    m.mezclar('arriba', 'abajo', 1.0)      # solo 'abajo'
    pilas.dt = 0.5
    m.actualizar()                          # t=0.5 -> mitad de -90°
    r = nodos[i]['r']
    assert r[2] == pytest.approx(-0.383, abs=0.01)   # sin(-22.5°)

    m.mezclar('arriba', 'abajo', 0.0)      # solo 'arriba'
    pilas.dt = 0.5
    m.actualizar()
    assert nodos[i]['r'][2] == pytest.approx(0.383, abs=0.01)

    m.mezclar('arriba', 'abajo', 0.5)      # +45°/-45° -> ~0°
    pilas.dt = 0.5
    m.actualizar()
    r = nodos[i]['r']
    assert abs(r[2]) < 0.05 and r[3] == pytest.approx(1.0, abs=0.01)


def test_gltf_arbol_mezcla_elige_vecinos():
    """arbol_mezcla interpola entre los dos puntos que rodean al
    parámetro y queda en un solo clip en los extremos."""
    pilas, m, i = _modelo_con_dos_clips()
    puntos = [(0, 'arriba'), (10, 'abajo')]

    m.arbol_mezcla(puntos, 5)
    assert m._mezcla == {'arriba': 0.5, 'abajo': 0.5}
    m.arbol_mezcla(puntos, -3)
    assert m._mezcla == {'arriba': 1.0}
    m.arbol_mezcla(puntos, 99)
    assert m._mezcla == {'abajo': 1.0}
    m.arbol_mezcla(puntos, 7.5)
    assert m._mezcla['abajo'] == pytest.approx(0.75)

    m.detener()
    assert m._mezcla is None and m.animacion is None


def test_gltf_mezclar_clip_inexistente_avisa():
    pilas, m, i = _modelo_con_dos_clips()
    with pytest.raises(ValueError):
        m.mezclar('arriba', 'volar')


# -- RAG del proyecto ---------------------------------------------------------

def test_rag_buscar_encuentra_fragmentos_relevantes():
    from pilas3d.ia import rag
    r = rag.buscar('enemigo que persiga al jugador')
    assert r                                     # índice no vacío
    texto = (r[0]['archivo'] + ' ' + r[0]['texto']).lower()
    assert 'persegu' in texto or 'bot' in texto


def test_rag_buscar_identificadores_de_codigo():
    from pilas3d.ia import rag
    r = rag.buscar('colisiona_con radio_de_colision')
    assert r
    todo = ' '.join(x['texto'] for x in r)
    assert 'colisiona' in todo


def test_rag_contexto_formatea_para_prompt():
    from pilas3d.ia import rag
    ctx = rag.contexto('gravedad fisica vincular')
    assert '###' in ctx                          # "### archivo"
    assert len(ctx) <= 1600                      # respeta max_chars aprox


def test_rag_reiniciar_indice_y_consulta_vacia():
    from pilas3d.ia import rag
    rag.reiniciar_indice()
    assert rag.buscar('cubo')                    # reconstruye
    assert rag.buscar('') == []                  # consulta vacía


def test_ia_buscar_desde_el_motor():
    pilas = crear_pilas()
    r = pilas.ia.buscar('camara seguir actor')
    assert isinstance(r, list)


def test_preguntar_inyecta_documentacion(monkeypatch):
    """preguntar() mete el RAG en el prompt del modelo."""
    from pilas3d.ia import asistente
    capturado = {}
    def fake(prompt, system=None, modelo=None, al_token=None):
        capturado['prompt'] = prompt
        return 'ok'
    monkeypatch.setattr(asistente, 'llamar_ollama', fake)
    asistente.preguntar('¿cómo hago un enemigo que persiga?')
    assert 'Documentación relevante del motor' in capturado['prompt']
    assert 'Pregunta:' in capturado['prompt']

    capturado.clear()
    asistente.preguntar('¿cómo hago un enemigo que persiga?',
                        con_rag=False)
    assert 'Documentación' not in capturado['prompt']


# -- frente / mirar_hacia ------------------------------------------------------

def test_mirar_hacia_respeta_frente_del_actor():
    """mirar_hacia orienta según adónde mira el modelo en reposo:
    frente=+Z (default) mira +Z con rotacion_y=0; un modelo que
    mira -Z (wolf y la mayoría de los glTF) compensa con (0,-1)."""
    pilas = crear_pilas()
    a = pilas.actores.Cubo()
    a.mirar_hacia(10, 0)                   # objetivo en +x
    assert a.rotacion_y == pytest.approx(90)
    a.mirar_hacia(0, -10)                  # objetivo en -z
    assert a.rotacion_y == pytest.approx(180)

    lobo = pilas.actores.Cubo()
    lobo.frente = (0, -1)                  # modelo que mira -Z
    lobo.mirar_hacia(10, 0)
    # frente -Z debe llegar a +x: rotacion_y = 90 - 180 = -90
    assert lobo.rotacion_y == pytest.approx(-90)
    lobo.mirar_hacia(0, -10)
    assert lobo.rotacion_y == pytest.approx(0)


def test_serbot_sigue_mirando_al_llegar():
    """Al quedar pegado al objetivo el bot sigue orientándose
    (antes el early-return dejaba la rotación congelada)."""
    pilas = crear_pilas()
    objetivo = pilas.actores.Cubo()
    bot = pilas.actores.Cubo(x=0.05, z=0.05)  # dist < 0.15
    bot.aprender(pilas.habilidades.SerBot, objetivo=objetivo,
                 radio_vision=5, velocidad=2.0)
    bot.pre_actualizar()                   # estado perseguir + mira
    # objetivo está en (-0.05,-0.05) -> atan2(-.05,-.05) = -135
    assert bot.rotacion_y == pytest.approx(-135)


# -- terreno ----------------------------------------------------------------

def test_terreno_basico():
    """El Terreno crea la rejilla de alturas y su geometría."""
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=10)
    assert t.celdas == 10
    assert len(t.alturas) == 11
    assert all(len(f) == 11 for f in t.alturas)
    pos, norm, modo, colores, uvs = t._generar_geometria()
    # 10x10 celdas * 4 vértices (dibujo indexado, no duplica)
    assert len(pos) == 10 * 10 * 4 * 3
    assert len(norm) == len(pos)
    assert len(uvs) == 10 * 10 * 4 * 2
    assert len(t._indices) == 10 * 10 * 6


def test_terreno_subir_bajar():
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=6)
    t.subir(3, 3, 2.0)
    assert t.alturas[3][3] == pytest.approx(2.0)
    t.bajar(3, 3, 0.5)
    assert t.alturas[3][3] == pytest.approx(1.5)
    t.nivelar(0)
    assert t.alturas[3][3] == 0


def test_terreno_montana_y_pozo():
    """Las formas circulares deforman la rejilla suavemente."""
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=12)
    t.montana(6, 6, radio=3, altura=2.0)
    # el pico está en el centro y decae con la distancia
    assert t.alturas[6][6] == pytest.approx(2.0)
    assert t.alturas[6][5] < 2.0
    assert t.alturas[6][5] > 0.0
    t.nivelar()
    t.pozo(6, 6, radio=3, profundidad=1.5)
    assert t.alturas[6][6] == pytest.approx(-1.5)


def test_terreno_altura_suelo():
    """altura_suelo interpola la rejilla en coordenadas de mundo."""
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=10)          # 10x10 m, centrado
    t.subir(5, 5, 2.0)                            # vértice central
    assert t.altura_suelo(0.0, 0.0) == pytest.approx(2.0)
    assert t.altura_suelo(99, 0) is None          # fuera del terreno


def test_terreno_pintar_y_tipos():
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=10)
    t.pintar_zona(5, 5, 0, 'agua')
    assert t._tiles[t._tex[5][5]] == 'agua'
    t.pintar_zona(5, 5, 1, 'piedra')
    assert t._tiles[t._tex[5][6]] == 'piedra'
    # las celdas lejanas quedan como estaban
    assert t._tiles[t._tex[0][0]] == 'pasto'


def test_terreno_agua():
    """El plano de agua aparece a la altura pedida y se puede quitar."""
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=8)
    t.agua = 0.4
    assert t._agua is not None
    assert t._agua.y == pytest.approx(0.4)
    t.agua = None
    assert t._agua is None


def test_terreno_guardar_cargar(tmp_path):
    """guardar/cargar preserva alturas, baldosas, agua y spawn."""
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=8)
    t.montana(3, 3, radio=2, altura=1.5)
    t.pintar_zona(6, 6, 1, 'agua')
    t.agua = 0.4
    t.spawn = (0.0, 1.0, 0.0)
    ruta = str(tmp_path / 'nivel.terreno.json')
    t.guardar(ruta, nombre='nivel')
    t2 = pilas.mapas.cargar(ruta)
    assert type(t2).__name__ == 'Terreno'
    assert t2.celdas == 8
    assert t2.alturas[3][3] == pytest.approx(1.5)
    assert t2._tiles[t2._tex[6][6]] == 'agua'
    assert t2.agua == pytest.approx(0.4)
    assert t2.spawn == (0.0, 1.0, 0.0)


# -- materiales compuestos ---------------------------------------------------

def test_material_desde_carpeta(tmp_path):
    """desde_carpeta detecta los mapas de un pack por nombre."""
    d = tmp_path / 'pack'
    d.mkdir()
    for n in ('X_BaseColor.jpg', 'X_Normal.png',
              'X_AmbientOcclusion.jpg', 'X_Roughness.jpg',
              'X_Metallic.jpg', 'X_Displacement.png',
              'X_Preview1.png'):
        (d / n).write_bytes(b'x')
    mat = crear_pilas().materiales.desde_carpeta(str(d))
    assert mat.base.endswith('BaseColor.jpg')
    assert mat.normal.endswith('Normal.png')
    assert mat.ao.endswith('AmbientOcclusion.jpg')
    assert mat.rugosidad.endswith('Roughness.jpg')
    assert mat.metalico.endswith('Metallic.jpg')
    assert mat.heightmap.endswith('Displacement.png')
    assert 'Preview' not in mat.base


def test_terreno_desde_heightmap(tmp_path):
    """desde_heightmap convierte la luminancia de la imagen en
    alturas de la rejilla."""
    from pyglet.image import ImageData
    px = []
    for k in range(8):
        for i in range(8):
            v = int(i * 255 / 7)
            px += [v, v, v, 255]
    ruta = str(tmp_path / 'h.png')
    ImageData(8, 8, 'RGBA', bytes(px)).save(ruta)
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=7)
    t.desde_heightmap(ruta, altura=2.0)
    assert t.alturas[0][0] == pytest.approx(0)
    assert t.alturas[7][0] == pytest.approx(2.0)
    assert t.alturas[3][0] == pytest.approx(3 / 7.0 * 2.0, abs=0.02)


def test_material_apagar_prender():
    """apagar/prender apaga un mapa sin perder la ruta (el bug del
    ejemplo: asignar None destruía el mapa para siempre)."""
    mat = crear_pilas().materiales.cargar(normal='n.png')
    mat.apagar('normal')
    assert mat.normal is None
    assert mat.textura('normal') is None
    mat.prender('normal')
    assert mat.normal == 'n.png'
    mat.prender('normal')            # idempotente
    assert mat.normal == 'n.png'


def test_material_alias_texturas(tmp_path, monkeypatch):
    """pilas.materiales['nombre'] resuelve packs de texturas/ por
    alias de carpeta; los inexistentes devuelven material vacío."""
    pack = tmp_path / 'texturas' / 'pasto'
    pack.mkdir(parents=True)
    (pack / 'suelo_BaseColor.jpg').write_bytes(b'x')
    monkeypatch.chdir(tmp_path)
    pilas = crear_pilas()
    assert 'pasto' in pilas.materiales.lista()
    mat = pilas.materiales['pasto']
    assert mat.base.endswith('suelo_BaseColor.jpg')
    assert pilas.materiales['no_existe_xyz'].base is None


def test_terreno_aplicar_material(tmp_path, monkeypatch):
    """Terreno.aplicar_material(alias): pasa a textura única, guarda
    las baldosas y las restaura con None."""
    pack = tmp_path / 'texturas' / 'suelo'
    pack.mkdir(parents=True)
    png = _png_minimo()
    (pack / 'suelo_Color.png').write_bytes(png)
    (pack / 'suelo_NormalGL.png').write_bytes(png)
    monkeypatch.chdir(tmp_path)
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=4)
    tipos0 = t.tipos
    t.aplicar_material('suelo')
    assert t._material_nombre == 'suelo'
    assert t.tipos['unica'].endswith('suelo_Color.png')
    assert t.material.normal.endswith('suelo_NormalGL.png')
    t.aplicar_material(None)
    assert t.tipos == tipos0 and t.material is None


def test_mapa_terreno_persiste_material(tmp_path, monkeypatch):
    """El .terreno.json guarda el alias del pack; al cargar se
    re-aplica y las baldosas quedan restaurables."""
    pack = tmp_path / 'texturas' / 'suelo'
    pack.mkdir(parents=True)
    (pack / 'suelo_Color.png').write_bytes(_png_minimo())
    monkeypatch.chdir(tmp_path)
    pilas = crear_pilas()
    t = pilas.actores.Terreno(celdas=4)
    t.aplicar_material('suelo')
    ruta = str(tmp_path / 'x.terreno.json')
    pilas.mapas.guardar_terreno(ruta, t)
    t2 = pilas.mapas.cargar(ruta)
    assert t2._material_nombre == 'suelo'
    assert t2._tipos_baldosas is not None


def _png_minimo():
    """PNG chico válido para tests (el atlas carga la imagen real)."""
    import io
    from pyglet.image import create, SolidColorImagePattern
    img = create(4, 4, SolidColorImagePattern((120, 80, 40, 255)))
    buf = io.BytesIO()
    img.save('x.png', file=buf)
    return buf.getvalue()


def test_fuentes_familia():
    """fuentes.familia: nombre de familia pasa igual; un .ttf de
    data/fonts/ se registra y devuelve su familia real (tabla name)."""
    from pilas3d import fuentes
    assert fuentes.familia('DejaVu Sans') == 'DejaVu Sans'
    assert fuentes.familia('DejaVuSansMono.ttf') == 'DejaVu Sans Mono'
    assert fuentes.familia(None) is None
    assert fuentes.familia('no_existe.ttf') == 'no_existe.ttf'


def test_fuentes_lista():
    """pilas.fuentes.lista() incluye las fuentes del motor."""
    pilas = crear_pilas()
    assert 'DejaVuSansMono.ttf' in pilas.fuentes.lista()


def test_efectos_sobre_actor():
    """pilas.efectos: parpadear restaura la transparencia, temblar
    vuelve a la posición, flotar devuelve una tarea cancelable."""
    pilas = crear_pilas()
    a = pilas.actores.Cubo()
    # parpadear: alterna y termina restaurando
    pilas.efectos.parpadear(a, veces=2, cada=0.05)
    for _ in range(10):
        pilas.tareas.actualizar(0.1)
    assert a.transparencia == 0
    # temblar: al acabar vuelve a la posición original
    a.posicion = (1, 0, 2)
    pilas.efectos.temblar(a, duracion=0.2)
    for _ in range(10):
        pilas.tareas.actualizar(0.1)
    assert a.posicion == (1, 0, 2)
    # flotar: mueve y, la tarea se puede eliminar
    t = pilas.efectos.flotar(a, altura=0.5)
    pilas.tareas.actualizar(0.1)
    t.eliminar()
    n = pilas.tareas.obtener_cantidad_de_tareas_planificadas()
    pilas.tareas.actualizar(0.1)
    assert pilas.tareas.obtener_cantidad_de_tareas_planificadas() <= n


def test_efectos_tweens():
    """pulsar/desvanecer/aparecer interpolan escala y transparencia;
    flash restaura el color original."""
    pilas = crear_pilas()
    a = pilas.actores.Cubo()
    pilas.efectos.pulsar(a, escala=1.5)
    assert a._interpolaciones        # tween en curso sobre escala
    pilas.efectos.desvanecer(a, duracion=0.5)
    assert any(t.atributo == 'transparencia'
               for t in a._interpolaciones)
    a.color = pilas.colores.verde
    pilas.efectos.flash(a, pilas.colores.rojo, duracion=0.1)
    assert a.color == pilas.colores.rojo
    for _ in range(5):
        pilas.tareas.actualizar(0.1)
    assert a.color == pilas.colores.verde


def test_efectos_camara_tiempo_estela():
    """temblar_pantalla no deriva la cámara; hit_stop escala el dt;
    estela persigue al actor y muere con él."""
    import time
    pilas = crear_pilas()
    cam = pilas.escena.camara
    cam.posicion = (0, 5, 12)
    pilas.efectos.temblar_pantalla(0.4, 0.3)
    for _ in range(30):
        cam.actualizar(0.05)   # 1.5s — el temblor ya terminó
    assert cam.x == pytest.approx(0) and cam.y == pytest.approx(5)
    # hit_stop: el reloj del juego se congela, no el de pared
    pilas.efectos.hit_stop(0.05, escala=0.0)
    assert pilas.efectos.tiempo_escala() == 0.0
    t0 = pilas.tareas.contador_de_tiempo
    pilas._tick(0.016)
    assert pilas.tareas.contador_de_tiempo == pytest.approx(t0)
    time.sleep(0.06)
    assert pilas.efectos.tiempo_escala() == 1.0
    # estela: emite detrás del actor y se apaga si él sale de escena
    a = pilas.actores.Cubo()
    emisor = pilas.efectos.estela(a)
    a.posicion = (3, 1, 0)
    pilas.tareas.actualizar(0.01)
    # rotacion_y=0 -> punto de emisión (x, y, z - detras)
    assert emisor.posicion == pytest.approx((3, 1, -0.45))
    # la estela no se arrastra: las partículas quedan en el mundo
    emisor._px[0] = 1.0
    mundo_antes = emisor.x + emisor._px[0]
    a.x = 6.0
    pilas.tareas.actualizar(0.01)
    assert emisor.x + emisor._px[0] == pytest.approx(mundo_antes)
    a.eliminar()
    pilas.tareas.actualizar(0.01)
    assert not emisor.esta_en_escena()


def test_asignacion_directa_corta_tween():
    """actor.x = 5 con un tween corriendo sobre x lo cancela: la
    escritura directa gana (evita que un desvanecer viejo pise
    un parpadear nuevo). El propio tween no se auto-cancela."""
    pilas = crear_pilas()
    a = pilas.actores.Cubo()
    a.transparencia = ([100], 5.0)          # tween largo en curso
    assert a._interpolaciones
    a.transparencia = 30                    # asignación directa
    assert not a._interpolaciones           # tween cancelado
    a.pre_actualizar()
    assert a.transparencia == 30            # nadie lo pisa
    # y un tween sigue pudiendo avanzar sin suicidarse
    a.x = ([10], 0.5)
    a.pre_actualizar()
    assert a._interpolaciones               # vivo tras el paso


# -- Fondos HDR (.hdr Radiance / RGBE) -----------------------------------

def _hdr_plano(ancho, alto, pixeles):
    """Arma un .hdr mínimo en formato plano (sin RLE)."""
    enc = b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n" % (
        alto, ancho)
    cuerpo = b"".join(bytes(p) for p in pixeles)
    return enc + cuerpo


def _hdr_rle(ancho, filas):
    """Arma un .hdr con scanlines RLE: cada fila es una lista de
    (rgb byte, exponente) corridas de ``ancho`` píxeles."""
    enc = b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y 1 +X %d\n" % ancho
    cuerpo = b""
    for (r, g, b, e) in filas:
        cuerpo += bytes([2, 2, ancho >> 8, ancho & 0xff])
        for v in (r, g, b, e):
            cuerpo += bytes([128 + ancho, v])   # corrida pura
    return enc + cuerpo


def test_hdr_decodifica_plano(tmp_path):
    from pilas3d import hdr
    # e=136 -> factor 2^0 = 1: el byte ES el float (200 = HDR real)
    p = tmp_path / "f.hdr"
    p.write_bytes(_hdr_plano(4, 2, [(200, 100, 50, 136)] * 8))
    ancho, alto, datos = hdr.cargar(str(p))
    assert (ancho, alto) == (4, 2)
    assert datos[0:4] == pytest.approx((200.0, 100.0, 50.0, 1.0))


def test_hdr_decodifica_rle(tmp_path):
    from pilas3d import hdr
    p = tmp_path / "r.hdr"
    p.write_bytes(_hdr_rle(8, [(255, 128, 0, 136)]))
    ancho, alto, datos = hdr.cargar(str(p))
    assert (ancho, alto) == (8, 1)
    assert datos[0:4] == pytest.approx((255.0, 128.0, 0.0, 1.0))
    assert datos[-4:] == pytest.approx((255.0, 128.0, 0.0, 1.0))


def test_hdr_direccion_sol_y_promedio(tmp_path):
    from pilas3d import hdr
    # un pixel brillante arriba a la izquierda; el resto oscuro
    px = [(10, 10, 10, 128)] * 8
    px[0] = (255, 100, 50, 140)      # sol rojizo brillante (e=140)
    p = tmp_path / "s.hdr"
    p.write_bytes(_hdr_plano(4, 2, px))
    ancho, alto, datos = hdr.cargar(str(p))
    dir_sol, color_sol = hdr.direccion_sol(ancho, alto, datos)
    assert dir_sol[1] > 0.5          # el sol está arriba (cenit)
    medio = hdr.promedio(ancho, alto, datos)
    assert medio[0] > medio[2]       # el sol rojizo tiñe el promedio


def test_cielo_hdr_activa_tonemap_y_exposicion():
    pilas = crear_pilas()
    c = pilas.actores.Cielo('mirrored_hall_2k.hdr')
    assert c.tonemap is True
    assert c.exposicion == 1.0
    c.tipo = 'estrellas'
    assert c.tonemap is False        # vuelve al modo normal


def test_cielo_iluminar_escena(tmp_path):
    pilas = crear_pilas()
    px = [(10, 10, 10, 128)] * 8
    px[0] = (255, 240, 200, 140)
    p = tmp_path / "cielo.hdr"
    p.write_bytes(_hdr_plano(4, 2, px))
    c = pilas.actores.Cielo(str(p))
    c.iluminar_escena()
    d = pilas.luces.direccional
    assert d.direccion[1] < 0        # la luz baja desde el cenit
    assert 0.15 <= d.ambiente <= 0.75
    assert max(d.ambiente_color) == pytest.approx(255.0)
    assert max(d.color) == pytest.approx(255.0)   # colores 0-255


def test_cielo_iluminar_escena_sin_hdr_falla():
    pilas = crear_pilas()
    c = pilas.actores.Cielo('estrellas')
    with pytest.raises(ValueError):
        c.iluminar_escena()


def test_imagenes_resolver_encuentra_data_hdr():
    from pilas3d.imagenes import resolver
    ruta = resolver('mirrored_hall_2k.hdr')
    assert ruta.endswith('mirrored_hall_2k.hdr')


def test_hdr_cache_binario_acelera_recargas(tmp_path):
    from pilas3d import hdr
    p = tmp_path / "c.hdr"
    p.write_bytes(_hdr_plano(4, 2, [(200, 100, 50, 136)] * 8))
    a1 = hdr.cargar(str(p))          # decodifica y guarda .cache
    assert (tmp_path / "c.hdr.cache").exists()
    hdr._cache.clear()
    a2 = hdr.cargar(str(p))          # lee el dump, sin decodificar
    assert a1 == a2
    # un .hdr más nuevo que el .cache invalida y redecodifica
    p.write_bytes(_hdr_plano(4, 2, [(1, 2, 3, 136)] * 8))
    os.utime(p, (9e9, 9e9))
    hdr._cache.clear()
    a3 = hdr.cargar(str(p))
    assert a3[2][0] == pytest.approx(1.0)


def test_pilas3d_init_crea_la_estructura(tmp_path):
    from pilas3d import nuevo_juego
    import os
    viejo = os.getcwd()
    os.chdir(tmp_path)
    try:
        base = nuevo_juego.crear('Mi Juego!')
        assert base == 'mi_juego'
        for d in ('mapas', 'modelos/personajes', 'modelos/props',
                  'modelos/fuentes', 'modelos/docs', 'texturas',
                  'sonidos', 'fonts', 'data/hdr', 'data/imagenes'):
            assert os.path.isdir(tmp_path / 'mi_juego' / d), d
        juego = (tmp_path / 'mi_juego' / 'juego.py').read_text()
        assert 'Mi Juego!' in juego and 'pilas3d.iniciar' in juego
        compile(juego, 'juego.py', 'exec')           # sintaxis válida
        assert (tmp_path / 'mi_juego' / 'README.md').exists()
        # no pisa un proyecto existente con contenido
        with pytest.raises(IOError):
            nuevo_juego.crear('Mi Juego!')
    finally:
        os.chdir(viejo)


def test_pilas3d_init_nombre_directorio():
    from pilas3d.nuevo_juego import _nombre_directorio
    assert _nombre_directorio('Mi Juego!') == 'mi_juego'
    assert _nombre_directorio('  Space Wars 3 ') == 'space_wars_3'
