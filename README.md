# Pilas3D-Engine

Motor de videojuegos 3D simple y en español, inspirado en
[pilas-engine](https://github.com/pilas-engine/pilas-engine) 1.x de Hugo
Ruscitti. Mantiene su filosofía y API didáctica, pero reemplaza el
render 2D (QPainter/PyQt4) por OpenGL 3D usando **pyglet**.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-apoyar-yellow?logo=buy-me-a-coffee)](https://buymeacoffee.com/lukasgaleano)

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
./instalar.sh          # Linux / macOS
instalar.bat           # Windows (doble click o desde cmd)
```

o a mano:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .   # opcional: habilita el comando pilas3d
```

Para **actualizar** a la última versión:

```bash
./actualizar.sh        # Linux / macOS
actualizar.bat         # Windows
```

Baja los cambios con `git pull --tags` y reinstala dependencias. La
versión actual está en el archivo `VERSION` y cada entrega queda
registrada con un tag de Git (`v0.2.0`, …).

### Asistente de IA (opcional)

Los instaladores descargan el binario de [Ollama](https://ollama.com)
(~200 MB) a `pilas3d/_vendor/` — si ya tenés Ollama instalado se usa
ese — y ofrecen elegir el modelo del asistente (default:
`qwen2.5-coder:0.5b`, ~500 MB, corre en CPU). Si lo salteás, el modelo
se baja solo la primera vez que consultás, y después todo corre
**local y offline**.

Para instalar/cambiar el modelo más tarde:

```bash
.venv/bin/python -m pilas3d.ia --lista                 # catálogo
.venv/bin/python -m pilas3d.ia qwen2.5-coder:7b        # baja otro
.venv/bin/python -m pilas3d.ia --instalados            # los que tenés
.venv/bin/python -m pilas3d.ia borrar qwen2.5-coder:0.5b  # libera espacio
PILAS3D_IA_MODELO=qwen2.5-coder:7b .venv/bin/pilas3d   # usarlo
```

```python
pilas.ayuda()                                   # chuleta clásica
pilas.ayuda("¿cómo hago un enemigo que me persiga?")
# en la consola interactiva:
In [1]: %ia ¿cómo pongo gravedad?
In [2]: %explicar        # explica el último error
```

Sin Ollama el motor funciona igual: `pilas.ayuda()` sigue mostrando la
guía. Variables de entorno: `PILAS3D_IA_MODELO` (modelo alternativo,
ej. `qwen2.5-coder:7b` con GPU) y `PILAS3D_IA_GPU=1` (usar GPU en vez
de CPU). Guía completa: [docs/asistente-ia.md](docs/asistente-ia.md).

## Ejemplos

```bash
.venv/bin/python ejemplos/hola_cubo.py
.venv/bin/python ejemplos/mover_con_teclado.py   # flechas o WASD
.venv/bin/python ejemplos/juego_recolectar.py   # mini-juego completo
.venv/bin/python ejemplos/camara_orbital.py     # órbita con mouse + debug
.venv/bin/python ejemplos/juego_doom.py         # mini-FPS: WASD + mouse + click
.venv/bin/python ejemplos/sonido.py             # efectos de audio
.venv/bin/python ejemplos/modelo_animado.py     # modelos .obj animados
.venv/bin/python ejemplos/escenas.py            # menu -> juego (escenas)
.venv/bin/python ejemplos/minecraft.py          # mini-Minecraft: picar/colocar bloques
.venv/bin/python ejemplos/juego_modelos.py      # recolectar gemas con modelos .obj
.venv/bin/python ejemplos/plataformas.py        # plataformero: PisaPlataformas + salto
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
In [4]: %ejemplo juego_recolectar          # corre un ejemplo acá mismo
In [5]: %ia ¿cómo pongo gravedad?          # asistente (opcional)
In [6]: %explicar                          # explica el último error
```

Con el asistente de IA también podés **generar juegos enteros**:

```
In [7]: %ia make_game un cubo que recolecta esferas
In [8]: %ia run juegos/un_cubo_que_recolecta_esferas.py
In [9]: %ia edit juegos/un_cubo_que_recolecta_esferas.py "agregá puntaje"
In [10]: %ia list                        # juegos guardados en ./juegos
```

`make_game` genera el juego desde un template validado (el modelo solo
rellena la lógica), lo prueba en modo headless y reintenta con el
error si falla. `run` lo ejecuta en la ventana abierta. Los juegos
quedan en `./juegos/` (en `.gitignore`).

`%ejemplo <nombre>` ejecuta un archivo de `ejemplos/` dentro de la
ventana ya abierta: el `iniciar()` del ejemplo devuelve la `pilas`
viva y su `ejecutar()` se omite — el auto-refresco la sigue animando
y podés seguir tocando los actores que creó. `%ejemplo` sin nombre
lista los disponibles.

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
| `actor.aprender(pilas.habilidades.X)` | igual — `MoverseConElTeclado`, `RebotarComoPelota` (3D), `GirarConstantemente`, `SeguirAlActor`, `MirarAlActor`, `MoverseEnCirculo`, `MoverseComoCoche`, `Imitar`, `AumentarConRueda`, `RotarConMouse`, `PuedeExplotar`, `PisaPlataformas`, `PerseguirAOtroActor` (A* esquivando obstáculos) |
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
| —                             | `pilas.actores.Mundo()` — voxels tipo Minecraft: `generar_terreno`, `poner/sacar_bloque`, `disparar_bloque` (rayo DDA) |
| —                             | `pilas.actores.ModeloJSON('x.json')` — modelos de bloque Minecraft (formato elements/faces) |
| —                             | `mundo.armar_atlas([pngs])` — atlas de bloques desde texturas propias |
| —                             | `pilas.luces` — sol + hasta 8 puntuales con atenuación |
| —                             | `pilas.actores.Sombra(actor)` (sombra falsa tipo blob) |
| —                             | `pilas.actores.Cielo()` — cielo estrellado (o `Cielo('fondo.png')`) |
| `pilas.ejecutar()`            | `pilas.ejecutar()`                   |

## Colaborar

¡Las contribuciones son bienvenidas! Algunas formas de sumar:

- **Issues y PRs**: reportá bugs, proponé habilidades o actores nuevos,
  mejorá ejemplos o documentación.
- **Ideas pendientes**: chunks para mundos voxel grandes, transiciones
  con fade entre escenas, lanzador gráfico, animación esquelética
  glTF, más habilidades de pilas (`Disparar`, `PisaPlataformas`…).
- **Ejemplos**: un nuevo juego o demo usando la API es una gran
  contribución — mirá `ejemplos/` para el estilo.

Antes de commitear corré los tests:

```bash
.venv/bin/python -m pytest tests/
```

### Apoyar el proyecto

Si el motor te resulta útil y querés darle una mano al desarrollo,
podés invitarme un café:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-lukasgaleano-yellow?logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/lukasgaleano)

**[buymeacoffee.com/lukasgaleano](https://buymeacoffee.com/lukasgaleano)**

## Licencia

LGPLv3, igual que el proyecto original.

El binario de Ollama (licencia MIT, © Ollama) **no** se distribuye con
este repositorio: los instaladores lo descargan aparte a
`pilas3d/_vendor/`, que está en `.gitignore`.
