# -*- encoding: utf-8 -*-
"""Fábrica de actores: ``pilas.actores.Cubo()``, etc.

Para crear un actor propio, heredá de ``Actor``::

    from pilas3d.actores.actor import Actor
"""

from pilas3d.actores.actor import Actor
from pilas3d.actores.cubo import Cubo
from pilas3d.actores.esfera import Esfera
from pilas3d.actores.piso import Piso
from pilas3d.actores.ejes import Ejes
from pilas3d.actores.pared import Pared
from pilas3d.actores.plano import Plano
from pilas3d.actores.mapa import Mapa
from pilas3d.actores.cartel import Cartel
from pilas3d.actores.animacion import Animacion
from pilas3d.actores.modelo import Modelo
from pilas3d.actores.sombra import Sombra
from pilas3d.actores.cielo import Cielo
from pilas3d.actores.modelo_animado import ModeloAnimado
from pilas3d.actores.mundo import Mundo
from pilas3d.actores.modelo_json import ModeloJSON
from pilas3d.actores.modelo_gltf import ModeloGLTF
from pilas3d.actores.texto import Texto, Puntaje
from pilas3d.actores.panel import Panel
from pilas3d.actores.temporizador import Temporizador
from pilas3d.actores.particulas import Particulas
from pilas3d.actores.proyectil import Proyectil
from pilas3d.actores.menu import Menu
from pilas3d.actores.personajes import (Personaje, Robot, Humanoide,
                                      Mono, Arania, Espectro)


class Actores(object):
    """Punto de acceso a los actores, como ``pilas.actores`` en pilas."""

    def __init__(self, pilas):
        self._pilas = pilas

    def Cubo(self, x=0, y=0, z=0):
        return Cubo(self._pilas, x=x, y=y, z=z)

    def Esfera(self, x=0, y=0, z=0, radio=1.0, radio_de_colision=None):
        return Esfera(self._pilas, x=x, y=y, z=z, radio=radio,
                      radio_de_colision=radio_de_colision)

    def Piso(self, x=0, y=0, z=0, tamano=20, divisiones=20):
        return Piso(
            self._pilas, x=x, y=y, z=z, tamano=tamano, divisiones=divisiones
        )

    def Ejes(self, x=0, y=0, z=0, largo=5):
        return Ejes(self._pilas, x=x, y=y, z=z, largo=largo)

    def Pared(self, x=0, y=None, z=0, ancho=4.0, alto=3.0,
              profundidad=0.3):
        return Pared(self._pilas, x=x, y=y, z=z, ancho=ancho, alto=alto,
                     profundidad=profundidad)

    def Plano(self, x=0, y=0, z=0, ancho=20, profundidad=20):
        return Plano(self._pilas, x=x, y=y, z=z, ancho=ancho,
                     profundidad=profundidad)

    def Cartel(self, x=0, y=0, z=0, ancho=1.0, alto=1.0):
        return Cartel(self._pilas, x=x, y=y, z=z, ancho=ancho, alto=alto)

    def Animacion(self, imagen, columnas, filas=1, x=0, y=0, z=0,
                  ancho=1.0, alto=1.0, velocidad=10, ciclica=True,
                  eliminar_al_terminar=False):
        return Animacion(
            self._pilas, imagen, columnas, filas=filas, x=x, y=y, z=z,
            ancho=ancho, alto=alto, velocidad=velocidad, ciclica=ciclica,
            eliminar_al_terminar=eliminar_al_terminar)

    def Modelo(self, ruta, x=0, y=0, z=0, escala=1.0):
        return Modelo(self._pilas, ruta, x=x, y=y, z=z, escala=escala)

    def Sombra(self, dueno, radio=None, opacidad=60):
        return Sombra(self._pilas, dueno, radio=radio, opacidad=opacidad)

    def Cielo(self, imagen="estrellas", radio=400):
        """Domo de fondo: 'estrellas' genera un cielo sin archivos."""
        return Cielo(self._pilas, imagen=imagen, radio=radio)

    def Mundo(self, tipos=None, atlas=None, tamano_chunk=16,
              infinito=False, semilla=0, altura=4, distancia_vista=3):
        """Mundo de voxels (grilla de bloques, malla por chunk).

        ``atlas`` puede ser una lista de imágenes/rutas que se
        componen en una sola textura. Con ``infinito=True`` el terreno
        se genera solo alrededor de la cámara (determinista por
        ``semilla``) y los chunks lejanos se descargan de la malla.
        """
        return Mundo(self._pilas, tipos=tipos, atlas=atlas,
                     tamano_chunk=tamano_chunk, infinito=infinito,
                     semilla=semilla, altura=altura,
                     distancia_vista=distancia_vista)

    def ModeloJSON(self, ruta, x=0, y=0, z=0, escala=1.0):
        """Modelo de bloque estilo Minecraft (.json con elements)."""
        return ModeloJSON(self._pilas, ruta, x=x, y=y, z=z,
                          escala=escala)

    def ModeloGLTF(self, ruta, x=0, y=0, z=0, escala=1.0,
                   animacion=None, velocidad=1.0, ciclica=True):
        """Modelo glTF 2.0 (.gltf/.glb) con animación esquelética
        por CPU. ``.animar('nombre')`` / ``.animaciones()``."""
        return ModeloGLTF(self._pilas, ruta, x=x, y=y, z=z,
                          escala=escala, animacion=animacion,
                          velocidad=velocidad, ciclica=ciclica)

    def ModeloAnimado(self, rutas, velocidad=8, ciclica=True,
                      suavizar=False, eliminar_al_terminar=False,
                      x=0, y=0, z=0, escala=1.0):
        """Secuencia de .obj animada (lista de rutas o patrón glob)."""
        return ModeloAnimado(
            self._pilas, rutas, velocidad=velocidad, ciclica=ciclica,
            suavizar=suavizar,
            eliminar_al_terminar=eliminar_al_terminar,
            x=x, y=y, z=z, escala=escala)

    def Particulas(self, cantidad=100, vida=2.0, velocidad=3.0,
                   direccion=(0, 1, 0), dispersion=0.5, gravedad=0.0,
                   color=None, color_final=None, tamano=4.0,
                   ciclico=True, x=0, y=0, z=0):
        """Emisor de partículas. Presets: ``Particulas.fuego(pilas)``,
        ``.humo``, ``.lluvia``, ``.explosion``."""
        return Particulas(
            self._pilas, cantidad=cantidad, vida=vida,
            velocidad=velocidad, direccion=direccion,
            dispersion=dispersion, gravedad=gravedad, color=color,
            color_final=color_final, tamano=tamano, ciclico=ciclico,
            x=x, y=y, z=z)

    def Proyectil(self, direccion=(0, 0, 1), velocidad=20.0,
                  alcance=40.0, objetivos=None, cuando_impacta=None,
                  ignorar=None, radio=0.15, color=None,
                  x=0, y=0, z=0):
        """Disparo en línea recta; ver ``habilidades.Disparar``."""
        return Proyectil(
            self._pilas, direccion=direccion, velocidad=velocidad,
            alcance=alcance, objetivos=objetivos,
            cuando_impacta=cuando_impacta, ignorar=ignorar,
            radio=radio, color=color, x=x, y=y, z=z)

    def Menu(self, opciones, x=200, y=300, separacion=38, tamano=22,
             color=None, seleccionado=None, titulo=None,
             guardar_en=None):
        """Menú navegable (flechas/ENTER o mouse) con opciones
        ``[(texto, funcion), ...]``. Con ``guardar_en`` persiste los
        valores en un JSON."""
        return Menu(self._pilas, opciones, x=x, y=y,
                    separacion=separacion, tamano=tamano, color=color,
                    seleccionado=seleccionado, titulo=titulo,
                    guardar_en=guardar_en)

    def Mapa(self, matriz, simbolos, tamano_celda=2.0, x=0, y=0, z=0):
        return Mapa(self._pilas, matriz, simbolos,
                    tamano_celda=tamano_celda, x=x, y=y, z=z)

    def Texto(self, texto="", x=10, y=10, tamano=18):
        return Texto(self._pilas, texto=texto, x=x, y=y, tamano=tamano)

    def Panel(self, x=0, y=0, ancho=200, alto=200, color=None,
              opacidad=255):
        """Rectángulo 2D relleno (overlay) para paneles de interfaz:
        fondos oscuros detrás de textos, HUD, barras. Combínalo con
        ``pilas.ventana.area_3d`` para dividir la ventana en vista 3D
        + zona de interfaz."""
        return Panel(self._pilas, x=x, y=y, ancho=ancho, alto=alto,
                     color=color, opacidad=opacidad)

    def Puntaje(self, x=10, y=10, tamano=22, prefijo=""):
        return Puntaje(
            self._pilas, x=x, y=y, tamano=tamano, prefijo=prefijo
        )

    def Temporizador(self, x=10, y=10, tamano=18, duracion=0,
                     cuando_termina=None, ciclico=False, visible=True,
                     autoeliminar=False, ascendente=True, formato=None,
                     color=None):
        """Contador de tiempo: cuenta regresiva (``duracion`` > 0) que
        ejecuta ``cuando_termina`` al llegar a cero, o cronómetro
        ascendente (``duracion=0``). ``visible=False`` lo hace
        invisible; ``ciclico=True`` lo repite; ``avisar(s, fn)``
        programa avisos intermedios."""
        if color is None:
            from pilas3d import colores
            color = colores.negro
        return Temporizador(
            self._pilas, x=x, y=y, tamano=tamano, duracion=duracion,
            cuando_termina=cuando_termina, ciclico=ciclico,
            visible=visible, autoeliminar=autoeliminar,
            ascendente=ascendente, formato=formato, color=color)

    # -- personajes predefinidos (como pilas.actores.Mono en pilas) --

    def Robot(self, x=0, y=0, z=0):
        return Robot(self._pilas, x=x, y=y, z=z)

    def Humanoide(self, x=0, y=0, z=0):
        return Humanoide(self._pilas, x=x, y=y, z=z)

    def Mono(self, x=0, y=0, z=0):
        return Mono(self._pilas, x=x, y=y, z=z)

    def Arania(self, x=0, y=0, z=0):
        return Arania(self._pilas, x=x, y=y, z=z)

    def Espectro(self, x=0, y=0, z=0):
        return Espectro(self._pilas, x=x, y=y, z=z)

    def Bot(self, personaje='Robot', x=0, y=0, z=0, casa=None,
            radio_patron=8, velocidad=2.0, radio_vision=8,
            mundo=None, objetivo=None):
        """NPC con comportamiento: un personaje que aprende la
        habilidad ``SerBot`` — patrulla cerca de ``casa``, persigue
        a ``objetivo`` si entra en ``radio_vision`` y vuelve después.

        ``personaje`` elige el cuerpo: 'Robot', 'Humanoide', 'Mono',
        'Arania' o 'Espectro' (o la clase directamente)."""
        from pilas3d.habilidades.ser_bot import SerBot
        clases = {'Robot': Robot, 'Humanoide': Humanoide, 'Mono': Mono,
                  'Arania': Arania, 'Espectro': Espectro}
        base = clases[personaje] if isinstance(personaje, str) \
            else personaje
        bot = base(self._pilas, x=x, y=y, z=z)
        bot.aprender(SerBot, casa=casa, radio_patron=radio_patron,
                     velocidad=velocidad, radio_vision=radio_vision,
                     mundo=mundo, objetivo=objetivo)
        return bot


# Los presets del emisor quedan accesibles desde la fábrica:
# ``pilas.actores.Particulas.fuego(pilas)``, ``.humo``, ``.lluvia``,
# ``.explosion``.
for _preset in ('fuego', 'humo', 'lluvia', 'explosion'):
    setattr(Actores.Particulas, _preset, getattr(Particulas, _preset))
