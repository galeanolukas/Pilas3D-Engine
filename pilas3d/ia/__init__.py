# -*- encoding: utf-8 -*-
"""Asistente de IA local para pilas3d (Ollama embebido).

Todo es opcional y perezoso: el motor funciona igual sin IA. La
primera vez que se usa ``pilas.ayuda("...")`` se descarga el binario
de Ollama (si no está) y el modelo (~1 GB) a pedido del usuario.
"""

from pilas3d.ia.servidor import (asegurar_servidor, asegurar_modelo,
                                 listar_modelos, borrar_modelo,
                                 disponible, MODELO, MODELOS)
from pilas3d.ia.asistente import preguntar, explicar_error

__all__ = ['preguntar', 'explicar_error', 'asegurar_servidor',
           'asegurar_modelo', 'listar_modelos', 'borrar_modelo',
           'disponible', 'MODELO', 'MODELOS']
