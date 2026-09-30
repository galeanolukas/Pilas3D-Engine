# Física 2D (`pilas.fisica`)

Física realista para el mundo 3D con **pymunk** (Chipmunk2D).
Dependencia opcional:

```bash
pip install pymunk          # o: pip install "pilas3d[fisica]"
```

## El plano

El motor es 3D, pero la mecánica de la mayoría de los géneros es
plana. Elegís el plano una vez:

| `pilas.fisica.plano` | Uso | Gravedad por defecto |
|---|---|---|
| `'xy'` | plataformas / vista lateral | `(0, -9.8)` |
| `'xz'` | vista cenital (top-down) | `(0, 0)` |

En `xy` el cuerpo escribe `actor.x`, `actor.y` y `rotacion_z`;
en `xz` escribe `actor.x`, `actor.z` y `rotacion_y`.

## Vincular actores

```python
pilas.fisica.plano = 'xy'
pilas.fisica.gravedad = (0, -12)

pelota = pilas.actores.Esfera(y=6, radio=0.4)
pelota.radio_de_colision = 0.4
pilas.fisica.vincular(pelota, forma='circulo', elasticidad=0.9)

suelo = pilas.actores.Cubo()
pilas.fisica.vincular(suelo, estatico=True, ancho=30, alto=1)

plataforma_movil = pilas.actores.Cubo(x=3, y=4)
pilas.fisica.vincular(plataforma_movil, cinematica=True)
```

- **`forma`**: `'caja'` (default), `'circulo'`, `'segmento'`
  (suelos de un tramo de `ancho`)
- **`estatico=True`**: nunca se mueve (pisos, paredes)
- **`cinematica=True`**: lo mueve el juego — el cuerpo sigue al
  actor cada frame y empuja lo dinámico (jugador por teclado,
  plataformas móviles)
- **`sensor=True`**: detecta el contacto pero no empuja
  (monedas, gatillos, zonas)
- **`ancho`/`alto`/`radio`**: por defecto salen de
  `actor.radio_de_colision`
- **`friccion`** (0–1+), **`elasticidad`** (0–1+), **`masa`**

## El cuerpo del actor

`vincular` deja `actor.cuerpo`:

```python
cuerpo.velocidad = (5, 8)      # u,v en el plano
cuerpo.impulsar(0, 6)          # salto / disparo
cuerpo.detener()
cuerpo.posicion                # (u, v)
cuerpo.pymunk                  # body crudo por si hace falta más
```

## Colisiones

```python
pilas.fisica.cuando_colisionan(pelota, jugador, al_tocar)

def al_tocar(a, b):
    puntaje.valor += 1
```

Se dispara al empezar el contacto; con `sensor=True` llega el aviso
sin respuesta física.

## Limpieza

- `fisica.desvincular(actor)` — el actor deja de simularse
- `fisica.limpiar()` — suelta todos (al cambiar de nivel)
- `actor.eliminar()` suelta su cuerpo solo en el próximo paso

## Ejemplo

`ejemplos/fisica_plataformas.py` — cubo que se mueve con flechas,
cajas que caen, pelota que rebota y puntaje por contacto.

## Limitaciones (a propósito)

- Es física **2D**: los cuerpos viven en un plano, no hay gravedad
  3D ni colisiones entre esferas reales — para eso haría falta un
  motor 3D (p. ej. pybullet), que es otro nivel de complejidad.
- Los cuerpos no rotan en el eje "perpendicular" visible: en `xy`
  rotan en Z, en `xz` en Y.
