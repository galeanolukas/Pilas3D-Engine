# -*- encoding: utf-8 -*-
"""Voz para los actores: síntesis de texto a audio con Piper (local).

Igual que el asistente baja Ollama a pedido, la primera llamada a
``sintetizar`` descarga el binario de Piper (~26 MB) y la voz
(~60 MB) dentro de ``pilas3d/_vendor/piper/``::

    from pilas3d.ia import voz
    ruta = voz.sintetizar("hola chicos")      # → archivo .wav
    pilas.sonidos.cargar(ruta).reproducir()

La voz se elige con la variable de entorno ``PILAS3D_VOZ``
(formato ``<locale>-<nombre>-<calidad>``, ej. ``es_ES-davefx-medium``;
el catálogo está en https://huggingface.co/rhasspy/piper-voices).
"""

import os
import pathlib
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request

URL_PIPER = ('https://github.com/rhasspy/piper/releases/download/'
             '2023.11.14-2/')
URL_VOZ = ('https://huggingface.co/rhasspy/piper-voices/resolve/'
           'v1.0.0/')

#: Voz por defecto (español de España, masculina, ~60 MB).
VOZ = os.environ.get('PILAS3D_VOZ', 'es_ES-davefx-medium')


def _dir_piper():
    return (pathlib.Path(__file__).parent.parent
            / '_vendor' / 'piper')


def _url_binario():
    sistema = platform.system().lower()
    maquina = platform.machine().lower()
    if sistema == 'windows':
        return URL_PIPER + 'piper_windows_amd64.zip', 'zip'
    if sistema == 'darwin':
        arch = 'aarch64' if maquina in ('arm64', 'aarch64') else 'x64'
        return URL_PIPER + 'piper_macos_%s.tar.gz' % arch, 'tar'
    if maquina in ('aarch64', 'arm64'):
        nombre = 'piper_linux_aarch64.tar.gz'
    elif maquina.startswith('arm'):
        nombre = 'piper_linux_armv7l.tar.gz'
    else:
        nombre = 'piper_linux_x86_64.tar.gz'
    return URL_PIPER + nombre, 'tar'


def _buscar_binario():
    """``piper`` del PATH o el vendor descargado; None si falta."""
    en_path = shutil.which('piper')
    if en_path:
        return en_path
    exe = 'piper.exe' if os.name == 'nt' else 'piper'
    for ruta in (_dir_piper() / exe,
                 _dir_piper() / 'piper' / exe):
        if ruta.exists():
            return str(ruta)
    return None


def _descargar_binario():
    """Baja y descomprime Piper en ``_vendor/piper/``."""
    url, formato = _url_binario()
    destino = _dir_piper()
    destino.mkdir(parents=True, exist_ok=True)
    print("Descargando Piper desde %s ..." % url)
    if formato == 'zip':
        import io
        import zipfile
        datos = urllib.request.urlopen(url, timeout=300).read()
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            z.extractall(destino)
    else:
        import io
        datos = urllib.request.urlopen(url, timeout=300).read()
        with tarfile.open(fileobj=io.BytesIO(datos),
                          mode='r:gz') as t:
            t.extractall(destino)
    binario = _buscar_binario()
    if binario and os.name != 'nt':
        p = pathlib.Path(binario)
        p.chmod(p.stat().st_mode | stat.S_IXUSR
                | stat.S_IXGRP | stat.S_IXOTH)
    return binario


def asegurar_piper():
    """Devuelve la ruta al binario, descargándolo si hace falta."""
    binario = _buscar_binario()
    if binario is None:
        binario = _descargar_binario()
    if binario is None:
        raise RuntimeError("no se pudo conseguir el binario de Piper")
    return binario


def _url_voz(voz):
    """'es_ES-davefx-medium' → urls del .onnx y su .json."""
    locale, resto = voz.split('-', 1)
    nombre, calidad = resto.rsplit('-', 1)
    lang = locale.split('_')[0]
    base = '%s%s/%s/%s/%s/%s' % (URL_VOZ, lang, locale,
                               nombre, calidad, voz)
    return base + '.onnx', base + '.onnx.json'


def asegurar_voz(voz=None):
    """Devuelve la ruta del .onnx de la voz, bajándola si falta."""
    voz = voz or VOZ
    onnx = _dir_piper() / 'voces' / (voz + '.onnx')
    if onnx.exists():
        return str(onnx)
    url_onnx, url_json = _url_voz(voz)
    onnx.parent.mkdir(parents=True, exist_ok=True)
    print("Descargando voz %s ..." % voz)
    urllib.request.urlretrieve(url_onnx, onnx)
    urllib.request.urlretrieve(url_json, str(onnx) + '.json')
    return str(onnx)


def disponible():
    """True si ya hay un binario de Piper (PATH o vendor)."""
    return _buscar_binario() is not None


def _comando(binario, onnx, salida):
    """La línea de Piper: texto por stdin, wav a ``salida``."""
    return [binario, '--model', onnx, '--output_file', salida,
            '--espeak-data', os.path.dirname(binario)
            + os.sep + 'espeak-ng-data']


def sintetizar(texto, salida=None, voz=None):
    """Convierte ``texto`` a un archivo .wav y devuelve su ruta.

    La primera vez descarga Piper y la voz (puede tardar un rato).
    """
    binario = asegurar_piper()
    onnx = asegurar_voz(voz)
    if salida is None:
        fd, salida = tempfile.mkstemp(prefix='pilas3d_voz_',
                                      suffix='.wav')
        os.close(fd)
    subprocess.run(_comando(binario, onnx, salida),
                   input=texto.encode('utf-8'),
                   cwd=os.path.dirname(binario),
                   check=True)
    return salida
