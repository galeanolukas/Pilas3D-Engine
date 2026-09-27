# -*- encoding: utf-8 -*-

from pilas3d.habilidades.habilidad import Habilidad


class Imitar(Habilidad):
    """Copia la posición (y opcionalmente la rotación) de otro actor.

    Sirve, por ejemplo, para sombreros, mascotas o arrastrar un objeto
    con otro.

    >>> gorro.aprender(pilas.habilidades.Imitar, actor=jugador,
    ...                desplazar=(0, 1.2, 0))
    """

    def iniciar(self, receptor, actor, desplazar=(0, 0, 0),
                rotacion=True):
        super(Imitar, self).iniciar(receptor)
        self.actor = actor
        self.desplazar = desplazar
        self.rotacion = rotacion

    def actualizar(self):
        if self.actor not in self.pilas.escena_actual().actores:
            return
        a = self.actor
        r = self.receptor
        r.x = a.x + self.desplazar[0]
        r.y = a.y + self.desplazar[1]
        r.z = a.z + self.desplazar[2]
        if self.rotacion:
            r.rotacion_y = a.rotacion_y
