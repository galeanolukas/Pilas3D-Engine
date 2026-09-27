# -*- encoding: utf-8 -*-
"""Habilidades prediseñadas: ``actor.aprender(pilas.habilidades.X)``.

Port del sistema de ``pilasengine.habilidades``: clases que heredan de
``Habilidad`` y que un actor puede aprender con ``aprender``.
"""

import difflib

from pilas3d.habilidades.habilidad import Habilidad
from pilas3d.habilidades.moverse_con_el_teclado import MoverseConElTeclado
from pilas3d.habilidades.rebotar_como_pelota import RebotarComoPelota
from pilas3d.habilidades.girar_constamente import GirarConstantemente
from pilas3d.habilidades.caminar_en_primera_persona import (
    CaminarEnPrimeraPersona)
from pilas3d.habilidades.seguir_al_actor import SeguirAlActor
from pilas3d.habilidades.mirar_al_actor import MirarAlActor
from pilas3d.habilidades.moverse_en_circulo import MoverseEnCirculo
from pilas3d.habilidades.moverse_como_coche import MoverseComoCoche
from pilas3d.habilidades.imitar import Imitar
from pilas3d.habilidades.aumentar_con_rueda import AumentarConRueda
from pilas3d.habilidades.rotar_con_mouse import RotarConMouse
from pilas3d.habilidades.puede_explotar import PuedeExplotar
from pilas3d.habilidades.pisa_plataformas import PisaPlataformas


class Habilidades(object):
    """Acceso a las habilidades, como ``pilas.habilidades``.

    >>> nave.aprender(pilas.habilidades.MoverseConElTeclado)
    """

    Habilidad = Habilidad
    MoverseConElTeclado = MoverseConElTeclado
    RebotarComoPelota = RebotarComoPelota
    GirarConstantemente = GirarConstantemente
    CaminarEnPrimeraPersona = CaminarEnPrimeraPersona
    SeguirAlActor = SeguirAlActor
    MirarAlActor = MirarAlActor
    MoverseEnCirculo = MoverseEnCirculo
    MoverseComoCoche = MoverseComoCoche
    Imitar = Imitar
    AumentarConRueda = AumentarConRueda
    RotarConMouse = RotarConMouse
    PuedeExplotar = PuedeExplotar
    PisaPlataformas = PisaPlataformas

    def buscar_habilidad_por_nombre(self, nombre):
        disponibles = {
            'moverseconelteclado': MoverseConElTeclado,
            'rebotarcomopelota': RebotarComoPelota,
            'girarconstantemente': GirarConstantemente,
            'caminarenprimerapersona': CaminarEnPrimeraPersona,
            'seguiralactor': SeguirAlActor,
            'miraralactor': MirarAlActor,
            'moverseencirculo': MoverseEnCirculo,
            'moversecomocoche': MoverseComoCoche,
            'imitar': Imitar,
            'aumentarconrueda': AumentarConRueda,
            'rotarconmouse': RotarConMouse,
            'puedeexplotar': PuedeExplotar,
            'pisaplataformas': PisaPlataformas,
        }
        try:
            return disponibles[nombre.lower()]
        except KeyError:
            similar = difflib.get_close_matches(
                nombre.lower(), disponibles.keys())
            if similar:
                raise NameError(
                    "no existe esa habilidad... quisiste decir "
                    "'%s' ?" % similar[0])
            raise NameError(
                "no existe una habilidad con el nombre '%s'" % nombre)


class ProxyHabilidades(object):
    """Acceso a las habilidades aprendidas: ``actor.habilidades.Nombre``."""

    def __init__(self, habilidades):
        self._habilidades = habilidades

    def __getattr__(self, nombre):
        for habilidad in self._habilidades:
            if habilidad.__class__.__name__ == nombre:
                return habilidad
        raise AttributeError(
            "El actor no tiene asignada la habilidad " + nombre)

    def __repr__(self):
        return '<Este actor tiene {0} habilidades>'.format(
            len(self._habilidades))
