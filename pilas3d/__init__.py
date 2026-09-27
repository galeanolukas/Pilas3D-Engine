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
from pilas3d import simbolos
from pilas3d.actores import Actores
from pilas3d.control import Control, ControlNulo
from pilas3d.escenas import Escenas
from pilas3d.habilidades import Habilidades
from pilas3d.depurador import Depurador
from pilas3d.sonidos import Sonidos
from pilas3d.musica import _Musica
from pilas3d import interpolaciones

def _leer_version():
    """Versión del motor, tomada del archivo VERSION de la raíz."""
    ruta = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
    try:
        with open(ruta, encoding='utf-8') as f:
            return f.read().strip()
    except OSError:
        return '0.0.0'


VERSION = _leer_version()

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
    pilas.actores.ModeloAnimado('run/f*.obj', velocidad=10)  # secuencia .obj
    pilas.actores.ModeloGLTF('p.glb')        # glTF 2.0 con esqueleto
    modelo.animar('caminar'); modelo.animaciones()
    pilas.actores.Mundo(tamano_chunk=16)     # voxels estilo Minecraft
    pilas.actores.Mundo(infinito=True)       # terreno procedural sin fin
    mundo.generar_terreno(48, 48, altura=4)  # heightmap procedural
    mundo.poner_bloque(i, j, k, 'ladrillo')  sacar_bloque(i, j, k)
    mundo.disparar_bloque(origen, dir)       # picar/colocar (rayo DDA)
    pilas.actores.ModeloJSON('ladder.json')  # modelo de bloque Minecraft

Cada actor
    actor.x = 3      actor.rotacion_y = 45    actor.escala = 2
    actor.imagen = 'caja.png'                # textura
    actor.eliminar()  actor.actualizar()     # se llama ~60 veces/seg
    actor.colisiona_con(otro)                # esfera 3D
    actor.colisiona_en_plano_con(otro)       # solo XZ (estilo FPS)
    actor.radio_de_colision = 0.5  radio_de_disparo = 0.8

Escena y cámara
    pilas.escena_actual()  pilas.escena  pilas.cambiar_escena(e)
    class Menu(pilas3d.escenas.Escena):   # escena propia
        def iniciar(self): ...           # hooks: terminar(),
        def cuando_pulsa_tecla(s): ...   # cuando_actualiza()
    pilas.escenas.vincular(Menu)         # luego pilas.escenas.Menu()
    pilas.limpiar()                      # escena Normal vacía
    camara = pilas.escena_actual().camara
    camara.x/y/z  camara.objetivo = (x, y, z)
    camara.usar_control_orbital()            # drag orbita, rueda zoom
    camara.seguir_a(actor, modo='tercera')   # 'primera'/'segunda'
    camara.dejar_de_seguir()                 # vista libre
    camara.disparar_rayo(actores, alcance=40)
    camara.actor_bajo_mouse()                # picking con el mouse
    camara.punto_bajo_mouse(y_plano=0)       # rayo -> punto del suelo

Habilidades  (actor.aprender)
    pilas.habilidades.MoverseConElTeclado   RebotarComoPelota
    GirarConstantemente                     CaminarEnPrimeraPersona
    SeguirAlActor                           MirarAlActor
    MoverseEnCirculo                        MoverseComoCoche
    Imitar                                  AumentarConRueda
    RotarConMouse                           PuedeExplotar
    PisaPlataformas                         # gravedad que pisa bloques
    PerseguirAOtroActor                     # persigue esquivando (A*)
    Arrastrable                             # arrastrar con el mouse
    SeguirAlMouse                           # caminar hacia el puntero
    Disparar                                # actor.disparar() -> Proyectil

Tareas
    pilas.tareas.una_vez(2, f)   siempre(1, f)   condicional(0.1, f)

Entrada
    pilas.control.arriba/abajo/izquierda/derecha   (flechas + WASD)
    pilas.simbolos.t  .ESPACIO  .ENTER  .a-.z  ._1-._9  .F1-F12
    escena.cuando_pulsa_tecla = fn   # recibe el simbolo pulsado
    pilas.control.mouse_x/y  boton_izquierdo/derecho/medio
    pilas.cuando_hace_click(f)    # f(actor, punto) al hacer click
    pilas.cuando_suelta_click(f)  cuando_mueve_mouse(f)

Menu (overlay 2D, teclado+mouse)
    pilas.actores.Menu(opciones=[("Jugar", fn), ("Salir", fn)],
                       titulo="MI JUEGO", x=230, y=300)
    opciones extra: ("Sonido", 'check', True, fn)   [x]/[ ]
                    ("Nombre", 'input', 'yo', fn)   ENTER edita
    menu.mover('abajo')  menu.elegir()  menu.opcion

Audio
    pilas.sonidos.cargar('x.wav')  .volumen=.4  .mute=True
    pilas.musica.cargar('x.ogg')   .reproducir()  .volumen=.5

Tiempo
    pilas.actores.Temporizador(duracion=10, cuando_termina=fn)
    t.iniciar()  t.detener()  t.reiniciar()  t.ajustar(5, fn)
    t.ciclico=True   t.visible=False   t.avisar(3, fn)
    sin duracion: cronómetro ascendente (t.tiempo = transcurridos)

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
    pilas.actores.Cielo()                      # cielo estrellado
    pilas.actores.Cielo('mi_fondo.png')        # o con textura propia

Personajes predefinidos (heredan de Actor, cada uno con un método
de dibujo distinto)
    pilas.actores.Robot()      # cuboides combinados, color por vértice
    pilas.actores.Humanoide()  # bipedo estilo muñeco
    pilas.actores.Mono()       # esferas + cuboides
    pilas.actores.Arania()     # araña de primitivas (sin recursos)
    pilas.actores.Espectro()   # alambrado (GL_LINES, sin superficie)
    mallas.combinar([(geo, (dx,dy,dz), color), ...])  # arma los tuyos
    pilas.actores.Bot(personaje='Robot', mundo=mundo)  # NPC listo
    cualquier_actor.aprender(pilas.habilidades.SerBot, objetivo=j,
        mundo=mundo, radio_vision=8)   # patrulla, persigue y vuelve

Partículas (efectos)
    pilas.actores.Particulas(cantidad=100, vida=2, velocidad=3,
        direccion=(0,1,0), dispersion=0.5, gravedad=0, tamano=4,
        color=..., color_final=..., ciclico=True)
    Presets: pilas.actores.Particulas.fuego(pilas) / .humo / .lluvia
             / .explosion(pilas, x, y, z)      # explosión única
    emisor.pausar() / emisor.reanudar()

Red (multijugador simple, TCP + JSON)
    red = pilas.red.hospedar(puerto=7777)        # o .conectar(host, puerto)
    red.enviar("posicion", x=1, y=0, z=2)        # broadcast a los demás
    red.cuando_reciba("posicion", fn)            # fn(datos, de_id)
    # mensajes reservados: 'hola' (tu id), 'entro', 'salio'

Asistente de IA (opcional, modelo local con Ollama)
    pilas.ayuda("¿cómo hago un enemigo que me persiga?")
    # la primera vez descarga el binario y el modelo (~1 GB)

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
        self._callbacks_click = []
        self._callbacks_suelta = []
        self._callbacks_mueve = []
        self._mouse_handlers_conectados = False

        self.actores = Actores(self)
        self.escenas = Escenas(self)
        self.colores = colores
        self.simbolos = simbolos
        self.habilidades = Habilidades()
        self.depurador = Depurador(self)
        self.sonidos = Sonidos(self)
        self.musica = _Musica(self)
        self.interpolaciones = interpolaciones
        from pilas3d.red import Red
        self.red = Red(self)

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
    def escena(self):
        """La escena activa. Asignable: ``pilas.escena = Menu(pilas)``."""
        return self._escena_actual

    @escena.setter
    def escena(self, escena):
        self._definir_escena(escena)

    def cambiar_escena(self, escena):
        """Activa otra escena (la anterior recibe ``terminar()``).

        Crear una escena ya la activa sola; este método es la forma
        explícita, útil para volver a una escena ya construida.
        """
        self._definir_escena(escena)

    def limpiar(self):
        """Vuelve a una escena Normal vacía.

        Atajo pensado para la consola interactiva: tras correr un
        ``%ejemplo`` o probar cosas, ``pilas.limpiar()`` elimina todos
        los actores y deja una escena nueva (equivalente a
        ``pilas.escenas.Normal()``).
        """
        self.escenas.Normal()

    @property
    def tareas(self):
        """El planificador de tareas de la escena actual."""
        return self._escena_actual.tareas

    @property
    def luces(self):
        """Las luces de la escena actual (``pilas.luces.agregar(...)``)."""
        return self._escena_actual.luces

    # -- eventos de mouse ---------------------------------------------------

    def cuando_hace_click(self, funcion):
        """Conecta ``funcion`` al click izquierdo del mouse.

        La función recibe ``(actor, punto)``: el actor de la escena
        bajo el puntero (o None) y el punto donde el rayo corta el
        plano ``y=0`` (o None)::

            >>> pilas.cuando_hace_click(al_clickear)
            >>> def al_clickear(actor, punto):
            ...     if actor: print("click en", actor)
        """
        self._callbacks_click.append(funcion)
        self._conectar_mouse()

    def cuando_suelta_click(self, funcion):
        """Conecta ``funcion(x, y)`` al soltar el botón izquierdo."""
        self._callbacks_suelta.append(funcion)
        self._conectar_mouse()

    def cuando_mueve_mouse(self, funcion):
        """Conecta ``funcion(x, y)`` al mover el mouse (píxeles)."""
        self._callbacks_mueve.append(funcion)
        self._conectar_mouse()

    def _conectar_mouse(self):
        if (self.ventana is not None
                and not self._mouse_handlers_conectados):
            self.ventana.push_handlers(
                on_mouse_press=self._ev_mouse_press,
                on_mouse_release=self._ev_mouse_release,
                on_mouse_motion=self._ev_mouse_motion)
            self._mouse_handlers_conectados = True

    def _ev_mouse_press(self, x, y, button, modifiers):
        from pyglet.window import mouse
        if button & mouse.LEFT:
            self.procesar_click(x, y)

    def _ev_mouse_release(self, x, y, button, modifiers):
        from pyglet.window import mouse
        if button & mouse.LEFT:
            for fn in self._callbacks_suelta:
                fn(x, y)

    def _ev_mouse_motion(self, x, y, dx, dy):
        for fn in self._callbacks_mueve:
            fn(x, y)

    def procesar_click(self, x, y):
        """Ejecuta los callbacks de click para el píxel (x, y).

        También sirve para simular clicks sin ventana real (tests,
        consola interactiva): ``pilas.procesar_click(320, 240)``.
        """
        if not self._callbacks_click:
            return
        camara = self._escena_actual.camara
        actor = camara.actor_bajo_mouse(x=x, y=y)
        punto = camara.punto_bajo_mouse(0.0, x=x, y=y)
        for fn in self._callbacks_click:
            fn(actor, punto)

    def mostrar_ejes(self, largo=50):
        """Muestra los ejes X (rojo), Y (verde) y Z (azul) del origen."""
        if self._actor_ejes is None:
            self._actor_ejes = self.actores.Ejes(largo=largo)

    def ocultar_ejes(self):
        if self._actor_ejes is not None:
            self._actor_ejes.eliminar()
            self._actor_ejes = None

    def _definir_escena(self, escena):
        anterior = self._escena_actual
        if anterior is not None and anterior is not escena:
            anterior.terminar()
            self._actor_ejes = None
        self._escena_actual = escena

    def _tick(self, dt):
        # escena.actualizar actualiza self.dt
        self._escena_actual.actualizar(dt)
        self.red._actualizar()

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
            # tick igual: puede haber un cierre diferido pendiente
            # (terminar() agenda el close para no romper el event loop)
            pyglet.clock.tick()
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

    def ayuda(self, consulta=None):
        """Guía rápida de la API o asistente de IA.

        Sin argumentos imprime la chuleta de siempre. Con una consulta
        pregunta a un modelo local (Ollama); la primera vez descarga
        el binario y el modelo a pedido::

            pilas.ayuda()                          # chuleta
            pilas.ayuda("¿cómo hago un enemigo?")  # IA local
        """
        if consulta is None:
            print(AYUDA)
            return
        from pilas3d.ia.asistente import preguntar
        try:
            print(preguntar(consulta, contexto=self._contexto()))
        except RuntimeError as e:
            print("(asistente no disponible: %s)" % e)
            print(AYUDA)

    def _contexto(self):
        """Resumen de la escena para darle contexto al asistente."""
        escena = self._escena_actual
        if escena is None:
            return ''
        cam = escena.camara
        return ('escena=%s, actores=%d (%s), camara=(%.1f, %.1f, %.1f)'
                % (escena.__class__.__name__, len(escena.actores),
                   ', '.join(a.__class__.__name__
                             for a in escena.actores[:8]),
                   cam.x, cam.y, cam.z))
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
        """Cierra la ventana. El cierre es diferido: si se llama desde
        dentro del event loop (un handler de tecla, el inputhook de
        IPython que itera ``pyglet.app.windows``), cerrar en el acto
        rompe la iteración con 'Set changed size during iteration'."""
        ventana = self.ventana
        self.ventana = None
        if ventana is not None:
            pyglet.clock.schedule_once(
                lambda dt: ventana.close(), 0)


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
    # PILAS3D_HEADLESS=1 fuerza modo sin ventana (validación de juegos
    # generados, CI, tests).
    if os.environ.get('PILAS3D_HEADLESS'):
        sin_ventana = True
    return Pilas(ancho=ancho, alto=alto, titulo=titulo,
                 sin_ventana=sin_ventana)
