# -*- encoding: utf-8 -*-
"""Personaje por capas (paper-doll): un ``PersonajeSprite`` base más
hojas extra dibujadas encima — ropa, cabello, armaduras… Cada capa
es un sprite esclavo que replica fila, cuadro, variante y espejo
del personaje base::

    pj = pilas.actores.PersonajeCapas('base.personaje.json')
    pj.agregar_capa('ropa1.png', columnas=8, filas=4)
    pj.agregar_capa('cabello.png', columnas=8, filas=4)

Las capas pueden ser otra hoja con la **misma** grilla (los
defaults) o declarar su propia ``columnas``/``filas``/``variantes``
(p. ej. la base 32x4 con 4 variantes y la ropa 8x4 sin variantes).
En el ``.personaje.json`` se declaran con ``capas``::

    {"hoja": "base.png", "columnas": 8, "filas": 4, ...,
     "capas": ["cabello.png",
               {"hoja": "ropa1.png", "columnas": 8, "filas": 4,
                "variantes": 1}]}
"""

from pilas3d.actores.personaje_sprite import PersonajeSprite


class _Capa(PersonajeSprite):
    """Sprite esclavo de un ``PersonajeCapas``: no anima solo —
    cada frame copia posición (con un offset mínimo hacia la cámara
    para no pelear en profundidad), fila, cuadro, variante, espejo
    y transparencia del personaje base, y encuadra con su grilla."""

    #: separación hacia la cámara por nivel de capa (unidades)
    SEPARACION = 0.006

    def __init__(self, pilas, base, nivel, hoja, seguir_variante=False,
                 **kw):
        self._base = base
        self._nivel = nivel
        #: True para que la capa copie la variante del base cada frame
        #: (la ropa cambia de color junto a la piel); False deja la
        #: variante propia (pelo de un color distinto a la piel)
        self.seguir_variante = seguir_variante
        kw.setdefault('x', base.x)
        kw.setdefault('y', base.y)
        kw.setdefault('z', base.z)
        kw.setdefault('ancho', base.ancho)
        kw.setdefault('alto', base.alto)
        kw.setdefault('velocidad', base.velocidad)
        super(_Capa, self).__init__(pilas, hoja, **kw)
        self.radio_de_colision = 0.0      # las capas no colisionan

    def actualizar(self):
        b = self._base
        cam = self.pilas.escena_actual().camara
        d = cam.direccion()
        s = self._nivel * self.SEPARACION
        self._x = b.x - d.x * s
        self._y = b.y - d.y * s
        self._z = b.z - d.z * s
        # mismo fotograma dentro de la grilla propia
        self._fila = b._fila % self.filas
        self._flip = b._flip
        if self.seguir_variante:
            self._variante = b._variante % self.variantes
        self.cuadro = b.cuadro
        self._encuadrar()
        self._transparencia = b._transparencia


class PersonajeCapas(PersonajeSprite):
    """``PersonajeSprite`` con hojas apiladas (estilo paper-doll).

    El personaje base es el que se mueve/anima; las capas lo siguen
    y muestran el mismo fotograma de su propia hoja (ropa, pelo…).
    """

    def __init__(self, pilas, imagen, capas=(), **kw):
        self._capas = []            # actores _Capa
        self._nivel_capas = 0
        super(PersonajeCapas, self).__init__(pilas, imagen, **kw)
        # capas declaradas en el .personaje.json o por kwargs
        for c in self._manifiesto.get('capas', ()):
            if isinstance(c, dict):
                c = dict(c)
                hoja = c.pop('hoja')
                self.agregar_capa(hoja, **c)
            else:
                self.agregar_capa(c)
        for c in capas:
            if isinstance(c, dict):
                c = dict(c)
                hoja = c.pop('hoja')
                self.agregar_capa(hoja, **c)
            else:
                self.agregar_capa(c)

    @property
    def capas(self):
        """Los actores-capa apilados sobre el personaje base."""
        return list(self._capas)

    def agregar_capa(self, hoja, seguir_variante=False, **kw):
        """Apila una hoja encima del personaje (ropa, cabello...).

        ``columnas``/``filas``/``variantes``/``variante`` por defecto
        son las de la base; pasar otras si la capa tiene su propia
        grilla o color (una capa ``.personaje.json`` trae las suyas).
        ``seguir_variante=True`` ata la variante de la capa a la del
        base (la ropa sigue al tono de piel); por defecto la capa
        mantiene su propia variante (pelo de otro color)."""
        self._nivel_capas += 1
        if not (isinstance(hoja, str)
                and hoja.lower().endswith('.json')):
            kw.setdefault('columnas', self.columnas)
            kw.setdefault('filas', self.filas)
            kw.setdefault('variantes', self.variantes)
            kw.setdefault('variante', self._variante)
            kw.setdefault('direcciones', dict(self._mapa))
            kw.setdefault('espejar', dict(self._espejar))
        capa = _Capa(self.pilas, self, self._nivel_capas, hoja,
                     seguir_variante=seguir_variante, **kw)
        self._capas.append(capa)
        return capa

    def quitar_capa(self, indice=-1):
        """Quita una capa por índice (default: la última agregada)."""
        capa = self._capas.pop(indice)
        capa.eliminar()
        return capa

    def manifiesto(self, hoja=None):
        man = super(PersonajeCapas, self).manifiesto(hoja=hoja)
        if self._capas:
            base_grid = (self.columnas, self.filas, self.variantes)
            capas = []
            for c in self._capas:
                otra_grid = (c.columnas, c.filas, c.variantes) != base_grid
                if not otra_grid and not c._variante \
                        and not c.seguir_variante:
                    capas.append(c.imagen)          # string simple
                    continue
                d = {'hoja': c.imagen}
                if otra_grid:
                    d.update(columnas=c.columnas, filas=c.filas,
                             variantes=c.variantes)
                if c._variante:
                    d['variante'] = c._variante
                if c.seguir_variante:
                    d['seguir_variante'] = True
                capas.append(d)
            man['capas'] = capas
        return man

    def eliminar(self):
        for capa in self._capas:
            capa.eliminar()
        self._capas = []
        super(PersonajeCapas, self).eliminar()
