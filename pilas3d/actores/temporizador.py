# -*- encoding: utf-8 -*-
"""Temporizador: cuenta regresiva o cronómetro, con texto opcional.

Equivalencia con pilas 1.x: ``pilas.actores.Temporizador`` es un
``Texto`` que descuenta segundos y ejecuta una función al llegar a
cero. Aquí se amplía con ciclos, avisos intermedios y modo invisible.

Ejemplo::

    t = pilas.actores.Temporizador(duracion=10,
                                   cuando_termina=lambda: print('¡fin!'))
    t.iniciar()

    # cronómetro ascendente e invisible:
    c = pilas.actores.Temporizador(visible=False)
    c.iniciar()
    print(c.tiempo)   # segundos transcurridos
"""

from pilas3d import colores
from pilas3d.actores.texto import Texto


class Temporizador(Texto):
    """Contador de tiempo configurable.

    :param duracion: segundos de la cuenta regresiva; ``0`` (default)
                     lo convierte en cronómetro ascendente.
    :param cuando_termina: función a invocar al llegar a cero.
    :param ciclico: reinicia automáticamente al terminar (spawneo
                    periódico, oleadas, etc).
    :param visible: si es ``False`` no se dibuja (reloj invisible).
    :param autoeliminar: se elimina solo al terminar (sin ciclos).
    :param ascendente: si es ``True`` el cronómetro cuenta hacia
                       arriba siempre; ignorado con duracion > 0.
    :param formato: función opcional ``fn(segundos) -> str`` para
                    personalizar el texto mostrado.
    """

    def __init__(self, pilas, x=10, y=10, tamano=18, duracion=0,
                 cuando_termina=None, ciclico=False, visible=True,
                 autoeliminar=False, ascendente=True, formato=None,
                 color=colores.negro):
        self.duracion = duracion
        self.tiempo = duracion
        self.cuando_termina = cuando_termina
        self.ciclico = ciclico
        self.visible = visible
        self.autoeliminar = autoeliminar
        self.ascendente = ascendente
        self.formato = formato
        self.activo = False
        self._avisos = []
        super(Temporizador, self).__init__(
            pilas, texto=self._formatear(), x=x, y=y, tamano=tamano
        )
        self.color = color

    def _formatear(self):
        """Texto a mostrar: formato propio o mm:ss / segundos."""
        if self.formato:
            return self.formato(self.tiempo)
        resto = int(self.tiempo + 0.999)
        if resto >= 60:
            return "%d:%02d" % (resto // 60, resto % 60)
        return str(resto)

    # -- configuración (API pilas) ---------------------------------

    def ajustar(self, tiempo=1, funcion=None):
        """Ajusta la cuenta regresiva y la función al terminar."""
        self.duracion = tiempo
        self.tiempo = tiempo
        if funcion is not None:
            self.cuando_termina = funcion
        self.texto = self._formatear()

    def avisar(self, en_segundo, funcion):
        """Ejecuta ``funcion`` cuando el tiempo restante cruce
        ``en_segundo`` (solo cuenta regresiva). Se reactiva en cada
        ciclo si el temporizador es cíclico."""
        self._avisos.append([en_segundo, funcion])

    # -- control ----------------------------------------------------

    def iniciar(self):
        """Pone en marcha el contador."""
        self.activo = True

    def detener(self):
        """Pausa el contador conservando el tiempo restante."""
        self.activo = False

    def reiniciar(self):
        """Vuelve a ``duracion`` (o a 0 si es cronómetro) y arranca."""
        self.tiempo = self.duracion
        for aviso in self._avisos:
            if len(aviso) > 2:
                aviso.pop()
        self.activo = True
        self.texto = self._formatear()

    # -- interno ----------------------------------------------------

    def actualizar(self):
        if not self.activo:
            return
        dt = self.pilas.dt

        if self.duracion > 0:
            self.tiempo = max(0.0, self.tiempo - dt)
            self._procesar_avisos()
            if self.tiempo <= 0:
                self._terminar()
        elif self.ascendente:
            self.tiempo += dt

        self.texto = self._formatear()

    def _procesar_avisos(self):
        for aviso in self._avisos:
            if len(aviso) == 2 and self.tiempo <= aviso[0]:
                aviso.append(True)   # marcado como ya avisado
                aviso[1]()

    def _terminar(self):
        if self.cuando_termina:
            self.cuando_termina()
        if self.ciclico:
            self.tiempo = self.duracion
            for aviso in self._avisos:
                if len(aviso) > 2:
                    aviso.pop()
        else:
            self.activo = False
            if self.autoeliminar:
                self.eliminar()

    def dibujar(self):
        if self.visible:
            super(Temporizador, self).dibujar()
