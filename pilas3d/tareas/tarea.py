# -*- encoding: utf-8 -*-
"""Tareas programables del planificador (port de pilasengine.tareas)."""


class Tarea(object):
    """Una tarea que el planificador ejecuta cuando llega su ``time_out``.

    :param una_vez: si es True se elimina luego de ejecutarse; si es
                    False se reprograma cada ``dt`` segundos.
    """

    def __init__(self, planificador, una_vez, time_out, dt, funcion,
                 *args, **kwargs):
        self.planificador = planificador
        self.una_vez = una_vez
        self.time_out = time_out
        self.dt = dt
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs

    def ejecutar(self):
        return self.funcion(*self.args, **self.kwargs)

    def eliminar(self):
        """Quita la tarea del planificador."""
        self.planificador.eliminar_tarea(self)

    def terminar(self):
        """Alias de eliminar."""
        self.eliminar()


class TareaCondicional(Tarea):
    """Tarea que se repite mientras la función retorne verdadero."""

    def ejecutar(self):
        retorno = super(TareaCondicional, self).ejecutar()
        if not retorno:
            self.una_vez = True
