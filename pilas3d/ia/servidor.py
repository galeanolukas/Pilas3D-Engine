# -*- encoding: utf-8 -*-
"""Lanza Ollama como subproceso y descarga el modelo a demanda.

El binario se busca en este orden:

1. ``ollama`` en el PATH (instalación normal del usuario).
2. ``pilas3d/_vendor/ollama/`` (descargado por instalar.sh/.bat).
3. Descarga perezosa desde https://ollama.com/download si falta.

El servidor solo arranca cuando alguien usa el asistente, y se
termina solo al cerrar el proceso (atexit).
"""

import atexit
import json
import os
import pathlib
import platform
import shutil
import stat
import subprocess
import time
import urllib.error
import urllib.request

URL_API = "http://localhost:11434"
MODELO = os.environ.get('PILAS3D_IA_MODELO', 'qwen2.5-coder:0.5b')

# Catálogo sugerido: todos Qwen code, de más chico a más grande.
MODELOS = {
    'qwen2.5-coder:0.5b': '~500 MB - recomendado, rápido en CPU',
    'qwen2.5-coder:1.5b': '~1 GB - mejor código, sigue en CPU',
    'qwen2.5-coder:3b':   '~2 GB - con GPU o paciencia',
    'qwen2.5-coder:7b':   '~4.7 GB - con GPU, el mejor',
}

_proc = None


def _vendor_dir():
    return (pathlib.Path(__file__).parent.parent
            / '_vendor' / 'ollama')


def _url_binario():
    sistema = platform.system().lower()     # 'linux' / 'windows'
    maquina = platform.machine().lower()
    arch = 'arm64' if maquina in ('aarch64', 'arm64') else 'amd64'
    if sistema == 'windows':
        return ('https://ollama.com/download/ollama-windows-%s.zip'
                % arch, True)
    return ('https://ollama.com/download/ollama-%s-%s'
            % (sistema, arch), False)


def _buscar_binario():
    """Devuelve la ruta al ejecutable de ollama o None."""
    en_path = shutil.which('ollama')
    if en_path:
        return en_path
    exe = 'ollama.exe' if os.name == 'nt' else 'ollama'
    local = _vendor_dir() / exe
    return str(local) if local.exists() else None


def _descargar_binario():
    """Baja el binario a ``pilas3d/_vendor/ollama/`` (~200 MB)."""
    url, es_zip = _url_binario()
    destino = _vendor_dir()
    destino.mkdir(parents=True, exist_ok=True)
    exe = 'ollama.exe' if os.name == 'nt' else 'ollama'
    print("Descargando Ollama desde %s ..." % url)
    if es_zip:
        import io
        import zipfile
        datos = urllib.request.urlopen(url, timeout=300).read()
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            for nombre in z.namelist():
                if nombre.endswith('ollama.exe'):
                    (destino / exe).write_bytes(z.read(nombre))
                    break
    else:
        binario = destino / exe
        urllib.request.urlretrieve(url, binario)
        binario.chmod(binario.stat().st_mode | stat.S_IXUSR
                      | stat.S_IXGRP | stat.S_IXOTH)
    return str(destino / exe)


def _get(ruta, timeout=1.0):
    with urllib.request.urlopen(URL_API + ruta,
                                timeout=timeout) as r:
        return json.loads(r.read())


def disponible():
    """True si el servidor de Ollama ya está respondiendo."""
    try:
        _get('/api/tags')
        return True
    except Exception:
        return False


def asegurar_servidor():
    """Arranca ``ollama serve`` si no hay uno corriendo."""
    global _proc
    if disponible():
        return
    if _proc and _proc.poll() is None:
        return
    binario = _buscar_binario()
    if binario is None:
        try:
            binario = _descargar_binario()
        except Exception as e:
            raise RuntimeError(
                "no se pudo descargar Ollama (%s); instalalo desde "
                "https://ollama.com o corré ./instalar.sh" % e)
    _proc = subprocess.Popen([binario, 'serve'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    atexit.register(_proc.terminate)
    for _ in range(50):
        if disponible():
            return
        time.sleep(0.2)
    raise RuntimeError("Ollama no arrancó en 10 segundos")


def listar_modelos():
    """Modelos descargados en el servidor local."""
    try:
        tags = _get('/api/tags', timeout=5)
    except urllib.error.URLError:
        return []
    return [m.get('name', '') for m in tags.get('models', [])]


def borrar_modelo(modelo):
    """Elimina un modelo descargado (`ollama rm`)."""
    req = urllib.request.Request(
        URL_API + '/api/delete',
        data=json.dumps({'name': modelo}).encode(),
        headers={'Content-Type': 'application/json'},
        method='DELETE')
    try:
        urllib.request.urlopen(req, timeout=30)
        return True
    except urllib.error.URLError:
        return False


def asegurar_modelo(modelo=MODELO):
    """Descarga el modelo si falta (primera vez, ~1 GB)."""
    try:
        tags = _get('/api/tags', timeout=5)
    except urllib.error.URLError:
        return   # sin servidor todavía; asegurar_servidor() lo llama
    modelos = [m.get('name', '') for m in tags.get('models', [])]
    base = modelo.split(':')[0]
    if any(m == modelo or m.split(':')[0] == base for m in modelos):
        return
    print("Descargando el modelo '%s' (solo la primera vez)..."
          % modelo)
    req = urllib.request.Request(
        URL_API + '/api/pull',
        data=json.dumps({'name': modelo, 'stream': True}).encode(),
        headers={'Content-Type': 'application/json'})
    completado = ''
    with urllib.request.urlopen(req, timeout=None) as r:
        for linea in r:
            estado = json.loads(linea).get('status', '')
            if estado and estado != completado:
                print('  ', estado)
                completado = estado
