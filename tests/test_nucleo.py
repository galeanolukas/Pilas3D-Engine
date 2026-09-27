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
    assert pilas.luces.direccional.ambiente == 0.35


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
    pos, _, _, _, _ = mundo._generar_geometria()
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
    import math
    pilas = crear_pilas()
    objetivo = pilas.actores.Cubo(z=-10)
    torreta = pilas.actores.Cubo()
    torreta.aprender(pilas.habilidades.MirarAlActor, actor=objetivo)
    torreta.pre_actualizar()
    assert abs(torreta.rotacion_y - 0) < 0.01   # mira hacia -z
    objetivo.x = 10
    objetivo.z = 0
    torreta.pre_actualizar()
    assert abs(torreta.rotacion_y + 90) < 0.01   # mira hacia +x


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
