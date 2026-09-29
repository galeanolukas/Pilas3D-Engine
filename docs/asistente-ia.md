# Guía: asistente de IA local en pilas3d

Cómo funciona la integración con [Ollama](https://ollama.com): un
modelo de lenguaje que corre **100% en tu máquina**, sin cuentas, sin
API keys y sin enviar nada a internet después de la descarga inicial.

---

## 1. Vista general

```
pilas.ayuda("¿cómo hago un enemigo que persiga?")
        │
        ▼
pilas3d/ia/servidor.py      ¿hay un servidor Ollama corriendo?
        │                   ├─ sí → usarlo
        │                   └─ no → buscar binario → lanzar
        │                         `ollama serve` (subproceso)
        ▼
pilas3d/ia/servidor.py      ¿está descargado el modelo?
        │                   └─ no → `ollama pull` (~500 MB, una vez)
        ▼
pilas3d/ia/asistente.py     POST /api/chat con:
                            · system prompt (la API real del motor)
                            · contexto de la escena actual
                            · tu consulta
        ▼
              respuesta impresa en consola
```

**Todo es perezoso**: si nunca usás `pilas.ayuda("...")`, `%ia` ni
`%explicar`, nada se descarga ni se ejecuta. El motor funciona igual
sin IA.

---

## 2. Dónde vive cada pieza

| Archivo | Rol |
|---|---|
| `pilas3d/ia/servidor.py` | Encuentra/descarga el binario, lanza `ollama serve`, baja el modelo |
| `pilas3d/ia/asistente.py` | System prompt + `preguntar()` + `explicar_error()` |
| `pilas3d/ia/__init__.py` | Exporta la API pública del módulo |
| `pilas3d/__init__.py` | `Pilas.ayuda(consulta)` + `_contexto()` |
| `pilas3d/interactivo.py` | Magics `%ia` y `%explicar` de IPython |
| `instalar.sh` / `instalar.bat` | Descargan el binario de Ollama (opcional, no fatal) |
| `pilas3d/_vendor/ollama/` | Binario descargado (en `.gitignore`, ~200 MB) |

---

## 3. El binario de Ollama

`_buscar_binario()` lo busca en este orden:

1. `ollama` en el **PATH** (si lo instalaste normal, se usa ese).
2. `pilas3d/_vendor/ollama/ollama` (o `ollama.exe`) — el que bajan
   los instaladores.
3. Si no hay ninguno, `asegurar_servidor()` lo descarga al vuelo:

| SO | URL |
|---|---|
| Linux/macOS | `ollama.com/download/ollama-<os>-<amd64\|arm64>` (binario suelto) |
| Windows | `ollama.com/download/ollama-windows-amd64.zip` (se descomprime) |

El servidor corre en `http://localhost:11434` como subproceso hijo y
se termina solo al salir (`atexit`). Si ya hay un Ollama corriendo
(instalado por vos), se reutiliza y no se lanza otro.

---

## 4. El modelo

Por defecto: **`qwen2.5-coder:0.5b`** (~500 MB) — el Qwen
especializado en código más chico, corre en CPU, suficiente para una
API acotada como la de pilas3d.

`asegurar_modelo()` consulta `GET /api/tags`; si el modelo no está,
hace `POST /api/pull` mostrando el progreso en consola. La descarga
solo ocurre la primera vez; después queda en `~/.ollama/models`.

Elegir otro modelo, **en el instalador o después**:

```bash
python -m pilas3d.ia --lista                # catálogo sugerido
python -m pilas3d.ia qwen2.5-coder:7b       # descarga otro modelo
python -m pilas3d.ia --instalados           # qué tenés bajado
python -m pilas3d.ia borrar <modelo>        # libera espacio en disco
PILAS3D_IA_MODELO=qwen2.5-coder:7b          # usarlo (env)
```

Para **cambiar de modelo** basta descargar el nuevo y borrar el viejo
si querés el espacio — los modelos viven en `~/.ollama/models`, son
independientes del motor.

| Modelo | Peso | Nota |
|---|---|---|
| `qwen2.5-coder:0.5b` | ~500 MB | default, rápido en CPU |
| `qwen2.5-coder:1.5b` | ~1 GB | mejor código, sigue en CPU |
| `qwen2.5-coder:3b` | ~2 GB | GPU o paciencia |
| `qwen2.5-coder:7b` | ~4.7 GB | el mejor, con GPU |

Los instaladores muestran el mismo menú al final de la instalación
(si se corren en una terminal interactiva).

---

## 5. Por qué responde bien: el system prompt

Un modelo de 1.5B no conoce pilas3d. La clave es que
`asistente.SYSTEM` le describe **la API real completa**: actores,
habilidades, tareas, control, luces, escenas, mundo voxel, audio y
depurador — con la instrucción explícita "no inventes métodos fuera de
esta lista".

Además, cada consulta lleva **contexto vivo de tu escena**
(`Pilas._contexto()`):

```
escena=Normal, actores=3 (Cubo, Esfera, Mundo), camara=(0.0, 5.0, 12.0)
```

Así, si preguntás "¿por qué mi cubo no se mueve?", el modelo sabe que
existe un `Cubo` en la escena.

---

## 6. Cómo usarlo

### Desde cualquier script / consola

```python
pilas.ayuda()                                     # chuleta clásica
pilas.ayuda("¿cómo hago que la luna orbite?")     # pregunta a la IA
```

### En la consola interactiva (`pilas3d`)

```python
In [1]: %ia ¿cómo le pongo gravedad al jugador?
In [2]: cubo.no_existe()
# AttributeError ...
In [3]: %explicar            # la IA explica el último error
```

`%explicar` guarda la última excepción vía el evento `post_run_cell`
de IPython y se la manda al modelo junto con el contexto de la escena.

### Subcomandos de `%ia`: generar juegos

```
%ia make_game <descripción>     # crea juegos/<slug>.py
%ia run <archivo.py>            # lo corre en la ventana abierta
%ia edit <archivo.py> <cambio>  # le pide un cambio al modelo
%ia list                        # lista juegos guardados
```

El generador (`pilas3d/ia/make_game.py`) usa el patrón
**template-first**: el modelo no escribe el juego desde cero sino que
rellena los `{{placeholders}}` de `ia/templates/juego_base.py`, que ya
es válido. Después el código se valida dos veces — parseo AST (sin
placeholders sueltos, sin `input()`/`open()`) y ejecución **headless**
en un subproceso con `PILAS3D_HEADLESS=1` — y si falla, el error se le
devuelve al modelo para reintentar (hasta 3 veces). Aunque no valide,
el archivo se guarda igual para edición manual.

`run` ejecuta el archivo en la `pilas` ya viva (parchea `iniciar()` y
`ejecutar()` como `%ejemplo`): el juego aparece en la ventana abierta
y sus actores quedan accesibles en la consola.

---

## 7. Voz con Piper + `ActorIA`

`pilas3d.ia.voz` sintetiza texto a audio con **Piper** (TTS local,
sin internet después de la descarga). Igual que Ollama, el binario
(~26 MB) y la voz (~60 MB) se bajan a `pilas3d/_vendor/piper/` la
primera vez::

    from pilas3d.ia import voz
    ruta = voz.sintetizar("hola chicos")   # -> .wav
    pilas.sonidos.cargar(ruta).reproducir()

`pilas.actores.ActorIA` junta todo en un NPC conversable::

    npc = pilas.actores.ActorIA('robot', nombre='Robi')
    npc.preguntar('hola, ¿en qué juego estamos?')

`preguntar` consulta a Ollama en un hilo, muestra la respuesta en un
globo de diálogo (`npc.subtitulo`, un `Globo` que flota sobre el NPC)
y, si `npc.habla` es True, la sintetiza con Piper y la reproduce.
`hablar(texto)` dice algo sin consultar; `decir(texto)` solo lo
muestra. `al_responder = fn` engancha un callback con la respuesta.
`voz='mujer'`/`'hombre'`/nombre de Piper elige la voz.

Como `personaje` acepta 'robot'/'humanoide'/'mono'/'arania'/
'espectro' o la ruta a un `.glb`/`.obj` propio.

### Globos de diálogo

`pilas.actores.Globo` es un bocadillo 2D que sigue a cualquier actor
(el mismo que usa `ActorIA` de subtítulo)::

    npc = pilas.actores.Mono(x=2)
    globo = pilas.actores.Globo(npc, 'hola!')
    globo.decir('¿cómo andás?', duracion=3)   # se oculta solo
    globo.actor = otro                        # reconectar
    globo.alto = 2.5                          # altura sobre los pies

Se oculta solo si el actor queda detrás de la cámara.

Los textos largos se reparten en varios globos: `decir` corta a
`lineas_por_pagina` (4) líneas de `ancho_caracteres` (34) y las
páginas avanzan solas — con `duracion` > 0 es N segundos por globo
y se oculta al final; con 0 avanzan a ritmo de lectura y la última
queda fija. Así una respuesta larga de la IA no tapa la escena.

## 8. Variables de entorno

| Variable | Default | Qué hace |
|---|---|---|
| `PILAS3D_IA_MODELO` | `qwen2.5-coder:0.5b` | Modelo a usar/descargar |
| `PILAS3D_IA_GPU` | *(vacío = CPU)* | `=1` deja que Ollama use la GPU |
| `PILAS3D_VOZ` | `es_ES-davefx-medium` | Voz de Piper (`<locale>-<nombre>-<calidad>`) |

Por defecto se fuerza `num_gpu=0` (CPU): funciona en cualquier equipo,
incluso sin drivers de GPU. Con `PILAS3D_IA_GPU=1` Ollama autodetecta
CUDA/Metal/ROCm.

---

## 9. Resolución de problemas

| Síntoma | Causa y arreglo |
|---|---|
| `asistente no disponible: no se pudo descargar Ollama` | Sin internet o firewall. Instalalo desde ollama.com (queda en PATH y se usa ese). |
| `Ollama no arrancó en 10 segundos` | El binario no es ejecutable o el puerto 11434 está ocupado por algo que no es Ollama. Probá `pilas3d/_vendor/ollama/ollama serve` a mano. |
| La descarga del modelo se corta | Volvé a llamar `pilas.ayuda("...")`: `ollama pull` reanuda. |
| Respuestas lentas | Es CPU. Probá `PILAS3D_IA_GPU=1` o un modelo más chico. |
| Respuestas que inventan métodos | Reportalo: el system prompt se puede ajustar, o subir a `qwen2.5-coder:7b`. |
| Quiero desactivar la IA | No llames a `ayuda("...")`. Nada corre en segundo plano. Para limpiar: borrar `pilas3d/_vendor/` y `~/.ollama`. |

---

## 10. Detalles de implementación

- **Sin dependencias nuevas**: usa `urllib`, no `requests`.
- **Licencia**: Ollama es MIT pero su binario no se redistribuye en el
  repo — `pilas3d/_vendor/` está en `.gitignore`.
- **Privacidad**: después de la descarga inicial no hay llamadas de
  red; Ollama corre en `localhost` y Piper es un binario local.
- **Voz**: Piper (MIT) y las voces se bajan a `_vendor/piper/` —
  mismo criterio que Ollama: no se redistribuyen en el repo.
- **Límite conocido**: el timeout de una respuesta es 300 s; en CPU
  una respuesta típica tarda 10–60 s según el equipo.


## 11. Respuestas más rápidas

La integración ya incluye varias optimizaciones:

- **`keep_alive: 10m`** — el modelo queda cargado en memoria entre
  preguntas; no se paga la recarga cada vez.
- **`num_predict = 220`** (`PILAS3D_IA_MAX_TOKENS`) — corta respuestas
  largas: un NPC no necesita miles de tokens.
- **`num_ctx = 2048`** (`PILAS3D_IA_CTX`) — contexto acotado, menos
  prefill en CPU.
- **Streaming** — `ActorIA.preguntar` va llenando el globo palabra a
  palabra mientras el modelo genera (latencia percibida ~0).
- **Calentamiento** — al crear un `ActorIA` se pre-carga el modelo en
  un hilo; la primera pregunta real sale rápida.
- **GPU** — `PILAS3D_IA_GPU=1` deja de forzar `num_gpu=0` (5-10× si hay
  GPU compatible).
- **Modelo más chico** — `PILAS3D_IA_MODELO` permite usar uno más
  veloz (p.ej. `smollm2:135m` vuela en CPU).

## 12. `pilas.habilidades.Cerebro`: el actor piensa solo

Habilidad que convierte a cualquier actor en un NPC dirigido por el
LLM local. Cada `cada` segundos el cerebro describe el estado del
actor al modelo y éste responde UNA acción JSON de una lista cerrada:

```python
mono = pilas.actores.Mono()
mono.aprender(pilas.habilidades.Cerebro,
              cada=3,
              personalidad='sos un mono timido que evita a todos',
              objetivo=jugador,       # actor a observar
              radio_vista=10)
```

Acciones que puede elegir el modelo (lista blanca, **sin `eval`**):

| Acción | Efecto sobre el actor |
|---|---|
| `mover(dx, dz)` | `x += dx; z += dz` y mira hacia donde va |
| `girar(grados)` | `rotacion_y += grados` |
| `ir_a(x, z)` | se teletransporta |
| `decir(texto)` | globo de diálogo (usa `actor.decir`) |
| `acercarse` / `alejarse` | un paso hacia/desde `objetivo` |
| `esperar` | nada este turno |

Detalles:

- El pensamiento corre en un hilo; si el modelo tarda, el juego sigue
  y el actor espera (una petición a la vez).
- Si la respuesta no parsea, se descarta y cuenta en `cerebro.fallos`.
- `cerebro.ultima_decision` guarda la última acción para depurar.
- Ejemplo completo: `ejemplos/cerebro.py`.

## 13. `pilas.actores.Chat`: hablarle al actor con cerebro

Actor invisible que conecta el teclado con el cerebro de un NPC:
al pulsar la tecla (por defecto `t`) se abre un cuadro de texto
(`pilas.pedir_texto`) y el mensaje viaja al LLM junto con el estado
del actor:

```python
mono.aprender(pilas.habilidades.Cerebro,
              personalidad='sos un mono charlatan')
chat = pilas.actores.Chat(mono, tecla='t')
# pulsá T -> escribí "vení" -> el mono responde/acerca
```

La respuesta pasa por el **mismo canal que el cerebro**: el modelo
devuelve una acción de la lista cerrada, así que el NPC no solo
habla — también actúa (`"vení"` → `acercarse`, `"hola"` → `decir`).
Si el actor no tiene cerebro pero es un `ActorIA`, se delega a su
`preguntar` (con voz Piper); si no tiene nada, responde con el
asistente en su globo.

Bloques nuevos en el editor (categoría IA + Apariencia):
`darle cerebro`, `crear chat` y `poner el cielo` (estrellas/día/
textura del paquete). Ejemplo precargado: **"NPC con cerebro (IA)"**.

## 14. `pilas.ia`: un punto de acceso único

El namespace junta todo lo del asistente:

```python
pilas.ia.preguntar('¿cómo hago un enemigo que persiga?')
pilas.ia.modelo                 # el modelo en uso
pilas.ia.modelo = 'smollm2:135m'  # queda guardado en la config
pilas.ia.calentar()             # pre-carga el modelo (en un hilo)
pilas.ia.disponible()           # ¿hay servidor + modelo? (sin bajar nada)
pilas.ia.modelos()              # los instalados en el Ollama local
```

**Orden de precedencia del modelo:**
`PILAS3D_IA_MODELO` > `~/.pilas3d/config.json` (`ia_modelo`) >
`qwen2.5-coder:0.5b` (default). El instalador y
`python -m pilas3d.ia <modelo>` ya escriben la config — el modelo
elegido queda fijo sin exportar variables.

## 15. `pilas.eventos` y `pilas.camara`

- `pilas.eventos` — bus propio del juego:
  `pilas.eventos.cuando('golpe', fn)` (o `@pilas.eventos.cuando('golpe')`)
  y `pilas.eventos.emitir('golpe', 10)`. Sirve para que actores,
  habilidades y escenas se hablen sin referencias directas.
- `pilas.camara` — atajo de `pilas.escena_actual().camara`:
  `pilas.camara.seguir_a(actor, modo='tercera')`,
  `pilas.camara.usar_control_orbital()`, `pilas.camara.proyectar(x,y,z)`.
  Los bloques de Blockly ya generan esta forma.
- `pilas.colisiones` — utilidades de colisión en el plano XZ:
  `pilas.colisiones.colisionan(a, b)` (atajo de
  `a.colisiona_en_plano_con(b)`), `caja_desde_actor` y
  `resolver_circulo_en_cajas` para paredes/obstáculos.
