# -*- encoding: utf-8 -*-
"""Editor de personajes-sprite: arma el ``.personaje.json`` de un
``PersonajeSprite`` viendo el billboard caminar en 3D en vivo.

    pilas3d-personaje vikingo.png -c 5 -f 2
    pilas3d-personaje vikingo.personaje.json

Teclas:
  WASD/flechas  mueve el sprite — se ve la fila según la dirección
  TAB           elige el slot: las 4 direcciones y los estados
  Q / E         fila anterior / siguiente del slot elegido
  M             espejar la dirección desde otra (cicla por fuentes)
  N             nuevo estado (atacar, morir, saltar, correr...)
  B             borra el estado elegido
  X / K         estado cíclico / quedarse en el último cuadro
  U / I         velocidad -/+
  ESPACIO       previsualiza el slot (pose o estado)
  G             guarda el .personaje.json
  H             muestra/oculta la ayuda
  ESC           salir
"""

import argparse
import os
import sys

import pilas3d
from pilas3d.actores.personaje_sprite import PersonajeSprite

DIRECCIONES = ['abajo', 'izquierda', 'derecha', 'arriba']
NOMBRES_ESTADO = ['atacar', 'morir', 'saltar', 'correr', 'especial']


def _slots(pj):
    """Slots editables: las direcciones + los estados existentes."""
    return DIRECCIONES + [n for n in pj._estados
                          if n not in DIRECCIONES]


def cli(argv=None):
    ap = argparse.ArgumentParser(
        prog='pilas3d-personaje',
        description='Editor de personajes-sprite (.personaje.json)')
    ap.add_argument('archivo',
                    help='hoja .png (con -c/-f) o .personaje.json')
    ap.add_argument('-c', '--columnas', type=int, default=None,
                    help='cuadros por fila (obligatorio con .png)')
    ap.add_argument('-f', '--filas', type=int, default=None,
                    help='cantidad de filas (obligatorio con .png)')
    ap.add_argument('-o', '--salida', default=None,
                    help='ruta del .personaje.json (default: junto '
                         'a la hoja, mismo nombre)')
    a = ap.parse_args(argv)

    pilas = pilas3d.iniciar(ancho=800, alto=600,
                            titulo='pilas3d — editor de personaje')
    pilas.actores.Cielo('dia')
    pilas.actores.Piso(tamano=24, divisiones=24)

    es_json = a.archivo.lower().endswith('.json')
    if es_json:
        pj = pilas.actores.PersonajeSprite(a.archivo, y=0.9)
        salida = a.salida or a.archivo
    else:
        if not (a.columnas and a.filas):
            ap.error('con una imagen hace falta -c/--columnas y '
                     '-f/--filas')
        pj = pilas.actores.PersonajeSprite(
            a.archivo, columnas=a.columnas, filas=a.filas,
            ancho=1.4, alto=1.8, y=0.9, velocidad=8)
        base = a.salida or os.path.splitext(a.archivo)[0]
        salida = base + '.personaje.json'
    pj.aprender(pilas.habilidades.MoverseConElTeclado, velocidad=4)

    cam = pilas.escena_actual().camara
    cam.seguir_a(pj, modo='tercera', distancia=4.5, altura=2.5)

    sel = [0]                                   # índice del slot
    info = pilas.actores.Texto('', x=10, y=540, tamano=14)
    info.color = pilas.colores.amarillo
    lista = pilas.actores.Texto('', x=10, y=90, tamano=12)
    ayuda = pilas.actores.Texto(
        "WASD mover - TAB slot - Q/E fila - M espejo - "
        "N/B estado +/- - X/K ciclico/quedarse - U/I vel - "
        "ESPACIO preview - G guardar - ESC salir",
        x=10, y=10, tamano=12)
    ver_ayuda = [True]

    def refrescar():
        slots = _slots(pj)
        sel[0] %= len(slots)
        slot = slots[sel[0]]
        partes = ['>> slot: %s' % slot]
        if slot in DIRECCIONES:
            if slot in pj._espejar:
                partes.append('espejo de %r' % pj._espejar[slot])
            else:
                partes.append('fila %d' % pj._mapa.get(slot, 0))
        else:
            e = pj._estados[slot]
            partes.append('fila %d' % e['fila'])
            partes.append('ciclica:%s' % ('si' if e['ciclica']
                                          else 'no'))
            if e['quedarse']:
                partes.append('quedarse')
            partes.append('vel %s' % (e['velocidad']
                                      or pj.velocidad))
        partes.append('| estado: %s dir: %s vel %d'
                      % (pj.estado, pj.direccion, pj.velocidad))
        info.texto = '  '.join(partes)
        lista.texto = ' | '.join(
            ('[%s]' % s if s == slot else s) for s in slots)

    def al_pulsar(tecla):
        s = pilas.simbolos
        slots = _slots(pj)
        slot = slots[sel[0] % len(slots)]
        if tecla == s.ESCAPE:
            pilas.terminar()
        elif tecla == s.TAB:
            sel[0] += 1
        elif tecla == s.h:
            ver_ayuda[0] = not ver_ayuda[0]
            ayuda.transparencia = 0 if ver_ayuda[0] else 100
        elif tecla == s.g:
            pj.guardar(salida)
            print('guardado %s' % salida)
        elif tecla == s.ESPACIO:
            if slot in DIRECCIONES:
                if slot in pj._mapa or slot in pj._espejar:
                    pj.definir_direccion(slot)
            else:
                pj.reproducir_estado(slot)
        elif slot in DIRECCIONES:
            if tecla == s.q:
                pj._mapa[slot] = (pj._mapa.get(slot, 0) - 1) % pj.filas
                pj._espejar.pop(slot, None)
            elif tecla == s.e:
                pj._mapa[slot] = (pj._mapa.get(slot, 0) + 1) % pj.filas
                pj._espejar.pop(slot, None)
            elif tecla == s.m:
                # cicla: sin espejo -> espejar desde cada otra dir
                otras = [d for d in DIRECCIONES if d != slot]
                act = pj._espejar.get(slot)
                if act is None:
                    pj._espejar[slot] = otras[0]
                else:
                    i = otras.index(act) + 1
                    if i < len(otras):
                        pj._espejar[slot] = otras[i]
                    else:
                        del pj._espejar[slot]
                pj.definir_direccion(slot)
        else:
            est = pj._estados[slot]
            if tecla == s.q:
                est['fila'] = (est['fila'] - 1) % pj.filas
            elif tecla == s.e:
                est['fila'] = (est['fila'] + 1) % pj.filas
            elif tecla == s.x:
                est['ciclica'] = not est['ciclica']
            elif tecla == s.k:
                est['quedarse'] = not est['quedarse']
            elif tecla == s.b:
                del pj._estados[slot]
                if pj._estado and pj._estado['nombre'] == slot:
                    pj.reproducir_estado(None)
                sel[0] = 0
        if tecla == s.n:
            for nombre in NOMBRES_ESTADO:
                if nombre not in pj._estados:
                    pj.agregar_estado(nombre, fila=0)
                    sel[0] = _slots(pj).index(nombre)
                    break
        elif tecla == s.u:
            pj.velocidad = max(1, pj.velocidad - 1)
        elif tecla == s.i:
            pj.velocidad += 1

    def cuando_actualiza():
        refrescar()

    refrescar()
    pilas.escena.cuando_pulsa_tecla = al_pulsar
    pilas.escena.cuando_actualiza = cuando_actualiza
    pilas.ejecutar()
    return 0


if __name__ == '__main__':
    sys.exit(cli())
