# Empaquetar: tu juego como ejecutable

`pilas3d-empaquetar` usa PyInstaller para meter el intérprete de
Python + pilas3d + pyglet + los datos del motor en **un solo
ejecutable** — la otra persona no instala nada.

```bash
pip install pyinstaller            # una vez

pilas3d-empaquetar ejemplos/lampara.py
# -> dist/lampara   (Linux)  /  dist\lampara.exe  (Windows)
```

## Qué viaja dentro

- Python, pilas3d, pyglet (con sus drivers de plataforma)
- `pilas3d/data/` — texturas, sonidos y el logo del motor
- pymunk + sus binarios de Chipmunk **si está instalado** (física)
- lo que pases con `--incluir` — ver abajo

## Assets del juego: `--incluir`

Los modelos, texturas y sonidos **del juego** no viajan solos —
agregá sus carpetas:

```bash
pilas3d-empaquetar mi_juego.py --incluir modelos --incluir sonidos
```

Se empaquetan con el mismo nombre relativo, así que el juego los
encuentra igual que siempre (`'modelos/fox.glb'` funciona igual
adentro del exe).

## Opciones

| flag | efecto |
|---|---|
| `--nombre X` | nombre del ejecutable |
| `--incluir DIR` | carpeta de assets (repetible) |
| `--icono X` | `.ico` en Windows, `.png` en Linux/Mac |
| `--consola` | deja una terminal visible (para depurar) |
| `--dist DIR` | carpeta de salida (default `dist/`) |
| `--workflow` | no compila: escribe el workflow multi-SO |

## Los tres sistemas operativos: `--workflow`

PyInstaller **no cross-compila**: el exe que sale es del SO donde
corriste el comando. Para generar los tres de una vez, GitHub
Actions puede compilar cada uno en su runner:

```bash
pilas3d-empaquetar ejemplos/lampara.py --incluir modelos --workflow
# escribe .github/workflows/ejecutables.yml
git add .github && git push
```

Después de cada push, en *Actions → ejecutables → Artifacts* bajás
`lampara-ubuntu-latest`, `lampara-windows-latest` y
`lampara-macos-latest`.

## Notas

- El exe pesa ~15 MB mínimo (intérprete + motor + pyglet).
- La primera ejecución tarda un poco: descomprime todo en una
  carpeta temporal (`_MEI…`).
- Si el juego usa Ollama/IA, el ejecutable sigue necesitando que
  Ollama esté instalado en la máquina — es un servicio, no viaja.
- Los proyectos de **bloques** se exportan con el botón 🌐 Web del
  editor (generan un `.html`, no un exe). Para empaquetar uno como
  exe, copiá el "Código Python generado" a un `.py` y pasáselo a
  `pilas3d-empaquetar`.
