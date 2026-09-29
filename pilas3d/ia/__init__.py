# -*- encoding: utf-8 -*-
"""Asistente de IA local para pilas3d (Ollama embebido).

Todo es opcional y perezoso: el motor funciona igual sin IA. La
primera vez que se usa ``pilas.ayuda("...")`` se descarga el binario
de Ollama (si no está) y el modelo (~1 GB) a pedido del usuario.
"""

from pilas3d.ia.servidor import (asegurar_servidor, asegurar_modelo,
                                 listar_modelos, borrar_modelo,
                                 disponible, MODELO, MODELOS)
from pilas3d.ia.asistente import (preguntar, explicar_error,
                                  llamar_ollama, calentar,
                                  modelo_actual)
from pilas3d.ia import voz


class IA(object):
    """Punto de acceso del motor a la IA local: ``pilas.ia``.

        >>> pilas.ia.preguntar('¿cómo hago un enemigo que persiga?')
        >>> pilas.ia.modelo = 'smollm2:135m'   # queda guardado
        >>> pilas.ia.calentar()                # pre-carga en un hilo
        >>> pilas.ia.disponible()              # ¿hay servidor+modelo?
    """

    def __init__(self, pilas):
        self._pilas = pilas

    @property
    def modelo(self):
        """Modelo en uso (env > config > default)."""
        return modelo_actual()

    @modelo.setter
    def modelo(self, valor):
        """Cambia el modelo y lo recuerda en ``~/.pilas3d/config.json``."""
        from pilas3d import config
        config.guardar('ia_modelo', valor)

    def preguntar(self, consulta, contexto='', modelo=None,
                  al_token=None):
        from pilas3d.ia import asistente
        return asistente.preguntar(consulta, contexto=contexto,
                                   modelo=modelo, al_token=al_token)

    def explicar_error(self, texto_error, contexto=''):
        from pilas3d.ia import asistente
        return asistente.explicar_error(texto_error, contexto=contexto)

    def calentar(self, modelo=None):
        """Pre-carga el modelo en un hilo (no bloquea)."""
        import threading
        threading.Thread(target=calentar,
                         kwargs={'modelo': modelo}, daemon=True).start()

    def disponible(self):
        """True si Ollama responde y el modelo está instalado (sin
        descargar ni arrancar nada)."""
        try:
            return disponible()
        except Exception:
            return False

    def modelos(self):
        """Modelos instalados en el Ollama local."""
        try:
            return listar_modelos()
        except Exception:
            return []


__all__ = ['preguntar', 'explicar_error', 'llamar_ollama', 'calentar',
           'modelo_actual', 'asegurar_servidor', 'asegurar_modelo',
           'listar_modelos', 'borrar_modelo', 'disponible', 'MODELO',
           'MODELOS', 'voz', 'IA']
