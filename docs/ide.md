# Guía: pilas3d-ide

REPL de Python integrado en la ventana del motor — la alternativa a
`pilas3d` cuando no querés una terminal flotante separada:

```bash
.venv/bin/pilas3d-ide
```

```
┌────────────────────────┬──────────────────┐
│                        │  >>> cubo = ...  │
│      vista 3D          │  (log de salida) │
│      (area_3d)         │                  │
│                        │  >>> |           │
└────────────────────────┴──────────────────┘
```

`pilas` ya está iniciada — escribís `cubo = pilas.actores.Cubo()` y
el cubo aparece al instante a la izquierda.

## Controles

| Tecla | Acción |
|---|---|
| ENTER | ejecutar la línea |
| ENTER en línea vacía | cerrar un bloque multi-línea |
| ↑ / ↓ | historial de líneas |
| ESC | limpiar la línea (no cierra la ventana) |
| Ctrl+S | guardar todo lo ejecutado en `sesion_pilas3d.py` |

## Multi-línea y auto-indentación

Los bloques `def`/`for`/`si` se detectan solos con
`codeop.CommandCompiler` (el mismo mecanismo de la consola estándar
de Python): si el bloque está incompleto el prompt cambia a `...`, la
línea siguiente **ya viene indentada** (y si terminó en `:` suma 4
espacios), y ENTER en una línea vacía cierra el bloque. Con la línea
vacía, TAB inserta indentación a mano.

## Comandos `%`

| Comando | Acción |
|---|---|
| `%run archivo.py` | ejecuta un `.py` (no entra a la sesión) |
| `%abrir archivo.py` | ejecuta **y** lo incorpora a la sesión — `Ctrl+S` lo re-guarda con lo nuevo |
| `%guardar [archivo.py]` | guarda la sesión (default `sesion_pilas3d.py`) |
| `%limpiar` | vacía el log |
| `%ayuda` | lista los comandos |

Flujo típico: trabajás en la consola → `Ctrl+S` → `sesion_pilas3d.py`
→ otro día `%abrir sesion_pilas3d.py` y seguís donde quedaste.

## Notas

- La consola siempre captura el teclado (la escena no recibe teclas
  de juego en este modo — se maneja todo por código).
- Los errores aparecen como traceback en el log, sin romper el motor.
- `pilas.consola_ide.ns` es el namespace donde corre el código —
  accesible también desde una consola externa si hace falta.
- Los `print()` y stderr se capturan al log de la ventana.
