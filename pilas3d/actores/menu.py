# -*- encoding: utf-8 -*-
"""Menu: lista de opciones navegable con teclado y mouse.

Igual que un menú de juego: las opciones son textos en overlay 2D
(píxeles de ventana), se navega con flechas/WS + ENTER o se elige
haciendo click::

    menu = pilas.actores.Menu(
        opciones=[
            ("Jugar",        iniciar_juego),              # accion
            ("Sonido", 'check', True, al_prender),        # checkbox
            ("Volumen",      ciclar_volumen),             # cicla texto
            ("Nombre", 'input', 'jugador', al_nombrar),   # input
            ("Salir",         pilas.terminar),
        ],
        x=260, y=300, tamano=22)

Tipos de opción:

- ``(texto, fn)``: acción. Si ``fn()`` devuelve un texto nuevo, la
  etiqueta se actualiza — para opciones que ciclan valores.
- ``(texto, 'check', valor, fn)``: booleano, muestra ``[x]``/``[ ]``
  y al activar llama ``fn(valor_nuevo)``.
- ``(texto, 'input', inicial, fn)``: entrada de texto — ENTER abre la
  edición, se escribe directo, BACKSPACE borra, ENTER confirma y
  llama ``fn(texto)``, ESC cancela.

Persistencia: con ``guardar_en='config-game.json'`` el menú carga los
valores guardados al iniciar (y los aplica llamando a cada ``fn``) y
vuelve a escribir el JSON en cada cambio.

Fondo y presentación:

- ``fondo=(r, g, b)`` o ``(r, g, b, alfa)``: dibuja un panel detrás
  de las opciones para que el texto contraste; el alfa (0-255) lo
  hace transparente — ``(0, 0, 0, 120)`` es un panel oscuro suave.
- ``fondo_imagen='ruta.png'``: imagen detrás del menú (se estira al
  área del panel o a toda la ventana si ``pantalla_completa``).
- ``pantalla_completa=True``: el fondo/imagen cubre la ventana y el
  menú se centra — pensado para pantallas de título.
- ``centrado=True``: centra el panel en la ventana sin cubrirla.
- ``margen``: relleno del panel alrededor del texto (píxeles).
"""

import json
import os

from pyglet.window import key, mouse

from pilas3d import colores
from pilas3d.actores.actor import Actor
from pilas3d.actores.texto import Texto


class Menu(Actor):
    """Menú de opciones como overlay 2D (no es geometría 3D)."""

    es_overlay = True

    def __init__(self, pilas, opciones, x=200, y=300, separacion=38,
                 tamano=22, color=None, seleccionado=None, titulo=None,
                 guardar_en=None, fondo=None, fondo_imagen=None,
                 pantalla_completa=False, centrado=False, margen=24):
        super(Menu, self).__init__(pilas)
        self.radio_de_colision = 0.0
        self.color_base = color or colores.blanco
        self.color_sel = seleccionado or colores.amarillo
        self.separacion = separacion
        self.tamano = tamano
        self.margen = margen
        self.pantalla_completa = pantalla_completa
        self._opciones = [self._normalizar(o) for o in opciones]
        self._sel = 0
        self._editando = None        # índice de la opción 'input' activa
        self._editando_valor = ''
        self._ruta = guardar_en
        self._rect_fondo = None      # Rectangle lazy (modo ventana)
        self._sprite = None
        self._imagen = None
        self._fondo_rgba = None
        if fondo is not None:
            f = tuple(fondo)
            self._fondo_rgba = (f + (255,))[:4]
        if fondo_imagen is not None:
            try:
                import pyglet
                self._imagen = pyglet.image.load(fondo_imagen)
            except Exception:
                self._imagen = None

        y0 = y
        if titulo:
            t = Texto(pilas, titulo, x=x, y=y, tamano=tamano + 10)
            t.color = self.color_sel
            self._titulo = t
            y0 -= separacion * 1.6
        else:
            self._titulo = None

        self._x = x
        self._y0 = y0
        self._textos = []
        for i, op in enumerate(self._opciones):
            item = Texto(pilas, '', x=x,
                         y=y0 - i * separacion, tamano=tamano)
            self._textos.append(item)
        if centrado or pantalla_completa:
            self.centrar()
        self._pintar()
        if self._ruta:
            self.cargar()

        if pilas.ventana is not None:
            pilas.ventana.push_handlers(
                on_key_press=self._al_pulsar,
                on_text=self._al_texto,
                on_mouse_motion=self._al_mover_mouse,
                on_mouse_press=self._al_click_mouse)

    # -- estado ----------------------------------------------------------

    def _generar_geometria(self):
        return [], [], 0

    @staticmethod
    def _normalizar(op):
        if len(op) == 2:
            return (op[0], 'accion', None, op[1])
        return tuple(op)            # (texto, tipo, valor, fn)

    @property
    def opcion(self):
        """Índice de la opción seleccionada."""
        return self._sel

    def _texto_visible(self, i):
        texto, tipo, valor, _fn = self._opciones[i]
        if tipo == 'check':
            return '[x] %s' % texto if valor else '[ ] %s' % texto
        if tipo == 'input':
            cursor = '_' if self._editando == i else ''
            return '%s: %s%s' % (texto, valor, cursor)
        return texto

    def _ancho_item(self, i):
        # estimación en píxeles (el Label real se crea al dibujar)
        return len(self._texto_visible(i)) * self.tamano * 0.62

    def _rect_item(self, i):
        ty = self._textos[i].y
        return (self._x, ty - 6,
                self._x + self._ancho_item(i), ty + self.tamano * 1.2)

    def _rect_panel(self):
        """Rectángulo (x0, y0, x1, y1) que contiene todo el menú."""
        ancho = max(self._ancho_item(i)
                    for i in range(len(self._opciones)))
        ancho += self.tamano * 2.4        # el prefijo '» ' no entra
        x0 = self._x - self.margen
        x1 = self._x + ancho + self.margen
        y1 = (self._titulo.y if self._titulo is not None
              else self._textos[0].y) + (self.tamano + 10) * 1.3 \
            + self.margen
        y0 = self._textos[-1].y - 6 - self.margen
        return (x0, y0, x1, y1)

    def centrar(self):
        """Reubica título y opciones centrados en la ventana."""
        ventana = self.pilas.ventana
        vw = ventana.width if ventana is not None else 800
        vh = ventana.height if ventana is not None else 600
        x0, y0, x1, y1 = self._rect_panel()
        desplaza_x = (vw - (x1 - x0)) / 2 - x0
        desplaza_y = (vh - (y1 - y0)) / 2 - y0
        self._x += desplaza_x
        for item in self._textos:
            item.y += desplaza_y
            item.x = self._x
        if self._titulo is not None:
            self._titulo.x = self._x
            self._titulo.y += desplaza_y
        self._y0 += desplaza_y

    # -- dibujado ----------------------------------------------------------

    def dibujar(self):
        """Fondo del menú: imagen y/o panel de color con alfa."""
        if self._imagen is None and self._fondo_rgba is None:
            return
        x0, y0, x1, y1 = self._rect_panel()
        ventana = self.pilas.ventana
        if self.pantalla_completa and ventana is not None:
            x0, y0, x1, y1 = 0, 0, ventana.width, ventana.height
        if self._imagen is not None:
            if self._sprite is None:
                import pyglet
                self._sprite = pyglet.sprite.Sprite(self._imagen)
            self._sprite.x = x0
            self._sprite.y = y0
            self._sprite.scale_x = (x1 - x0) / self._imagen.width
            self._sprite.scale_y = (y1 - y0) / self._imagen.height
            self._sprite.draw()
        if self._fondo_rgba is not None:
            from pyglet.shapes import Rectangle
            if self._rect_fondo is None:
                self._rect_fondo = Rectangle(0, 0, 1, 1)
            r = self._rect_fondo
            r.x, r.y = x0, y0
            r.width, r.height = x1 - x0, y1 - y0
            r.color = self._fondo_rgba[:3]
            r.opacity = self._fondo_rgba[3]
            r.draw()

    def _pintar(self):
        for i, item in enumerate(self._textos):
            sel = i == self._sel
            item.texto = ('» ' if sel else '  ') + self._texto_visible(i)
            item.color = self.color_sel if sel else self.color_base

    # -- navegación --------------------------------------------------------

    def mover(self, direccion):
        """Mueve la selección: 'arriba'/'abajo' o -1/+1."""
        if self._editando is not None:
            return
        if direccion in ('arriba', -1):
            self._sel = (self._sel - 1) % len(self._opciones)
        else:
            self._sel = (self._sel + 1) % len(self._opciones)
        self._pintar()

    def elegir(self):
        """Activa la opción seleccionada según su tipo.

        - acción: llama ``fn()``; si devuelve texto actualiza la
          etiqueta (opciones que ciclan valores).
        - check: alterna el valor y llama ``fn(valor)``.
        - input: entra en modo edición (ver ``escribir``).
        """
        texto, tipo, valor, fn = self._opciones[self._sel]
        if tipo == 'check':
            valor = not valor
            self._opciones[self._sel] = (texto, tipo, valor, fn)
            if fn:
                fn(valor)
            self._pintar()
            self.guardar()
            return valor
        if tipo == 'input':
            self._editando = self._sel
            self._editando_valor = str(valor or '')
            self._pintar()
            return None
        if fn is None:
            return None
        nuevo = fn()
        if isinstance(nuevo, str):
            self._opciones[self._sel] = (nuevo, tipo, valor, fn)
            self._pintar()
            self.guardar()
        return nuevo

    # -- persistencia -----------------------------------------------------

    def guardar(self, ruta=None):
        """Escribe los valores del menú en un JSON (check e input).

        Las acciones no se persisten (no tienen valor); su etiqueta
        cíclica sí queda guardada bajo el texto original si la opción
        es de tipo valor.
        """
        ruta = ruta or self._ruta
        if not ruta:
            return
        datos = {}
        for texto, tipo, valor, _fn in self._opciones:
            if tipo in ('check', 'input'):
                datos[texto] = valor
            else:
                # acción cíclica: guarda la etiqueta actual bajo la
                # clave base ("Calidad" -> "Calidad: media")
                datos[texto.split(':')[0].strip()] = texto
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    def cargar(self, ruta=None):
        """Lee el JSON y aplica los valores (llama a cada ``fn``)."""
        ruta = ruta or self._ruta
        if not ruta or not os.path.exists(ruta):
            return
        try:
            with open(ruta, encoding='utf-8') as f:
                datos = json.load(f)
        except (ValueError, OSError):
            return
        for i, (texto, tipo, valor, fn) in enumerate(self._opciones):
            base = texto.split(':')[0].strip()
            clave = texto if texto in datos else base
            if clave not in datos:
                continue
            valor = datos[clave]
            if tipo == 'check':
                valor = bool(valor)
                if fn:
                    fn(valor)
            elif tipo == 'input':
                valor = str(valor)
                if fn:
                    fn(valor)
            else:
                valor = datos[clave]          # etiqueta cíclica
                texto = valor
            self._opciones[i] = (texto, tipo, valor, fn)
        self._pintar()

    def fijar_texto(self, i, texto):
        """Cambia la etiqueta de la opción ``i`` (o por nombre)."""
        if isinstance(i, str):
            for n, (t, _tipo, _v, _f) in enumerate(self._opciones):
                if t.startswith(i) or i in t:
                    i = n
                    break
        op = self._opciones[i]
        self._opciones[i] = (texto, op[1], op[2], op[3])
        self._pintar()

    # -- edición de texto ----------------------------------------------------

    def escribir(self, caracter):
        """Agrega un caracter al input en edición (o borra con '\\b')."""
        if self._editando is None:
            return
        if caracter == '\b':
            self._editando_valor = self._editando_valor[:-1]
        else:
            self._editando_valor += caracter
        i = self._editando
        texto, tipo, _v, fn = self._opciones[i]
        self._opciones[i] = (texto, tipo, self._editando_valor, fn)
        self._pintar()

    def confirmar_edicion(self):
        """Cierra el input activo llamando ``fn(valor)``."""
        if self._editando is None:
            return
        i = self._editando
        texto, tipo, valor, fn = self._opciones[i]
        self._editando = None
        if fn:
            fn(valor)
        self._pintar()

    def cancelar_edicion(self):
        if self._editando is None:
            return
        self._editando = None
        self._pintar()

    # -- eventos de ventana -------------------------------------------------

    def _al_pulsar(self, simbolo, modificadores):
        if not self.esta_en_escena():
            return
        if self._editando is not None:
            if simbolo == key.ENTER:
                self.confirmar_edicion()
            elif simbolo == key.ESCAPE:
                self.cancelar_edicion()
            elif simbolo == key.BACKSPACE:
                self.escribir('\b')
            return True                     # no propaga (ESC no cierra)
        if simbolo in (key.UP, key.W):
            self.mover('arriba')
        elif simbolo in (key.DOWN, key.S):
            self.mover('abajo')
        elif simbolo in (key.ENTER, key.SPACE):
            self.elegir()

    def _al_texto(self, texto):
        if not self.esta_en_escena() or self._editando is None:
            return
        if texto.isprintable():
            self.escribir(texto)

    def _bajo_mouse(self, x, y):
        for i in range(len(self._opciones)):
            x0, y0, x1, y1 = self._rect_item(i)
            if x0 <= x <= x1 and y0 <= y <= y1:
                return i
        return None

    def _al_mover_mouse(self, x, y, dx, dy):
        if not self.esta_en_escena() or self._editando is not None:
            return
        i = self._bajo_mouse(x, y)
        if i is not None and i != self._sel:
            self._sel = i
            self._pintar()

    def _al_click_mouse(self, x, y, button, modifiers):
        if not self.esta_en_escena() or self._editando is not None:
            return
        if button & mouse.LEFT:
            i = self._bajo_mouse(x, y)
            if i is not None:
                self._sel = i
                self._pintar()
                self.elegir()

    def eliminar(self):
        for item in self._textos:
            item.eliminar()
        if self._titulo is not None:
            self._titulo.eliminar()
        super(Menu, self).eliminar()
