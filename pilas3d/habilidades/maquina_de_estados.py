# -*- encoding: utf-8 -*-
"""MaquinaDeEstados: estados con nombre para comportamientos de NPC.

El patrón clásico para IA de juegos: cada estado es una función que
se ejecuta por frame mientras el actor está en ese estado, y el
actor mismo decide cuándo cambiar::

    def patrullar(npc):
        npc.rotacion_y += 1
        if npc.distancia_plana_con(jugador) < 4:
            npc.cambiar_estado('perseguir')

    def perseguir(npc):
        npc.x += 0.05 if jugador.x > npc.x else -0.05
        if npc.distancia_plana_con(jugador) > 6:
            npc.cambiar_estado('patrullar')

    npc.aprender(pilas.habilidades.MaquinaDeEstados,
                 estados={'patrullar': patrullar,
                          'perseguir': perseguir},
                 inicial='patrullar')

Un estado también puede ser un dict con claves opcionales
``entrar``/``actualizar``/``salir`` (callables que reciben al actor)::

    {'entrar': lambda npc: npc.decir('te vi!'),
     'actualizar': perseguir,
     'salir': lambda npc: npc.decir('se escapó…')}
"""

from pilas3d.habilidades.habilidad import Habilidad


class MaquinaDeEstados(Habilidad):
    """Agrega ``estado``, ``cambiar_estado`` y ``agregar_estado``."""

    def iniciar(self, receptor, estados=None, inicial=None):
        super(MaquinaDeEstados, self).iniciar(receptor)
        receptor.estados = dict(estados or {})
        receptor.estado = inicial or \
            next(iter(receptor.estados), None)
        receptor.cambiar_estado = self._cambiar_estado
        receptor.agregar_estado = self._agregar_estado

    # -- API que queda en el actor -------------------------------------------

    def _agregar_estado(self, nombre, estado):
        self.receptor.estados[nombre] = estado
        if self.receptor.estado is None:
            self.receptor.estado = nombre

    def _cambiar_estado(self, nombre):
        r = self.receptor
        if nombre == r.estado:
            return
        if nombre not in r.estados:
            raise KeyError("no existe el estado '%s'" % nombre)
        self._llamar(r, 'salir')
        r.estado = nombre
        self._llamar(r, 'entrar')

    def _llamar(self, r, fase):
        estado = r.estados.get(r.estado)
        fn = estado.get(fase) if isinstance(estado, dict) \
            else (estado if fase == 'actualizar' else None)
        if callable(fn):
            fn(r)

    def actualizar(self):
        r = self.receptor
        if r.estado is not None and r.esta_en_escena():
            self._llamar(r, 'actualizar')
