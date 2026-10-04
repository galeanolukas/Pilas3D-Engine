# -*- encoding: utf-8 -*-
"""Menú de opciones con pilas.actores.Menu (overlay 2D) y flujo real.

Demuestra el ciclo completo de un juego: pantalla de título con cámara
cinematográfica orbitando -> Jugar -> robot controlable -> ESC abre el
menú de pausa (el robot queda quieto) -> ESC reanuda donde quedó.

- flechas/WS + ENTER para navegar, o click con el mouse
- opciones: acción / check [x] / cíclica / input de texto
- ``guardar_en`` persiste los valores en un JSON y los restaura
- al cambiar la resolución el menú se re-centra solo

    python3 ejemplos/menu.py
"""

import math
import os

import pilas3d

pilas = pilas3d.iniciar(ancho=640, alto=480, titulo="pilas3d - menu")

pilas.actores.Piso(tamano=40)
pilas.actores.Cielo('dia')
pilas.luces.direccional.ambiente = 0.5

# decoración de la pantalla de título
cubo = pilas.actores.Cubo(y=1)
cubo.color = pilas.colores.verde
cubo.aprender(pilas.habilidades.GirarConstantemente, velocidad=40)
lampara = pilas.actores.Lampara(x=3, y=2.5, z=2, alcance=9)
lampara.color = pilas.colores.naranja

estado = {'jugando': False, 'menu': None, 'robot': None}
# fuentes: archivos .ttf de pilas3d/data/fonts/ (pilas.fuentes.lista()
# muestra todas); también vale un nombre de familia instalada
hud = pilas.actores.Texto('', x=10, y=10, tamano=15,
                          fuente='DejaVuSansMono.ttf')
saludo = pilas.actores.Texto('', x=10, y=32, tamano=18)
saludo.color = pilas.colores.celeste

# -- cámara: orbita lenta de título / tercera persona al jugar -----------

camara = pilas.escena.camara
camara.posicion = (11, 6, 11)
camara.objetivo = (0, 1, 0)
angulo = [0.0]


def orbitar():
    """Orbita cinematográfica; al jugar la cámara sigue al robot."""
    if estado['jugando']:
        return
    angulo[0] += pilas.dt * 0.2
    foco = estado['robot'].posicion if estado['robot'] is not None \
        else (0, 1, 0)
    cx, cy, cz = foco[0], foco[1] + 1.0, foco[2]
    camara.posicion = (cx + math.cos(angulo[0]) * 11, cy + 5,
                       cz + math.sin(angulo[0]) * 11)
    camara.objetivo = (cx, cy, cz)


pilas.tareas.siempre(0, orbitar)

# -- jugar <-> pausa -----------------------------------------------------


def jugar():
    """Deja el menú y le da el teclado al robot (o lo reanuda)."""
    if estado['jugando']:
        return
    estado['jugando'] = True
    if estado['menu'] is not None:
        estado['menu'].eliminar()
        estado['menu'] = None
    if estado['robot'] is None:
        estado['robot'] = pilas.actores.Robot(z=3)
    estado['robot'].aprender(
        pilas.habilidades.MoverseConElTeclado, velocidad=5)
    camara.seguir_a(estado['robot'], 'tercera', distancia=7,
                    altura=4)
    hud.texto = 'flechas: mover - ESC: menú'


def pausar():
    """Congela al robot (sin perder su posición) y abre el menú."""
    if not estado['jugando']:
        return
    estado['jugando'] = False
    estado['robot'].eliminar_habilidad(
        pilas.habilidades.MoverseConElTeclado)
    camara.dejar_de_seguir()
    crear_menu()
    hud.texto = ''


def _atajos(simbolo, _mod):
    """ESC togglea juego <-> menú en vez de cerrar la ventana."""
    if simbolo == pilas.simbolos.ESCAPE:
        if estado['jugando']:
            pausar()
        else:
            jugar()
        return True


# -- opciones ------------------------------------------------------------

RESOLUCIONES = [(640, 480), (800, 600), (1024, 768)]
res_idx = [0]

CALIDADES = ['baja', 'media', 'alta']
cal_idx = [2]

VOLUMENES = [0.0, 0.25, 0.5, 0.75, 1.0]
vol_idx = [4]


def ciclar_resolucion():
    res_idx[0] = (res_idx[0] + 1) % len(RESOLUCIONES)
    ancho, alto = RESOLUCIONES[res_idx[0]]
    if pilas.ventana is not None:
        pilas.ventana.set_size(ancho, alto)
        if estado['menu'] is not None:
            estado['menu'].centrar()     # re-centra tras el resize
    return "Resolución: %dx%d" % (ancho, alto)


def ciclar_calidad():
    cal_idx[0] = (cal_idx[0] + 1) % len(CALIDADES)
    calidad = CALIDADES[cal_idx[0]]
    if calidad == 'baja':
        pilas.escena.niebla = ((0.5, 0.55, 0.6), 8, 30)
    elif calidad == 'media':
        pilas.escena.niebla = ((0.5, 0.55, 0.6), 20, 60)
    else:
        pilas.escena.niebla = None
    return "Calidad: %s" % calidad


def al_pantalla_completa(activo):
    if pilas.ventana is not None:
        pilas.ventana.set_fullscreen(activo)
        if estado['menu'] is not None:
            estado['menu'].centrar()


def al_sonar(activo):
    pilas.sonidos.mute = not activo          # mute/sonido global


def ciclar_volumen():
    vol_idx[0] = (vol_idx[0] + 1) % len(VOLUMENES)
    v = VOLUMENES[vol_idx[0]]
    pilas.sonidos.volumen = v                # volumen maestro
    pilas.sonidos.cargar('tick.wav').reproducir()   # preview
    return "Volumen: %d%%" % int(v * 100)


def al_nombrar(nombre):
    saludo.texto = "Hola, %s!" % nombre


# el menú persiste la config en un JSON al lado de este archivo
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'config-menu.json')


def crear_menu():
    estado['menu'] = pilas.actores.Menu(
        titulo="PAUSA" if estado['robot'] is not None else "PILAS3D",
        guardar_en=CONFIG,
        opciones=[
            ("Jugar", jugar),
            ("Resolución: 640x480", ciclar_resolucion),
            ("Pantalla completa", 'check', False,
             al_pantalla_completa),
            ("Calidad: alta", ciclar_calidad),
            ("Sonido", 'check', True, al_sonar),
            ("Volumen: 100%", ciclar_volumen),
            ("Nombre", 'input', 'jugador', al_nombrar),
            ("Salir", pilas.terminar),
        ],
        tamano=20,
        fuente='Blox2.ttf',            # fuente pixel del paquete
        centrado=True,
        fondo=(0, 0, 0, 150),          # panel oscuro semitransparente
        sonido_mover=True,             # 'tick.wav' al navegar
        sonido_elegir=True,            # 'smile.wav' al activar
        color=pilas.colores.blanco,
        seleccionado=pilas.colores.amarillo)


crear_menu()

if pilas.ventana is not None:
    pilas.ventana.push_handlers(on_key_press=_atajos)

pilas.ejecutar()
