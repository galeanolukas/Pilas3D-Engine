# Pilas3D-Engine

Motor de videojuegos 3D simple y en español, inspirado en
[pilas-engine](https://github.com/pilas-engine/pilas-engine) 1.x de Hugo
Ruscitti. Mantiene su filosofía y API didáctica, pero reemplaza el
render 2D (QPainter/PyQt4) por OpenGL 3D usando **pyglet**.

```python
import pilas3d
from pilas3d.actores.actor import Actor
from pilas3d import mallas

pilas = pilas3d.iniciar()

class CuboGiratorio(Actor):
    def _generar_geometria(self):
        return mallas.cubo(2.0)

    def actualizar(self):
        self.rotacion_y += 60 * self.pilas.dt

CuboGiratorio(pilas, y=1)
pilas.actores.Piso()
pilas.actores.Ejes()
pilas.ejecutar()
```

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Ejemplos

```bash
.venv/bin/python ejemplos/hola_cubo.py
.venv/bin/python ejemplos/mover_con_teclado.py   # flechas o WASD
.venv/bin/python ejemplos/juego_recolectar.py   # mini-juego completo
.venv/bin/python ejemplos/camara_orbital.py     # órbita con mouse + debug
.venv/bin/python ejemplos/juego_doom.py         # mini-FPS: WASD + mouse + click
.venv/bin/python ejemplos/sonido.py             # efectos de audio
```

## Consola interactiva (con autocompletado)

Tras `pip install -e .` queda disponible el comando `pilas3d`, que abre
la ventana junto con una consola IPython (autocompletado, historial,
colores) donde `pilas` ya está iniciada. **Cada línea que ejecutás
refresca la escena automáticamente** con `pilas.paso()`:

```bash
pilas3d                       # o: python3 -m pilas3d
```

```
In [1]: cubo = pilas.actores.Cubo()        # aparece al instante
In [2]: cubo.color = pilas.colores.rojo    # se vuelve rojo
In [3]: pilas.ayuda()                      # guía de la API
```

Sin IPython instalado cae a la consola estándar de Python con
autocompletado por tabulador (ahí hay que llamar `pilas.paso()` a mano).

## Modo interactivo manual

También se puede usar `paso()` desde cualquier REPL o script sin
bloquear con `ejecutar()`:

```python
>>> import pilas3d
>>> pilas = pilas3d.iniciar()
>>> cubo = pilas.actores.Cubo()      # la ventana ya muestra la escena
>>> cubo.color = pilas.colores.rojo
>>> pilas.paso()                     # redibuja con el cambio
>>> for i in range(180):             # anima ~3 segundos
...     cubo.rotacion_y += 2
...     pilas.paso()
>>> pilas.ayuda()                    # guía rápida de toda la API
```

`pilas.ayuda()` imprime una chuleta con toda la API disponible.

## Tests

```bash
.venv/bin/python -m pytest tests/
```

## Mapa con pilas-engine 1.4.9

| pilas (2D)                    | pilas3d                              |
|-------------------------------|--------------------------------------|
| `pilasengine.iniciar()`       | `pilas3d.iniciar()`                  |
| `pilas.actores.Aceituna()`    | `pilas.actores.Cubo()` / `Esfera()`… |
| `actor.x`, `actor.y`          | `actor.x`, `actor.y`, `actor.z` real |
| `actor.rotacion`              | `rotacion_x/y/z` (`rotacion` = eje Y)|
| `pilas.escenas.Normal()`      | igual + `escenas.vincular(Clase)`, hooks `iniciar`/`terminar`/`cuando_pulsa_tecla`, `pilas.escena`, `pilas.cambiar_escena` |
| `escena.camara.x/y`           | `camara.x/y/z` + `camara.objetivo`   |
| `pilas.control.izquierda`…    | igual (flechas + WASD)               |
| `pilas.actores.Texto/Puntaje` | `pilas.actores.Texto()` / `Puntaje()` (overlay 2D) |
| `actor.colisiona_con(otro)`   | igual (esfera-esfera 3D con `radio_de_colision`) + `colisiona_en_plano_con` (solo XZ) |
| `pilas.tareas.siempre(s, f)`  | igual (`una_vez`, `siempre`, `condicional`)  |
| `actor.x = [100]`             | igual — interpolación; `actor.x = ([a,b], dur)` u `Objeto` (`pilas.interpolaciones.Lineal`, `ReboteFinal`, `ElasticoInicial`…) + `pilas.interpolar(actor, 'x', v, duracion)` |
| `actor.aprender(pilas.habilidades.X)` | igual — `MoverseConElTeclado`, `RebotarComoPelota` (3D), `GirarConstantemente` |
| `pilas.depurador.definir_modos` | `fps`, `ejes`, `radios_de_colision`, `puntos_de_control` |
| `pilas.fps.ver()`             | igual                                |
| —                             | `camara.usar_control_orbital()` (mouse: orbitar + zoom) |
| —                             | `habilidades.CaminarEnPrimeraPersona` (FPS: mouse look + WASD) |
| —                             | `camara.disparar_rayo(actores)` (rayo-esfera, para disparos) |
| —                             | `pilas.actores.Pared()` + `escena.obstaculos` (bloquean el paso) |
| `pilas.control.mouse_x/y`     | posición y botones del mouse         |
| `pilas.sonidos.cargar()`      | igual (`reproducir`, `detener`, `pausar`, `continuar`, `volumen`) |
| `pilas.musica.cargar()`       | igual (streaming, bucle por defecto, `detener_gradualmente`) |
| `Grilla`/`Animacion`          | `pilas.actores.Animacion(img, columnas, filas, velocidad)` (billboard animado) |
| —                             | `pilas.actores.Cartel()` (sprite que siempre mira a la cámara) |
| —                             | `pilas.actores.Modelo('x.obj')` (carga modelos Wavefront .obj) |
| —                             | `pilas.actores.ModeloAnimado('run/f*.obj')` (secuencia .obj estilo MD2, `suavizar=True` interpola vértices) |
| —                             | `pilas.luces` — sol + hasta 8 puntuales con atenuación |
| —                             | `pilas.actores.Sombra(actor)` (sombra falsa tipo blob) |
| —                             | `pilas.actores.Cielo()` — cielo estrellado (o `Cielo('fondo.png')`) |
| `pilas.ejecutar()`            | `pilas.ejecutar()`                   |

## Licencia

LGPLv3, igual que el proyecto original.
