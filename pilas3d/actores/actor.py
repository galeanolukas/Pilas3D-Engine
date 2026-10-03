# -*- encoding: utf-8 -*-
"""Actor base de pilas3d.

Equivalente a ``pilasengine.actores.actor.Actor`` pero con geometría
3D: posición (x, y, z) real, rotación por eje y escala por eje.
"""

import math

from pyglet.gl import glActiveTexture, glBindTexture, \
    glTexParameteri, GL_TEXTURE0
from pyglet.gl import GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T
from pyglet.gl import GL_REPEAT
from pyglet.math import Mat4, Vec3

from pilas3d import colores, shaders
from pilas3d.habilidades import ProxyHabilidades


class Actor(object):
    """Clase base para todos los actores 3D.

    Ejemplo de uso::

        pilas = pilas3d.iniciar()
        cubo = pilas.actores.Cubo()
        cubo.x = 3
        cubo.rotacion_y = 45
    """

    #: Si es True se dibuja en el overlay 2D (texto), no en la escena 3D.
    es_overlay = False

    def __init__(self, pilas, x=0, y=0, z=0):
        self.pilas = pilas

        self._x = x
        self._y = y
        self._z = z
        self._rotacion_x = 0.0
        self._rotacion_y = 0.0
        self._rotacion_z = 0.0
        self._escala_x = 1.0
        self._escala_y = 1.0
        self._escala_z = 1.0
        self._transparencia = 0
        self._color = colores.blanco
        self._imagen = None
        self._textura = None
        #: Material compuesto opcional (normal/AO/rugosidad) —
        #: ``actor.material = pilas.materiales.desde_carpeta(dir)``.
        self.material = None
        self._uv_escala = (1.0, 1.0)
        self._uv_desplazamiento = (0.0, 0.0)

        #: Radio para ``camara.disparar_rayo``; None usa
        #: ``radio_de_colision``. Útil en carteles altos.
        self.radio_de_disparo = None

        self.radio_de_colision = 1.0
        #: Con ``True`` el actor se dibuja a color plano, sin
        #: iluminación (focos de lámparas, sprites brillantes).
        self.sin_luz = False
        #: Dirección ``(x, z)`` hacia donde "mira" el actor cuando
        #: ``rotacion_y = 0``. Los personajes del motor miran +Z;
        #: los glTF suelen mirar -Z — p. ej. ``lobo.frente = (0, -1)``.
        #: Las habilidades la usan para orientar al actor.
        self.frente = (0.0, 1.0)
        self._interpolaciones = []
        self._habilidades = []
        self.habilidades = ProxyHabilidades(self._habilidades)
        self._vertex_list = None
        self._modo = None
        #: Índices para dibujar con vertex list indexado (los modelos
        #: glTF los usan: no duplican vértices y el skinning es más
        #: barato). ``None`` = draw plano con los vértices en orden.
        #: Las subclases pueden setearlo antes de ``super().__init__``.
        if not hasattr(self, '_indices'):
            self._indices = None
        self._matriz = None
        self._matriz_sucia = True

        escena = pilas.escena_actual()
        if escena is not None:
            escena.agregar_actor(self)
        self.iniciar()

    def iniciar(self):
        """Hook de pilas-engine: se llama una vez al crear el actor.

        Redefinilo en tus propios actores para configurarlo::

            class Nave(Actor):
                def iniciar(self):
                    self.aprender(pilas.habilidades.MoverseConElTeclado)
        """
        pass

    # -- posición ---------------------------------------------------------

    def _definir_o_interpolar(self, atributo, valor):
        """Si el valor es una interpolación, la agenda y retorna True.

        Soporta la sintaxis de pilas::

            actor.x = [100]              # Lineal, 1 segundo
            actor.x = ([100, -50], 3)    # (valores, duración)
            actor.x = interpolaciones.ReboteFinal([2])
        """
        from pilas3d.interpolaciones import Interpolacion, Lineal

        if isinstance(valor, Interpolacion):
            valor.iniciar(self, atributo)
        elif isinstance(valor, list):
            Lineal(valor).iniciar(self, atributo)
        elif isinstance(valor, tuple):
            valores, duracion = valor
            Lineal(valores, duracion=duracion).iniciar(self, atributo)
        else:
            return False
        return True

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, valor):
        if self._definir_o_interpolar('x', valor):
            return
        self._x = valor
        self._matriz_sucia = True

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, valor):
        if self._definir_o_interpolar('y', valor):
            return
        self._y = valor
        self._matriz_sucia = True

    @property
    def z(self):
        """Profundidad real (en pilas 2D era solo el orden de dibujo)."""
        return self._z

    @z.setter
    def z(self, valor):
        if self._definir_o_interpolar('z', valor):
            return
        self._z = valor
        self._matriz_sucia = True

    @property
    def posicion(self):
        return (self._x, self._y, self._z)

    @posicion.setter
    def posicion(self, valor):
        self._x, self._y, self._z = valor
        self._matriz_sucia = True

    # -- rotación (en grados, como en pilas) -------------------------------

    @property
    def rotacion_x(self):
        return self._rotacion_x

    @rotacion_x.setter
    def rotacion_x(self, valor):
        if self._definir_o_interpolar('rotacion_x', valor):
            return
        self._rotacion_x = valor
        self._matriz_sucia = True

    @property
    def rotacion_y(self):
        return self._rotacion_y

    @rotacion_y.setter
    def rotacion_y(self, valor):
        if self._definir_o_interpolar('rotacion_y', valor):
            return
        self._rotacion_y = valor
        self._matriz_sucia = True

    @property
    def rotacion_z(self):
        return self._rotacion_z

    @rotacion_z.setter
    def rotacion_z(self, valor):
        if self._definir_o_interpolar('rotacion_z', valor):
            return
        self._rotacion_z = valor
        self._matriz_sucia = True

    @property
    def rotacion(self):
        """Alias de ``rotacion_y``: el giro "plano" equivalente al 2D."""
        return self._rotacion_y

    @rotacion.setter
    def rotacion(self, valor):
        self.rotacion_y = valor

    def mirar_hacia(self, x, z):
        """Orienta el actor en Y para que su ``frente`` apunte al
        punto ``(x, z)`` del plano horizontal.

        Tiene en cuenta ``actor.frente``: los personajes del motor
        miran +Z por defecto; un modelo que mira -Z (la mayoría de
        los glTF) se corrige con ``actor.frente = (0, -1)`` una sola
        vez y todas las habilidades orientan bien.
        """
        dx, dz = x - self.x, z - self.z
        if not (dx or dz):
            return
        fx, fz = self.frente
        self.rotacion_y = math.degrees(math.atan2(dx, dz)) - \
            math.degrees(math.atan2(fx, fz))

    # -- escala -------------------------------------------------------------

    @property
    def escala(self):
        return self._escala_x

    @escala.setter
    def escala(self, valor):
        if self._definir_o_interpolar('escala', valor):
            return
        self._escala_x = self._escala_y = self._escala_z = valor
        self._matriz_sucia = True

    @property
    def escala_x(self):
        return self._escala_x

    @escala_x.setter
    def escala_x(self, valor):
        if self._definir_o_interpolar('escala_x', valor):
            return
        self._escala_x = valor
        self._matriz_sucia = True

    @property
    def escala_y(self):
        return self._escala_y

    @escala_y.setter
    def escala_y(self, valor):
        if self._definir_o_interpolar('escala_y', valor):
            return
        self._escala_y = valor
        self._matriz_sucia = True

    @property
    def escala_z(self):
        return self._escala_z

    @escala_z.setter
    def escala_z(self, valor):
        if self._definir_o_interpolar('escala_z', valor):
            return
        self._escala_z = valor
        self._matriz_sucia = True

    # -- apariencia ----------------------------------------------------------

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, valor):
        self._color = valor
        self._reconstruir_gl()

    @property
    def transparencia(self):
        """De 0 (opaco) a 100 (invisible)."""
        return self._transparencia

    @transparencia.setter
    def transparencia(self, valor):
        if self._definir_o_interpolar('transparencia', valor):
            return
        self._transparencia = valor
        self._reconstruir_gl()

    @property
    def imagen(self):
        """Textura del actor: una ruta PNG/JPG o una imagen de pyglet."""
        return self._imagen

    @imagen.setter
    def imagen(self, ruta):
        self._imagen = ruta
        self._textura = None

    # -- colisiones -----------------------------------------------------------

    def distancia_con(self, otro):
        """Distancia euclidiana 3D entre los centros de dos actores."""
        return math.dist(self.posicion, otro.posicion)

    def colisiona_con(self, otro):
        """True si las esferas de colisión de ambos actores se tocan."""
        radios = self.radio_de_colision + otro.radio_de_colision
        return self.distancia_con(otro) <= radios

    def distancia_plana_con(self, otro):
        """Distancia en el plano XZ, ignorando la altura ``y``."""
        return math.hypot(self.x - otro.x, self.z - otro.z)

    def colisiona_en_plano_con(self, otro):
        """Colisión tipo Doom: solo sobre el plano XZ.

        Útil cuando dos actores tienen distinta ``y`` (el jugador
        apoyado en el piso, un enemigo flotando, etc.).
        """
        radios = self.radio_de_colision + otro.radio_de_colision
        return self.distancia_plana_con(otro) <= radios

    # -- habilidades ----------------------------------------------------------

    def aprender(self, clase_habilidad, *args, **kwargs):
        """Aprende una habilidad (clase que hereda de ``Habilidad``).

        >>> cubo.aprender(pilas.habilidades.MoverseConElTeclado)
        """
        from pilas3d.habilidades import Habilidad

        if isinstance(clase_habilidad, str):
            clase_habilidad = (
                self.pilas.habilidades.buscar_habilidad_por_nombre(
                    clase_habilidad))

        if not issubclass(clase_habilidad, Habilidad):
            raise TypeError(
                "El actor solo puede aprender clases que hereden "
                "de pilas3d.habilidades.Habilidad")

        if self.tiene_habilidad(clase_habilidad):
            self.eliminar_habilidad(clase_habilidad)

        habilidad = clase_habilidad(self.pilas)
        habilidad.iniciar(self, *args, **kwargs)
        self._habilidades.append(habilidad)
        return habilidad

    def tiene_habilidad(self, clase_habilidad):
        return clase_habilidad in [h.__class__ for h in self._habilidades]

    def obtener_habilidad(self, clase_habilidad):
        for h in self._habilidades:
            if h.__class__ == clase_habilidad:
                return h
        return None

    def eliminar_habilidad(self, clase_habilidad):
        habilidad = self.obtener_habilidad(clase_habilidad)
        if habilidad:
            self._habilidades.remove(habilidad)

    def eliminar_habilidades(self):
        for h in list(self._habilidades):
            self._habilidades.remove(h)

    def actualizar_habilidades(self):
        for h in list(self._habilidades):
            h.actualizar()

    def _actualizar_interpolaciones(self):
        """Avanza los tweens activos (``actor.x = [100]``, etc.)."""
        dt = self.pilas.dt
        self._interpolaciones = [
            t for t in self._interpolaciones if not t.avanzar(dt)]

    def pre_actualizar(self):
        """Actualiza habilidades antes de ``actualizar`` (como en pilas)."""
        self._actualizar_interpolaciones()
        self.actualizar_habilidades()

    # -- ciclo de vida --------------------------------------------------------

    def actualizar(self):
        """Se llama automáticamente ~60 veces por segundo.

        Redefinilo en tus propios actores para agregar comportamiento.
        """
        pass

    def terminar(self):
        """Se ejecuta justo antes de eliminar el actor de la escena."""
        pass

    def esta_en_escena(self):
        """True si el actor sigue vivo en la escena actual."""
        escena = self.pilas.escena_actual()
        return escena is not None and self in escena.actores

    def decir(self, texto, duracion=3):
        """Muestra un globo de diálogo sobre el actor.

        Crea (y reutiliza) un ``Globo`` pegado al actor — textos
        largos se reparten en varios globos que avanzan solos.

        >>> cubo.decir('hola!', duracion=3)
        """
        from pilas3d.actores.globo import Globo
        globo = getattr(self, '_globo', None)
        if globo is None or not globo.esta_en_escena():
            globo = Globo(self.pilas, actor=self, texto='')
            self._globo = globo
        globo.decir(texto, duracion=duracion)
        return globo

    def eliminar(self):
        self.terminar()
        self.eliminar_habilidades()
        if self._vertex_list is not None:
            self._vertex_list.delete()
            self._vertex_list = None
        escena = self.pilas.escena_actual()
        if escena is not None:
            escena.eliminar_actor(self)

    # -- render ---------------------------------------------------------------

    def _generar_geometria(self):
        """Retorna (posiciones, normales, modo) o (..., colores)."""
        raise NotImplementedError(
            "Redefini _generar_geometria en la subclase"
        )

    def _colores_planos(self, cantidad):
        r, g, b = colores.normalizar(self._color)
        a = 1.0 - self._transparencia / 100.0
        return [r, g, b, a] * cantidad

    def _colores_tenidos(self, colores_vertices):
        """Multiplica los colores del modelo por ``self._color``
        (tinte) y la transparencia. Sirve para 'pintar' actores que
        ya traen colores por vértice (materiales de .obj/.glb)."""
        r, g, b = colores.normalizar(self._color)
        a = 1.0 - self._transparencia / 100.0
        out = []
        for i in range(0, len(colores_vertices), 4):
            out += [colores_vertices[i] * r,
                    colores_vertices[i + 1] * g,
                    colores_vertices[i + 2] * b,
                    colores_vertices[i + 3] * a]
        return out

    def _colores_efectivos(self, colores_vertices, cantidad):
        """Colores finales del draw: los del modelo teñidos por
        ``color``/``transparencia``, o planos si no trae."""
        if colores_vertices is None:
            return self._colores_planos(cantidad)
        if self._color != colores.blanco or self._transparencia:
            return self._colores_tenidos(colores_vertices)
        return colores_vertices

    def _reconstruir_gl(self):
        if self._vertex_list is not None:
            self._vertex_list.delete()
            self._vertex_list = None

    def _cargar_textura(self):
        if hasattr(self._imagen, "get_texture"):
            # Ya es una imagen/textura de pyglet (p. ej. generada).
            self._textura = self._imagen.get_texture()
        else:
            from pyglet.image import load

            self._textura = load(
                self._resolver_imagen(self._imagen)).get_texture()

    @staticmethod
    def _resolver_imagen(ruta):
        """Busca la imagen en cwd, en ``pilas3d/data/`` y en el
        paquete — como hace ``sonidos.cargar`` con el audio."""
        import os
        base = os.path.dirname(os.path.dirname(__file__))
        for candidato in (ruta,
                          os.path.join(base, 'data', ruta),
                          os.path.join(base, ruta)):
            if os.path.exists(candidato):
                return candidato
        return ruta        # que pyglet dé su error habitual
        glBindTexture(GL_TEXTURE_2D, self._textura.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    def _construir_gl(self):
        datos = self._generar_geometria()
        posiciones, normales, modo = datos[0], datos[1], datos[2]
        colores_vertices = datos[3] if len(datos) > 3 else None
        uvs = datos[4] if len(datos) > 4 else None
        cantidad = len(posiciones) // 3

        colores_vertices = self._colores_efectivos(
            colores_vertices, cantidad)
        if uvs is None:
            uvs = [0.0] * (cantidad * 2)

        self._modo = modo
        programa = shaders.obtener_programa()
        if self._indices is not None:
            self._vertex_list = programa.vertex_list_indexed(
                cantidad,
                modo,
                self._indices,
                position=("f", posiciones),
                normal=("f", normales),
                color=("f", colores_vertices),
                texcoords=("f", uvs),
            )
        else:
            self._vertex_list = programa.vertex_list(
                cantidad,
                modo,
                position=("f", posiciones),
                normal=("f", normales),
                color=("f", colores_vertices),
                texcoords=("f", uvs),
            )

    def matriz_modelo(self):
        if self._matriz_sucia or self._matriz is None:
            matriz = Mat4.from_translation(Vec3(self._x, self._y, self._z))
            if self._rotacion_y:
                matriz = matriz @ Mat4.from_rotation(
                    math.radians(self._rotacion_y), Vec3(0, 1, 0)
                )
            if self._rotacion_x:
                matriz = matriz @ Mat4.from_rotation(
                    math.radians(self._rotacion_x), Vec3(1, 0, 0)
                )
            if self._rotacion_z:
                matriz = matriz @ Mat4.from_rotation(
                    math.radians(self._rotacion_z), Vec3(0, 0, 1)
                )
            matriz = matriz @ Mat4.from_scale(
                Vec3(self._escala_x, self._escala_y, self._escala_z)
            )
            self._matriz = matriz
            self._matriz_sucia = False
        return self._matriz

    def dibujar(self):
        """Dibuja el actor. Se invoca desde el bucle principal."""
        if self._vertex_list is None:
            self._construir_gl()
        programa = shaders.obtener_programa()
        programa["modelo"] = self.matriz_modelo()
        programa["punto_tamano"] = getattr(self, 'punto_tamano', 1.0)
        programa["uv_escala"] = self._uv_escala
        programa["uv_desplazamiento"] = self._uv_desplazamiento
        programa["sin_luz"] = self.sin_luz
        mat = self.material
        # la base del material reemplaza a imagen si no hay una
        textura_base = None
        if self._imagen is not None:
            if self._textura is None:
                self._cargar_textura()
            textura_base = self._textura
        elif mat is not None:
            textura_base = mat.textura('base')
        glActiveTexture(GL_TEXTURE0)
        if textura_base is not None:
            glBindTexture(GL_TEXTURE_2D, textura_base.id)
            programa["textura"] = 0
            programa["usar_textura"] = True
        else:
            programa["usar_textura"] = False
        # mapas compuestos en las unidades 1-3 (normal, AO, rugosidad)
        for unidad, slot, unif in (
                (1, 'normal', 'normal_map'),
                (2, 'ao', 'ao_map'),
                (3, 'rugosidad', 'rugosidad_map')):
            tex = mat.textura(slot) if mat is not None else None
            programa["usar_" + slot] = tex is not None
            if tex is not None:
                glActiveTexture(GL_TEXTURE0 + unidad)
                glBindTexture(GL_TEXTURE_2D, tex.id)
                glTexParameteri(GL_TEXTURE_2D,
                                GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D,
                                GL_TEXTURE_WRAP_T, GL_REPEAT)
                programa[unif] = unidad
        glActiveTexture(GL_TEXTURE0)
        self._vertex_list.draw(self._modo)
