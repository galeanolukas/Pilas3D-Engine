# -*- encoding: utf-8 -*-
"""pilas3d: motor de videojuegos 3D simple, en español.

Inspirado en pilas-engine 1.x (Hugo Ruscitti, LGPLv3): mantiene la API
didáctica (``pilas.actores``, ``pilas.escenas``, ``pilas.ejecutar()``)
pero reemplaza el render QPainter 2D por OpenGL vía pyglet.

Uso básico::

    import pilas3d

    pilas = pilas3d.iniciar()
    cubo = pilas.actores.Cubo()
    pilas.ejecutar()
"""

import os

import pyglet

from pilas3d import colores
from pilas3d.actores import Actores
from pilas3d.control import Control, ControlNulo
from pilas3d.escenas import Escenas
from pilas3d.habilidades import Habilidades
from pilas3d.depurador import Depurador
from pilas3d.sonidos import Sonidos
from pilas3d.musica import _Musica
from pilas3d import interpolaciones

VERSION = "0.1.0"

AYUDA = """\
pilas3d - guía rápida
=====================

Arranque
    pilas = pilas3d.iniciar()          # abre la ventana
    pilas.ayuda()                      # este texto
    pilas.ejecutar()                   # bucle de juego (bloquea)
    pilas.paso()                       # un frame (modo interactivo)
    pilas.terminar()                   # cierra todo

Actores  (posición x/y/z, rotacion_x/y/z, escala, color, imagen)
    pilas.actores.Cubo()  Esfera(radio=1)  Pared(ancho, alto, profundidad)
    pilas.actores.Piso()  Plano(ancho, profundidad)  Ejes(largo)
    pilas.actores.Cartel(ancho, alto)      # sprite que mira a la cámara
    pilas.actores.Animacion('x.png', columnas=8, velocidad=10)
    pilas.actores.Mapa(texto, {'#': constructor, 'E': otro})
    pilas.actores.Texto('hola')  Puntaje(prefijo='Puntos: ')
    pilas.actores.Modelo('modelos/arbol.obj', escala=0.1)  # archivo .obj

Cada actor
    actor.x = 3      actor.rotacion_y = 45    actor.escala = 2
    actor.imagen = 'caja.png'                # textura
    actor.eliminar()  actor.actualizar()     # se llama ~60 veces/seg
    actor.colisiona_con(otro)                # esfera 3D
    actor.colisiona_en_plano_con(otro)       # solo XZ (estilo FPS)
    actor.radio_de_colision = 0.5  radio_de_disparo = 0.8

Escena y cámara
    pilas.escena_actual()  pilas.escenas.Normal()
    camara = pilas.escena_actual().camara
    camara.x/y/z  camara.objetivo = (x, y, z)
    camara.usar_control_orbital()            # drag orbita, rueda zoom
    camara.disparar_rayo(actores, alcance=40)

Habilidades  (actor.aprender)
    pilas.habilidades.MoverseConElTeclado   RebotarComoPelota
    GirarConstantemente                     CaminarEnPrimeraPersona

Tareas
    pilas.tareas.una_vez(2, f)   siempre(1, f)   condicional(0.1, f)

Entrada
    pilas.control.arriba/abajo/izquierda/derecha   (flechas + WASD)
    pilas.control.mouse_x/y  boton_izquierdo/derecho/medio

Depuración
    pilas.fps.ver()   pilas.mostrar_ejes()
    pilas.depurador.definir_modos(fps=True, ejes=True,
        radios_de_colision=True, puntos_de_control=True)
    Atajos de la ventana: ESC salir - F9 ejes - F10 radios de
    colisión - F11 FPS - F12 puntos de control

Audio
    pilas.sonidos.cargar('explosion.wav').reproducir()
    pilas.musica.cargar('tema.ogg').reproducir()   # en bucle

Luces y sombras
    pilas.luces.direccional.color = pilas.colores.blanco  # el "sol"
    pilas.luces.direccional.ambiente = 0.2     # luz ambiente (0..1)
    pilas.luces.agregar(pilas3d.luces.LuzPuntual(x=2, y=4, z=0,
        color=(1, 0.7, 0.3), alcance=10))      # hasta 8 puntuales
    pilas.luces.quitar(luz) / pilas.luces.limpiar()
    pilas.actores.Sombra(actor)                # sombra falsa en el piso

Modo interactivo (consola de Python)
    >>> import pilas3d
    >>> pilas = pilas3d.iniciar()
    >>> cubo = pilas.actores.Cubo()       # la ventana ya se ve
    >>> pilas.paso()                      # dibuja un frame
    >>> for i in range(180):              # ~3s de animación
    ...     pilas.paso()
"""


class _Fps(object):
    """Acceso a la visualización de FPS: ``pilas.fps.ver()``."""

    def __init__(self, pilas):
        self._pilas = pilas

    def ver(self):
        self._pilas._fps_visible = True

    def ocultar(self):
        self._pilas._fps_visible = False

    @property
    def visible(self):
        return self._pilas._fps_visible


class Pilas(object):
    """Representa el área de juego; es el contenedor principal.

    Al igual que en pilas-engine, este objeto mantiene la escena actual,
    la fábrica de actores y el bucle de juego.
    """

    def __init__(self, ancho=640, alto=480, titulo="pilas3d",
                 sin_ventana=False):
        self.dt = 1 / 60.0
        self._escena_actual = None
        self._actor_ejes = None
        self._fps_visible = False
        self.fps = _Fps(self)

        self.actores = Actores(self)
        self.escenas = Escenas(self)
        self.colores = colores
        self.habilidades = Habilidades()
        self.depurador = Depurador(self)
        self.sonidos = Sonidos(self)
        self.musica = _Musica(self)
        self.interpolaciones = interpolaciones

        if sin_ventana:
            self.ventana = None
            self.control = ControlNulo()
        else:
            from pilas3d.ventana import Ventana

            self.ventana = Ventana(self, ancho, alto, titulo)
            self.control = Control(self.ventana)

        self.escenas.Normal()

    def escena_actual(self):
        return self._escena_actual

    @property
    def tareas(self):
        """El planificador de tareas de la escena actual."""
        return self._escena_actual.tareas

    @property
    def luces(self):
        """Las luces de la escena actual (``pilas.luces.agregar(...)``)."""
        return self._escena_actual.luces

    def mostrar_ejes(self, largo=50):
        """Muestra los ejes X (rojo), Y (verde) y Z (azul) del origen."""
        if self._actor_ejes is None:
            self._actor_ejes = self.actores.Ejes(largo=largo)

    def ocultar_ejes(self):
        if self._actor_ejes is not None:
            self._actor_ejes.eliminar()
            self._actor_ejes = None

    def _definir_escena(self, escena):
        self._escena_actual = escena

    def _tick(self, dt):
        # escena.actualizar actualiza self.dt
        self._escena_actual.actualizar(dt)

    def ejecutar(self):
        """Inicia el bucle de juego (llamadas a actualizar + dibujar)."""
        if self.ventana is None:
            print("pilas3d se inició con sin_ventana=True; "
                  "no hay ventana que ejecutar.")
            return
        pyglet.clock.schedule_interval(self._tick, 1 / 60.0)
        pyglet.app.run()

    def paso(self, dt=None):
        """Avanza un solo frame: para usar pilas3d en modo interactivo.

        En una consola de Python no hace falta ``ejecutar()`` (que
        bloquea): se puede ir construyendo la escena paso a paso y
        refrescar la ventana llamando a ``paso()``::

            >>> import pilas3d
            >>> pilas = pilas3d.iniciar()
            >>> cubo = pilas.actores.Cubo()
            >>> for i in range(120):   # anima ~2 segundos
            ...     pilas.paso()
        """
        if self.ventana is None:
            print("pilas3d se inició con sin_ventana=True; "
                  "no hay ventana que actualizar.")
            return
        self.ventana.switch_to()
        self.ventana.dispatch_events()
        self._tick(self.dt if dt is None else dt)
        # dispatch_event encola el evento; dispatch_pending_events lo
        # ejecuta ya, así paso() dibuja en el mismo llamado.
        self.ventana.dispatch_event('on_draw')
        self.ventana.dispatch_pending_events()
        self.ventana.flip()

    def ayuda(self):
        """Imprime una guía rápida de la API en la consola."""
        print(AYUDA)

    def interpolar(self, actor, atributo, valores, duracion=1.0,
                   demora=0.0, tipo=None):
        """Anima una propiedad del actor (como pilas.utils.interpolar).

        >>> pilas.interpolar(cubo, 'x', 10, duracion=2)
        >>> pilas.interpolar(cubo, 'rotacion', 360,
        ...                  tipo=interpolaciones.ReboteFinal)
        """
        clase = tipo or interpolaciones.Lineal
        clase(valores, duracion=duracion, demora=demora).iniciar(
            actor, atributo)

    def terminar(self):
        if self.ventana is not None:
            self.ventana.close()
            self.ventana = None


def obtener_ruta(nombre):
    """Ruta absoluta a un recurso dentro del paquete.

    >>> pilas3d.obtener_ruta('data/caja.png')
    """
    return os.path.join(os.path.dirname(__file__), nombre)


def iniciar(ancho=640, alto=480, titulo="pilas3d", sin_ventana=False):
    """Inicia pilas3d y retorna el objeto principal ``Pilas``.

    ``sin_ventana=True`` permite crear el mundo sin abrir una ventana
    (útil para tests).
    """
    return Pilas(ancho=ancho, alto=alto, titulo=titulo,
                 sin_ventana=sin_ventana)
