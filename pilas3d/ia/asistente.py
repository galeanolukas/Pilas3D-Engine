# -*- encoding: utf-8 -*-
"""Asistente de código: ``pilas.ayuda("¿cómo hago...?")``.

Usa un modelo local (Ollama) con un system prompt que describe la
API real de pilas3d, para que el código que genera sea ejecutable.
"""

import json
import os
import urllib.error
import urllib.request

from pilas3d.ia.servidor import (URL_API, MODELO, asegurar_servidor,
                                 asegurar_modelo)

SYSTEM = """\
Sos el asistente de Pilas3D-Engine, un motor 3D educativo en Python
para aprender a programar videojuegos (inspirado en pilas-engine).
Respondé en español, breve, y siempre con código ejecutable.

API disponible (no inventes métodos fuera de esta lista):
- pilas.actores: Cubo, Esfera(radio), Pared(ancho,alto,prof),
  Piso(), Plano, Ejes, Cartel, Texto, Puntaje, Animacion(png,columnas),
  Mapa(texto,mapa), Modelo('x.obj'), ModeloAnimado('f*.obj'),
  ModeloJSON('x.json'), Mundo() (voxels), Sombra(actor), Cielo()
- cada actor: x y z, rotacion_x/y/z, escala, color, imagen,
  radio_de_colision, eliminar(), actualizar(), aprender(),
  colisiona_con(otro), colisiona_en_plano_con(otro),
  distancia_con(otro), esta_en_escena()
- pilas.habilidades: MoverseConElTeclado, RebotarComoPelota,
  GirarConstantemente(eje), CaminarEnPrimeraPersona(mundo,gravedad,
  salto), SeguirAlActor(actor), MirarAlActor(actor),
  MoverseEnCirculo(centro,radio), MoverseComoCoche, Imitar(actor),
  AumentarConRueda, RotarConMouse, PuedeExplotar
- pilas.tareas: una_vez(s,f), siempre(s,f), condicional(s,f)
- pilas.interpolar(actor,'x',valor,duracion) / actor.x = [v1,v2]
- pilas.control: arriba abajo izquierda derecha (flechas+WASD),
  mouse_x mouse_y boton_izquierdo/derecho/medio
- pilas.luces: direccional(.color .direccion .ambiente),
  agregar(LuzPuntual(x,y,z,color,alcance)), quitar, limpiar
- escenas: class MiEscena(pilas3d.escenas.Escena) con iniciar(),
  terminar(), cuando_pulsa_tecla(s), cuando_actualiza();
  pilas.escenas.vincular(Clase); pilas.escenas.Clase() la activa
- camara: escena_actual().camara, usar_control_orbital(),
  disparar_rayo(actores, alcance)
- mundo voxel: generar_terreno(w,d,altura), poner_bloque(i,j,k,
  'pasto'), sacar_bloque, disparar_bloque(origen,direccion)
- audio: pilas.sonidos.cargar('x.wav').reproducir(),
  pilas.musica.cargar('x.ogg').reproducir()
- depurador: pilas.depurador.definir_modos(fps,ejes,
  radios_de_colision,puntos_de_control)
- pilas.paso() avanza un frame (modo interactivo); pilas.ejecutar()
  bloquea

Si algo no está en la lista, decilo en vez de inventarlo.\
"""


def modelo_actual():
    """El modelo a usar: PILAS3D_IA_MODELO > config guardada > default.

    La config se escribe al instalar o con ``pilas.ia.modelo = 'x'``.
    """
    from pilas3d import config
    return (os.environ.get('PILAS3D_IA_MODELO')
            or config.leer('ia_modelo')
            or MODELO)


def _opciones():
    """Opciones del modelo. Por defecto CPU (num_gpu=0) para que
    funcione en cualquier equipo; PILAS3D_IA_GPU=1 habilita la GPU.

    ``num_predict`` corta respuestas largas (un NPC no necesita 2000
    tokens) y ``num_ctx`` acota el contexto — los dos bajan mucho la
    latencia en CPU. Se ajustan con PILAS3D_IA_MAX_TOKENS /
    PILAS3D_IA_CTX."""
    opciones = {
        'num_predict': int(os.environ.get('PILAS3D_IA_MAX_TOKENS',
                                          '220')),
        'num_ctx': int(os.environ.get('PILAS3D_IA_CTX', '2048')),
    }
    if not os.environ.get('PILAS3D_IA_GPU'):
        opciones['num_gpu'] = 0
    return opciones


def llamar_ollama(prompt, system=SYSTEM, modelo=None, al_token=None):
    """Llama al modelo local y devuelve el texto de la respuesta.

    ``keep_alive`` mantiene el modelo cargado ~10 min: evita pagar la
    recarga en cada pregunta. Con ``al_token`` se usa streaming y la
    función se invoca con el texto parcial a medida que llega (sirve
    para mostrar la respuesta mientras se genera — la latencia
    percibida cae a casi cero)."""
    asegurar_servidor()
    modelo = asegurar_modelo(modelo or modelo_actual())
    cuerpo = {
        'model': modelo,
        'stream': al_token is not None,
        'keep_alive': '10m',
        'options': _opciones(),
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt},
        ],
    }
    req = urllib.request.Request(
        URL_API + '/api/chat',
        data=json.dumps(cuerpo).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            if al_token is None:
                return json.loads(r.read())['message']['content']
            partes = []
            for linea in r:
                if not linea.strip():
                    continue
                pedazo = json.loads(linea)['message'].get(
                    'content', '')
                if pedazo:
                    partes.append(pedazo)
                    al_token(''.join(partes))
            return ''.join(partes)
    except urllib.error.URLError as e:
        raise RuntimeError(
            "No pude hablar con el modelo local (%s)." % e)


def calentar(modelo=None):
    """Pre-carga el modelo en Ollama (vacío, solo para que quede en
    memoria) — la primera respuesta real sale mucho más rápida."""
    try:
        asegurar_servidor()
        modelo = asegurar_modelo(modelo or modelo_actual())
        req = urllib.request.Request(
            URL_API + '/api/generate',
            data=json.dumps({'model': modelo, 'keep_alive': '10m',
                             'prompt': '', 'stream': False}).encode(),
            headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=120).read()
    except Exception:
        pass      # sin Ollama o sin modelo: el calentamiento es opcional


def preguntar(consulta, contexto='', modelo=None, al_token=None):
    """Le pregunta al asistente; descarga Ollama/modelo si hace falta.

    >>> pilas.ayuda("¿cómo hago un enemigo que me persiga?")

    ``al_token`` se pasa a ``llamar_ollama`` para streaming."""
    prompt = ('Contexto actual:\n%s\n\n' % contexto
              if contexto else '') + 'Pregunta: ' + consulta
    try:
        return llamar_ollama(prompt, modelo=modelo, al_token=al_token)
    except RuntimeError as e:
        return "No pude hablar con el modelo local. Probá de nuevo. (%s)" % e


def explicar_error(texto_error, contexto=''):
    """Pide al asistente que explique un traceback en simple."""
    return preguntar(
        "Este error surgió usando el motor:\n%s\n"
        "Explicá qué hice mal y cómo arreglarlo." % texto_error,
        contexto=contexto)
