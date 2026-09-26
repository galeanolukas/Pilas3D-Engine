# -*- encoding: utf-8 -*-
"""Mapa definido por una matriz de caracteres (versión 3D del Mapa
de pilas-engine).

Cada símbolo de la matriz invoca una función constructora que crea el
actor correspondiente en esa celda::

    MAPA = '''
    ########
    #......#
    #..E...#
    ########
    '''

    def hacer_pared(pilas, x, z):
        return pilas.actores.Pared(x=x, z=z, ancho=2, alto=3,
                                   profundidad=2)

    def hacer_enemigo(pilas, x, z):
        return Enemigo(pilas, x=x, z=z)

    mapa = pilas.actores.Mapa(MAPA, {'#': hacer_pared, 'E': hacer_enemigo})

Los símbolos sin entrada en el diccionario se ignoran (celda vacía).
La celda (0, 0) de la matriz queda en el -x/-z del mapa; el conjunto
queda centrado en la posición del Mapa.
"""

from pilas3d.actores.actor import Actor


class Mapa(Actor):
    def __init__(self, pilas, matriz, simbolos, tamano_celda=2.0,
                 x=0, y=0, z=0):
        if isinstance(matriz, str):
            matriz = [l for l in matriz.strip('\n').split('\n')]
        self.matriz = matriz
        self.simbolos = simbolos
        self.tamano_celda = tamano_celda
        self.filas = len(matriz)
        self.columnas = max(len(f) for f in matriz)
        self.creados = []
        super(Mapa, self).__init__(pilas, x=x, y=y, z=z)
        self._construir()

    def _construir(self):
        t = self.tamano_celda
        for i, fila in enumerate(self.matriz):
            for j, simbolo in enumerate(fila):
                fabricar = self.simbolos.get(simbolo)
                if fabricar is None:
                    continue
                cx = self.x + (j - self.columnas / 2.0 + 0.5) * t
                cz = self.z + (i - self.filas / 2.0 + 0.5) * t
                self.creados.append(fabricar(self.pilas, cx, cz))

    def celda(self, fila, columna):
        """Retorna el símbolo de la celda (fila, columna)."""
        return self.matriz[fila][columna]

    def _generar_geometria(self):
        return [], [], 0, None, []

    def dibujar(self):
        pass  # El mapa en sí no dibuja nada: dibujan los actores creados.
