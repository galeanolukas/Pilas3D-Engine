# -*- encoding: utf-8 -*-
"""RAG del proyecto: busca en docs/, ejemplos/ y docstrings del
motor los fragmentos relevantes para una consulta y los inyecta al
prompt del asistente — así responde citando la API real en vez de
alucinar métodos.

Retriever BM25 en Python puro: sin dependencias, sin embeddings,
sin red. El índice se arma perezoso en el primer uso (~50 archivos,
milisegundos) y vive en memoria.

Uso directo::

    >>> from pilas3d.ia import rag
    >>> rag.buscar('enemigo que persiga')
    [{'archivo': '.../perseguir_a_otro_actor.py', 'texto': '...',
      'score': 4.2}, ...]
    >>> rag.contexto('enemigo que persiga', max_chars=1200)
    '### perseguir_a_otro_actor.py\\n...'

``pilas.ayuda`` / ``pilas.ia.preguntar`` lo usan solos; se desactiva
con la variable de entorno ``PILAS3D_IA_RAG=0``.
"""

import glob
import math
import os
import re

_RAIZ = os.path.normpath(os.path.join(
    os.path.dirname(__file__), '..', '..'))

# stopwords mínimas (español + inglés técnico que no discrimina)
_STOP = frozenset(
    'el la los las un una unos unas de del en y o a al que por con '
    'para se es son su sus lo como mas más sin sobre este esta estos '
    'estas ser no si sí tu te me mi eso hay hacer hace the a an of to '
    'in is and or for it its'.split())

_TOKEN = re.compile(r"[a-záéíóúñü0-9_]+")

_indice = None          # {'docs': [...], 'idf': {term: idf}}


def _tokens(texto):
    return [t for t in _TOKEN.findall(texto.lower())
            if t not in _STOP and len(t) > 1]


def _archivos():
    """Fuentes del índice: docs + ejemplos + README si existen (repo)
    y siempre los .py del paquete (viajan con la instalación)."""
    rutas = []
    for patron in ('docs/*.md', 'ejemplos/*.py', 'README.md',
                   'pilas3d/**/*.py'):
        rutas += glob.glob(os.path.join(_RAIZ, patron),
                           recursive=True)
    return sorted(set(rutas))


def _fragmentos_de(ruta):
    """Corta un archivo en fragmentos con título.

    - .md: por encabezados (## ...)
    - .py: por bloques de nivel superior (def/class/import sueltos)
    """
    try:
        with open(ruta, encoding='utf-8', errors='replace') as f:
            texto = f.read()
    except OSError:
        return []
    base = os.path.relpath(ruta, _RAIZ)
    if ruta.endswith('.md'):
        partes = re.split(r'(?m)^(#{1,3} .+)$', texto)
        # [pre, h1, cuerpo, h2, cuerpo, ...]
        frags = [partes[0]] + [a + b for a, b in
                               zip(partes[1::2], partes[2::2])]
    else:
        # corte en líneas de nivel 0 que abren bloque
        partes = re.split(r'(?m)^(?=def |class |@|"""|# ---)',
                          texto)
        frags = partes
    return [(base, f.strip()) for f in frags if f and f.strip()]


def _construir():
    docs = []
    for ruta in _archivos():
        for archivo, frag in _fragmentos_de(ruta):
            tokens = _tokens(frag)
            if len(tokens) < 4:
                continue
            frec = {}
            for t in tokens:
                frec[t] = frec.get(t, 0) + 1
            docs.append({'archivo': archivo, 'texto': frag,
                         'frec': frec, 'largo': len(tokens)})
    n_docs = len(docs) or 1
    df = {}
    for d in docs:
        for t in d['frec']:
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(1 + (n_docs - n + 0.5) / (n + 0.5))
           for t, n in df.items()}
    return {'docs': docs, 'idf': idf}


def _indice_built():
    global _indice
    if _indice is None:
        _indice = _construir()
    return _indice


def reiniciar_indice():
    """Relee los archivos (tras editar docs/ejemplos)."""
    global _indice
    _indice = None


def buscar(consulta, k=4):
    """Los ``k`` fragmentos más relevantes para ``consulta``.

    Devuelve ``[{'archivo', 'texto', 'score'}]`` ordenados por
    relevancia BM25 (k1=1.5, b=0.75); lista vacía si nada supera
    el piso."""
    indice = _indice_built()
    terminos = _tokens(consulta)
    if not terminos:
        return []
    largos = [d['largo'] for d in indice['docs']]
    avg = (sum(largos) / len(largos)) or 1.0
    k1, b = 1.5, 0.75
    puntos = []
    for d in indice['docs']:
        score = 0.0
        for t in terminos:
            f = d['frec'].get(t)
            if not f:
                continue
            idf = indice['idf'].get(t, 0.0)
            score += idf * (f * (k1 + 1)) / (
                f + k1 * (1 - b + b * d['largo'] / avg))
        if score > 0:
            puntos.append((score, d))
    puntos.sort(key=lambda s: -s[0])
    return [{'archivo': d['archivo'], 'texto': d['texto'],
             'score': round(s, 3)} for s, d in puntos[:k]]


def contexto(consulta, k=4, max_chars=1500):
    """Fragmentos relevantes formateados para meter en el prompt
    (o '' si no hay nada útil / el índice está vacío)."""
    if os.environ.get('PILAS3D_IA_RAG', '1') == '0':
        return ''
    try:
        resultados = buscar(consulta, k=k)
    except Exception:
        return ''         # el RAG nunca rompe la consulta
    partes = []
    usados = 0
    for r in resultados:
        bloque = '### %s\n%s' % (r['archivo'], r['texto'])
        if usados + len(bloque) > max_chars:
            break
        partes.append(bloque)
        usados += len(bloque)
    return '\n\n'.join(partes)
