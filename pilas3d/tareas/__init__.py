# -*- encoding: utf-8 -*-
"""Planificador de tareas: ``pilas.tareas.siempre(2, mi_funcion)``.

Cada escena tiene su propio planificador; ``pilas.tareas`` apunta al
de la escena actual, como en pilas-engine.
"""

from pilas3d.tareas.tarea import Tarea, TareaCondicional


class Tareas(object):
    """Contenedor de tareas a ejecutar por tiempo."""

    def __init__(self, escena, pilas):
        self.escena = escena
        self.pilas = pilas
        self.tareas_planificadas = []
        self.contador_de_tiempo = 0.0

    def obtener_cantidad_de_tareas_planificadas(self):
        return len(self.tareas_planificadas)

    def actualizar(self, dt):
        """Ejecuta las tareas cuyo tiempo ya llegó.

        :param dt: segundos desde la llamada anterior.
        """
        self.contador_de_tiempo += dt
        a_eliminar = []

        for tarea in list(self.tareas_planificadas):
            if self.contador_de_tiempo >= tarea.time_out:
                tarea.ejecutar()
                if tarea.una_vez:
                    a_eliminar.append(tarea)
                else:
                    tarea.time_out += tarea.dt

        for tarea in a_eliminar:
            if tarea in self.tareas_planificadas:
                self.tareas_planificadas.remove(tarea)

    def una_vez(self, time_out, funcion, *args, **kwargs):
        """Ejecuta la función una sola vez dentro de ``time_out`` segundos."""
        tarea = Tarea(self, True, self.contador_de_tiempo + time_out,
                      time_out, funcion, *args, **kwargs)
        self.tareas_planificadas.append(tarea)
        return tarea

    def siempre(self, time_out, funcion, *args, **kwargs):
        """Ejecuta la función cada ``time_out`` segundos, sin fin."""
        tarea = Tarea(self, False, self.contador_de_tiempo + time_out,
                      time_out, funcion, *args, **kwargs)
        self.tareas_planificadas.append(tarea)
        return tarea

    def condicional(self, time_out, funcion, *args, **kwargs):
        """Ejecuta cada ``time_out`` segundos mientras retorne verdadero."""
        tarea = TareaCondicional(
            self, False, self.contador_de_tiempo + time_out,
            time_out, funcion, *args, **kwargs
        )
        self.tareas_planificadas.append(tarea)
        return tarea

    def agregar(self, *args, **kwargs):
        return self.condicional(*args, **kwargs)

    def eliminar_tarea(self, tarea):
        if tarea in self.tareas_planificadas:
            self.tareas_planificadas.remove(tarea)

    def eliminar_todas(self):
        self.tareas_planificadas = []
