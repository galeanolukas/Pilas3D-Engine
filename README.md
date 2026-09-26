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
```

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
| `pilas.escenas.Normal()`      | `pilas.escenas.Normal()`             |
| `escena.camara.x/y`           | `camara.x/y/z` + `camara.objetivo`   |
| `pilas.control.izquierda`…    | igual (flechas + WASD)               |
| `pilas.actores.Texto/Puntaje` | `pilas.actores.Texto()` / `Puntaje()` (overlay 2D) |
| `actor.colisiona_con(otro)`   | igual (esfera-esfera 3D con `radio_de_colision`) + `colisiona_en_plano_con` (solo XZ) |
| `pilas.tareas.siempre(s, f)`  | igual (`una_vez`, `siempre`, `condicional`)  |
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
| `pilas.ejecutar()`            | `pilas.ejecutar()`                   |

## Licencia

LGPLv3, igual que el proyecto original.
