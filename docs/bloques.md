# Guía: pilas3d bloques

Programación por bloques estilo Scratch que genera y ejecuta **Python
real** sobre el motor — el puente entre jugar con bloques y escribir
código. Inspirado en Pilas Bloques.

```bash
.venv/bin/pilas3d-bloques
```

Abre dos cosas:

- la **ventana 3D** de pilas3d (donde corre el programa)
- el **navegador** con el editor de bloques en `http://127.0.0.1:8765/`

---

## 1. Cómo funciona

```
bloques en el navegador → Python generado (visible a la derecha)
   → botón Ejecutar → POST al motor → corre en la ventana 3D
```

Cada **Ejecutar** limpia la escena (bandera verde de Scratch): los
actores y tareas de la corrida anterior desaparecen. Si el código
falla, el panel "Resultado" muestra el traceback — el motor sigue
vivo.

## 2. Los bloques

| Categoría | Bloques |
|---|---|
| **Eventos** | `al iniciar` (corre una vez), `por siempre` (corre cada frame — es el "por siempre" de Scratch) |
| **Actores** | `crear <tipo> llamado <nombre>` (cubo, esfera, robot, humanoide, mono, araña, espectro), `crear modelo <ruta.glb>`, `eliminar` |
| **Movimiento** | `mover <a> en <eje> <n>` (`a.x += 0.05`), `llevar a x y z`, `girar en <eje> <grados>` |
| **Apariencia** | `poner de color`, `mostrar texto`, `escribir en consola` (print → aparece en "Resultado"), `animar <modelo> con <animación>` |
| **Sensores** | `tecla <dir> pulsada`, `<a> toca a <b>` (colisión en el piso), comparaciones lógicas |
| **Control** | `si`, `repetir N`, números |
| **Matemática** | número, operaciones |

El **nombre** que se le da al actor en `crear` es el nombre de la
variable Python — usado en `mover`, `girar`, `eliminar`, `colisiona`.

## 3. Ejemplo típico

```
al iniciar
    crear cubo llamado cubo en x 0 y 0 z 0
    crear esfera llamada bola en x 2 y 0 z 0
por siempre
    girar cubo en eje y 3 grados
    si tecla derecha pulsada
        mover cubo en x 0.05
    si cubo toca a bola
        escribir en consola "¡tocó!"
```

Genera Python real:

```python
def iniciar():
    global cubo, bola
    cubo = pilas.actores.Cubo(x=0, y=0, z=0)
    bola = pilas.actores.Esfera(x=2, y=0, z=0)
iniciar()

def siempre():
    global cubo, bola
    cubo.rotacion_y += 3
    if pilas.control.derecha:
        cubo.x += 0.05
    if cubo.colisiona_en_plano_con(bola):
        print('¡tocó!')
pilas.tareas.siempre(0, siempre)
```

## 4. Debajo del capó

- `pilas3d/puente.py` — `PuenteBloques`: `ThreadingHTTPServer` en
  `127.0.0.1:8765` (solo local). El código encolado se ejecuta **en el
  hilo principal** una vez por frame (OpenGL no es thread-safe).
- `pilas3d/bloques_web/` — la página: Blockly 9.3 vendored (offline,
  sin internet), definiciones en `bloques.js`, renderer `zelos` (el
  estilo visual de Scratch).
- `pilas3d/bloques.py` — `main()`: inicia pilas + puente + abre el
  navegador.

### Agregar un bloque nuevo

En `bloques.js`: un `defineBlocksWithJsonArray` + un `registrar` con
el generador. Si el bloque crea un actor con nombre, agregarlo a
`CREA_NOMBRE` para que aparezca en los `global`.

## 5. Límites

- Solo localhost, sin autenticación — no exponer el puerto.
- Los errores del código generado aparecen en "Resultado", no sobre
  el bloque que falló.
- No hay bloques de variables/listas todavía (los nombres de actores
  son campos de texto).
- Es v1: el set de bloques está pensado para iterarse con la práctica
  en aula (Pilas Bloques hizo eso durante años).
