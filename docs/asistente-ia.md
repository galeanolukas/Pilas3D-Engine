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
python -m pilas3d.ia --lista            # catálogo sugerido
python -m pilas3d.ia qwen2.5-coder:7b   # descarga otro modelo
PILAS3D_IA_MODELO=qwen2.5-coder:7b      # usarlo (env)
```

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

---

## 7. Variables de entorno

| Variable | Default | Qué hace |
|---|---|---|
| `PILAS3D_IA_MODELO` | `qwen2.5-coder:0.5b` | Modelo a usar/descargar |
| `PILAS3D_IA_GPU` | *(vacío = CPU)* | `=1` deja que Ollama use la GPU |

Por defecto se fuerza `num_gpu=0` (CPU): funciona en cualquier equipo,
incluso sin drivers de GPU. Con `PILAS3D_IA_GPU=1` Ollama autodetecta
CUDA/Metal/ROCm.

---

## 8. Resolución de problemas

| Síntoma | Causa y arreglo |
|---|---|
| `asistente no disponible: no se pudo descargar Ollama` | Sin internet o firewall. Instalalo desde ollama.com (queda en PATH y se usa ese). |
| `Ollama no arrancó en 10 segundos` | El binario no es ejecutable o el puerto 11434 está ocupado por algo que no es Ollama. Probá `pilas3d/_vendor/ollama/ollama serve` a mano. |
| La descarga del modelo se corta | Volvé a llamar `pilas.ayuda("...")`: `ollama pull` reanuda. |
| Respuestas lentas | Es CPU. Probá `PILAS3D_IA_GPU=1` o un modelo más chico. |
| Respuestas que inventan métodos | Reportalo: el system prompt se puede ajustar, o subir a `qwen2.5-coder:7b`. |
| Quiero desactivar la IA | No llames a `ayuda("...")`. Nada corre en segundo plano. Para limpiar: borrar `pilas3d/_vendor/` y `~/.ollama`. |

---

## 9. Detalles de implementación

- **Sin dependencias nuevas**: usa `urllib`, no `requests`.
- **Licencia**: Ollama es MIT pero su binario no se redistribuye en el
  repo — `pilas3d/_vendor/` está en `.gitignore`.
- **Privacidad**: después de la descarga inicial no hay llamadas de
  red; todo corre en `localhost`.
- **Límite conocido**: el timeout de una respuesta es 300 s; en CPU
  una respuesta típica tarda 10–60 s según el equipo.
