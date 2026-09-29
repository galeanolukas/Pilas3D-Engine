# -*- encoding: utf-8 -*-
"""Utilidades de colisión en el plano XZ.

Las paredes son cajas alineadas a los ejes (AABB); los actores se
aproximan por un círculo de ``radio_de_colision`` al caminar.
"""


def caja_desde_actor(actor, ancho, profundidad):
    """AABB (min_x, max_x, min_z, max_z) de un actor tipo pared.

    Tiene en cuenta ``rotacion_y`` proyectando las 4 esquinas de la
    base rectangular rotada.
    """
    import math

    hx, hz = ancho / 2.0, profundidad / 2.0
    esquinas = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    a = math.radians(actor.rotacion_y)
    c, s = math.cos(a), math.sin(a)
    puntos = [(x * c + z * s + actor.x, -x * s + z * c + actor.z)
              for x, z in esquinas]
    xs = [p[0] for p in puntos]
    zs = [p[1] for p in puntos]
    return (min(xs), max(xs), min(zs), max(zs))


def resolver_circulo_en_cajas(x, z, radio, cajas):
    """Empuja al círculo (x, z, radio) fuera de cada caja.

    Retorna la nueva posición (x, z) sin penetrar obstáculos.
    """
    for (min_x, max_x, min_z, max_z) in cajas:
        cx = max(min_x, min(x, max_x))
        cz = max(min_z, min(z, max_z))
        dx, dz = x - cx, z - cz
        d2 = dx * dx + dz * dz

        if d2 >= radio * radio:
            continue

        if d2 > 1e-9:
            # Punto más cercano del borde: empujar hacia afuera.
            d = d2 ** 0.5
            x = cx + dx / d * radio
            z = cz + dz / d * radio
        else:
            # El centro está dentro de la caja: salir por la cara
            # de menor penetración.
            empujes = [
                (max_x - x + radio, 1, 0),
                (x - min_x + radio, -1, 0),
                (max_z - z + radio, 0, 1),
                (z - min_z + radio, 0, -1),
            ]
            empuje = min(empujes, key=lambda e: e[0])
            x += empuje[1] * empuje[0]
            z += empuje[2] * empuje[0]
    return x, z


def colisionan(a, b):
    """True si ``a`` y ``b`` se tocan en el plano XZ (círculos).

    Atajo de ``a.colisiona_en_plano_con(b)`` para cuando no tenés
    claro qué actor preguntar::

        if pilas.colisiones.colisionan(pelota, meta): ...
    """
    return a.colisiona_en_plano_con(b)
