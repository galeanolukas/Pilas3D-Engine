# -*- encoding: utf-8 -*-
"""Bus de eventos propios del juego: ``pilas.eventos``.

Los actores, habilidades y tareas se hablan por nombre sin conocerse
entre sí — un arma emite ``'golpe'`` y el monstruo se entera sin una
referencia directa::

    pilas.eventos.cuando('golpe', lambda dmg: enemigo.decir('auch'))

    # o como decorador:
    @pilas.eventos.cuando('nivel_terminado')
    def al_terminar():
        pilas.escena = Menu(pilas)

    pilas.eventos.emitir('golpe', 10)   # args se pasan a los oyentes
"""


class Eventos(object):
    """Emisor/oyente por nombre. También usable como decorador."""

    def __init__(self):
        self._oyentes = {}

    def cuando(self, nombre, funcion=None):
        """Registra ``funcion`` para el evento ``nombre``.

        Sin ``funcion`` devuelve un decorador, así vale lo mismo
        ``pilas.eventos.cuando('x', f)`` que ``@cuando('x')``."""
        def registrar(fn):
            self._oyentes.setdefault(nombre, []).append(fn)
            return fn
        return registrar(funcion) if funcion is not None else registrar

    def emitir(self, nombre, *args, **kwargs):
        """Dispara el evento: llama a cada oyente con los args."""
        for fn in list(self._oyentes.get(nombre, [])):
            fn(*args, **kwargs)

    def olvidar(self, nombre, funcion=None):
        """Quita oyentes: solo ``funcion`` si se da, o todos."""
        if funcion is None:
            self._oyentes.pop(nombre, None)
        else:
            try:
                self._oyentes.get(nombre, []).remove(funcion)
            except ValueError:
                pass

    def limpiar(self):
        """Olvida todos los eventos (útil entre escenas/tests)."""
        self._oyentes.clear()
