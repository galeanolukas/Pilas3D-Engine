# -*- encoding: utf-8 -*-
"""Generador de juegos con IA: ``%ia make_game <descripción>``.

Patrón "scaffold + iteración": el LLM no genera un juego desde cero
(alucina), sino que rellena los ``{{placeholders}}`` de un template
válido. El resultado se valida con AST y con una ejecución headless
(``PILAS3D_HEADLESS``), con reintentos que le devuelven el error al
modelo para que lo corrija.
"""

import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unicodedata

from pilas3d.ia.asistente import llamar_ollama

TEMPLATE = (pathlib.Path(__file__).parent
            / 'templates' / 'juego_base.py')
JUEGOS_DIR = pathlib.Path(
    os.environ.get('PILAS3D_JUEGOS_DIR', './juegos'))

SYSTEM_MAKE = """\
Sos generador de juegos para Pilas3D-Engine (motor 3D educativo en
Python). Te doy un TEMPLATE con placeholders {{ASI}} y una
DESCRIPCIÓN. Devolvés el template COMPLETO con los placeholders
reemplazados por código válido.

REGLAS ESTRICTAS:
- Usá SOLO esta API: pilas.actores.Cubo/Esfera/Piso/Pared/Plano/Ejes/
  Texto/Puntaje/Cartel/Animacion/Mapa/Modelo/ModeloAnimado/Mundo/
  ModeloJSON/Sombra/Cielo
- Habilidades: MoverseConElTeclado, RebotarComoPelota,
  GirarConstantemente, CaminarEnPrimeraPersona, SeguirAlActor,
  MirarAlActor, MoverseEnCirculo, MoverseComoCoche, Imitar,
  AumentarConRueda, RotarConMouse, PuedeExplotar
- Tareas: pilas.tareas.siempre(segundos, fn), una_vez, condicional
- Interpolación: pilas.interpolar(actor, 'x', valor, duracion) o
  actor.x = [valor]
- Colisiones: actor.colisiona_con(otro), colisiona_en_plano_con(otro),
  distancia_con(otro), radio_de_colision
- Geometría: mallas.cubo(tamaño), mallas.esfera(radio)
- Propiedades de actor: x y z, rotacion_x/y/z, escala, color, imagen
- Colores: pilas.colores.rojo/verde/azul/amarillo/blanco/negro...
- Escena: pilas.escena_actual(), pilas.escenas.vincular(Clase),
  pilas.cambiar_escena(escena)
- NO uses input(), open(), ni nada fuera de la API
- Devolvés SOLO el código completo, sin markdown ni explicaciones
- No queden placeholders {{...}} sin reemplazar
"""

SYSTEM_EDIT = """\
Sos editor de juegos de Pilas3D-Engine. Recibís un código que YA
FUNCIONA y un CAMBIO pedido. Devolvés el código completo modificado,
sin markdown ni explicaciones. Mantenés la estructura y usás solo la
API real del motor (pilas.actores, pilas.habilidades, pilas.tareas,
pilas.control, pilas.interpolar, mallas). No rompés lo que ya andaba;
si el cambio es ambiguo elegí la interpretación más simple.
"""


def slugify(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_')[:40]


def extraer_codigo(respuesta):
    """Saca el código de una respuesta (soporta fences markdown)."""
    m = re.search(r'```(?:python)?\s*\n(.*?)```', respuesta, re.S)
    return m.group(1) if m else respuesta


def validar_codigo(codigo):
    """Chequeo estático rápido: parsea y no quedan placeholders."""
    if '{{' in codigo:
        return False, 'quedaron placeholders {{...}} sin reemplazar'
    try:
        arbol = ast.parse(codigo)
    except SyntaxError as e:
        return False, 'SyntaxError: %s' % e
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call) and
                isinstance(nodo.func, ast.Name) and
                nodo.func.id in ('input', 'open')):
            return False, 'usa %s() (prohibido en juegos)' % nodo.func.id
    return True, ''


def ejecutar_headless(codigo, timeout=15):
    """Corre el juego sin ventana para validar que no explota."""
    codigo_headless = codigo.replace(
        'pilas.ejecutar()', 'pilas._tick(1 / 60.0); ' * 3)
    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False,
            encoding='utf-8') as f:
        f.write("import os\nos.environ['PILAS3D_HEADLESS'] = '1'\n")
        f.write(codigo_headless)
        ruta = f.name
    try:
        r = subprocess.run([sys.executable, ruta], capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode == 0, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return False, '', 'Timeout %ds (¿loop infinito?)' % timeout
    finally:
        os.unlink(ruta)


def generar_juego(descripcion, max_intentos=3):
    """Genera, valida y guarda un juego en ``juegos/<slug>.py``.

    Devuelve ``(exito, ruta, mensaje)``. Guarda el archivo aunque la
    validación falle — mejor un juego imperfecto que nada.
    """
    JUEGOS_DIR.mkdir(exist_ok=True)
    slug = slugify(descripcion)
    destino = JUEGOS_DIR / ('%s.py' % slug)

    plantilla = TEMPLATE.read_text(encoding='utf-8')
    error = 'sin respuesta del modelo'
    codigo = None

    for intento in range(1, max_intentos + 1):
        if intento == 1:
            prompt = ('DESCRIPCIÓN:\n%s\n\nTEMPLATE:\n%s'
                      % (descripcion, plantilla))
        else:
            prompt = ('El código anterior falló. Corregilo.\n\n'
                      'CÓDIGO:\n%s\n\nERROR:\n%s\n\n'
                      'Devolvé SOLO el código corregido, sin markdown.'
                      % (codigo, error))

        respuesta = llamar_ollama(prompt, system=SYSTEM_MAKE)
        codigo = extraer_codigo(respuesta)

        ok, razon = validar_codigo(codigo)
        if not ok:
            error = razon
            print('  ⚠ Intento %d: %s' % (intento, razon))
            continue

        exito, stdout, stderr = ejecutar_headless(codigo)
        if exito:
            destino.write_text(codigo, encoding='utf-8')
            return True, destino, 'validado en %d intento(s)' % intento
        error = (stderr or stdout).strip() or 'error desconocido'
        print('  ⚠ Intento %d: %s' % (intento, error[:120]))

    if codigo:
        destino.write_text(codigo, encoding='utf-8')
    return False, destino, ('falló tras %d intentos: %s'
                            % (max_intentos, error[:200]))


def editar_juego(ruta, cambio, max_intentos=3):
    """Aplica un cambio a un juego existente. Devuelve (exito, msg)."""
    codigo_actual = pathlib.Path(ruta).read_text(encoding='utf-8')
    error = ''
    nuevo = codigo_actual

    for intento in range(1, max_intentos + 1):
        prompt = 'CÓDIGO ACTUAL:\n%s\n\nCAMBIO:\n%s' % (
            codigo_actual if intento == 1 else nuevo, cambio)
        if error:
            prompt += ('\n\nEl intento anterior falló con: %s\n'
                       'Corregilo.' % error[:300])
        nuevo = extraer_codigo(
            llamar_ollama(prompt, system=SYSTEM_EDIT))

        ok, razon = validar_codigo(nuevo)
        if not ok:
            error = razon
            continue
        exito, _, stderr = ejecutar_headless(nuevo)
        if exito:
            pathlib.Path(ruta).write_text(nuevo, encoding='utf-8')
            return True, 'cambio validado en %d intento(s)' % intento
        error = stderr.strip()

    pathlib.Path(ruta).write_text(nuevo, encoding='utf-8')
    return False, 'guardado sin validar: %s' % error[:120]
