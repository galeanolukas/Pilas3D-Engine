# -*- encoding: utf-8 -*-
"""Editor de personajes articulados — wrapper del motor.

El editor vive en ``pilas3d/editor.py``; este archivo queda como
acceso directo desde ``ejemplos/``:

    pilas3d-editor                     # comando (pip install -e .)
    python3 ejemplos/editor_personaje.py
    >>> pilas3d.editor.main()          # desde la consola interactiva

Controles: flechas eligen/rotan huesos, X/Y/Z el eje, M captura
keyframes, P reproduce, J guarda la animación junto al .glb,
T animación procedural, A explorador de archivos externo.
Ver ``docs/editor-personaje.md``.
"""

import pilas3d.editor

pilas3d.editor.main()
