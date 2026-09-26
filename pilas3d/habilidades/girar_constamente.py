# -*- encoding: utf-8 -*-

from pilas3d.habilidades.habilidad import Habilidad


class GirarConstantemente(Habilidad):
    """Gira al actor de forma continua alrededor de un eje.

    >>> cubo.aprender(pilas.habilidades.GirarConstantemente,
    ...               velocidad=90, eje='y')
    """

    def iniciar(self, receptor, velocidad=90, eje='y'):
        super(GirarConstantemente, self).iniciar(receptor)
        if eje not in ('x', 'y', 'z'):
            raise ValueError("eje debe ser 'x', 'y' o 'z'")
        self.velocidad = velocidad
        self.atributo = 'rotacion_' + eje

    def actualizar(self):
        actual = getattr(self.receptor, self.atributo)
        setattr(self.receptor, self.atributo,
                actual + self.velocidad * self.pilas.dt)
