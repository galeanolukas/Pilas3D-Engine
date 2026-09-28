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
