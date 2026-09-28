# Guía: pilas3d bloques

Programación por bloques estilo Scratch que genera y ejecuta **Python
real** sobre el motor — el puente entre jugar con bloques y escribir
código. Inspirado en Pilas Bloques.

```bash
.venv/bin/pilas3d-bloques
```

Arranca **solo el servidor** y abre el navegador con el editor de
bloques en `http://127.0.0.1:8765/` — la ventana 3D aparece recién al
pulsar **▶ Ejecutar** (corre en un proceso propio) y el botón pasa a
**■ Detener** para cerrarla.

---

## 1. Cómo funciona

```
bloques en el navegador → Python generado (visible a la derecha)
   → ▶ Ejecutar → POST al servidor → subproceso abre la ventana 3D
   → ■ Detener → cierra el subproceso y la ventana
```

Si el código falla, el panel "Resultado" muestra el traceback — el
servidor y el editor siguen vivos.

### Ejemplos precargados

El menú **ejemplos…** del header carga workspaces armados (`Hola
cubo`, `Cubo girando`, `Mover con flechas`, `Choque entre actores`):
se ve el armado en bloques, el Python que generan a la derecha y se
pueden ejecutar con ▶. Están en `pilas3d/bloques_web/ejemplos.js`
como XML de Blockly — para agregar uno, otra entrada en `EJEMPLOS`.

## 2. Los bloques

| Categoría | Bloques |
|---|---|
| **Eventos** | `al iniciar`, `por siempre` (cada frame), `al hacer click en <actor\|cualquier lugar>`, `al pulsar la tecla <t>` (letras, flechas, espacio, enter, escape) |
| **Actores** | `crear <tipo>` (cubo, esfera, robot, humanoide, mono, araña, espectro), `crear modelo <ruta.glb>`, `crear <escenario>` (piso, ejes, plano, pared, cartel), `eliminar` |
| **Movimiento** | `mover <a> en <eje> <n>` (`a.x += 0.05`), `llevar a x y z`, `girar en <eje> <grados>` |
| **Apariencia** | `poner de color`, `mostrar texto`, `escribir en consola` (print → aparece en "Resultado"), `hacer que <a> diga <texto>` (globo de diálogo), `animar <modelo>`, `reproducir sonido`, `crear menú` + `opción` (navegable con flechas/ENTER o mouse) |
| **Tiempo** | `llevar suave a x y z en N s` con curva a elección (normal, suave al arrancar/frenar, rebote, elástica), `esperar N s y hacer`, `cada N s hacer` |
| **Cámara** | `cámara orbital con el mouse`, `la cámara sigue a <a>` (primera/de frente/tercera), `soltar la cámara` |
| **Sensores** | `tecla <t> pulsada`, `botón del mouse pulsado`, `posición x/y del mouse`, `<a> toca a <b>`, comparaciones lógicas |
| **Control** | `si`, `repetir N`, números |
| **Matemática** | número, operaciones |

El **nombre** que se le da al actor en `crear` es el nombre de la
variable Python. Los bloques que usan actores (`mover`, `girar`,
`decir`…) lo eligen de un **menú** que se llena solo con los actores
ya creados — no hay que tipear nombres.

### Guardar y abrir proyectos

El editor **guarda solo**: cada cambio queda en `localStorage` y al
reabrir la página el workspace se restaura. Los botones **Guardar** y
**Abrir** exportan/importan el programa como `*.bloques.xml` — para
pasar ejercicios entre alumnos o dejarlos en un pendrive.

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
  `127.0.0.1:8765` (solo local). Sin pilas: `/codigo` lanza
  `bloques_runner.py` como subproceso (su ventana 3D es del proceso
  hijo) y `/detener` lo mata. Con pilas (modo legado/tests): ejecuta
  el código **en el hilo principal** una vez por frame.
- `pilas3d/bloques_runner.py` — proceso hijo que corre el código
  generado con `pilas` ya inicializada.
- `pilas3d/bloques_web/` — la página: Blockly 9.3 vendored (offline,
  sin internet), definiciones en `bloques.js`, ejemplos precargados
  en `ejemplos.js`, renderer `zelos` (el estilo visual de Scratch).
- `pilas3d/bloques.py` — `main()`: levanta el servidor y abre el
  navegador (sin ventana 3D).

### Agregar un bloque nuevo

En `bloques.js`: un `defineBlocksWithJsonArray` + un `registrar` con
el generador. Si el bloque crea un actor con nombre, agregarlo a
`CREA_NOMBRE` para que aparezca en los `global`.

## 5. Límites

- Solo localhost, sin autenticación — no exponer el puerto.
- Los errores del código generado aparecen en "Resultado", no sobre
  el bloque que falló.
- No hay bloques de variables/listas todavía.
- Es v1: el set de bloques está pensado para iterarse con la práctica
  en aula (Pilas Bloques hizo eso durante años).
