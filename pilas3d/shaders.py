# -*- encoding: utf-8 -*-
"""Shaders GLSL compartidos por todos los actores.

Un único programa con iluminación: una luz direccional (el "sol") más
hasta 8 luces puntuales con atenuación lineal — ver ``pilas3d.luces``.
Soporta texturas (``usar_textura`` + ``textura``) y descarta píxeles
transparentes. Los vértices sin normal (líneas del piso, ejes) se
dibujan con su color plano.
"""

MAX_LUCES = 8

VERTEX_SHADER = """#version 330 core

in vec3 position;
in vec3 normal;
in vec4 color;
in vec2 texcoords;

uniform mat4 proyeccion;
uniform mat4 vista;
uniform mat4 modelo;
uniform mat4 matriz_luz;         // mundo -> espacio de la sombra
uniform vec2 uv_escala;
uniform vec2 uv_desplazamiento;
uniform float punto_tamano;    // tamaño en px para GL_POINTS

out vec4 v_color;
out vec2 v_tex;
out vec3 v_normal;
out vec3 v_posicion;
out vec4 v_pos_luz;

void main()
{
    gl_Position = proyeccion * vista * modelo * vec4(position, 1.0);
    v_posicion = vec3(modelo * vec4(position, 1.0));
    v_pos_luz = matriz_luz * vec4(v_posicion, 1.0);
    v_normal = mat3(modelo) * normal;
    v_color = color;
    v_tex = texcoords * uv_escala + uv_desplazamiento;
    gl_PointSize = punto_tamano;
}
"""

FRAGMENT_SHADER = """#version 330 core
#define MAX_LUCES %d

in vec4 v_color;
in vec2 v_tex;
in vec3 v_normal;
in vec3 v_posicion;

uniform sampler2D textura;
uniform bool usar_textura;

// mapas compuestos opcionales (pilas.materiales)
uniform sampler2D normal_map;
uniform bool usar_normal;
uniform sampler2D ao_map;
uniform bool usar_ao;
uniform sampler2D rugosidad_map;
uniform bool usar_rugosidad;

// Normal map sin tangentes: reconstruye el marco TBN con derivadas
// de pantalla (Schüler) — funciona para cualquier malla con UVs.
vec3 perturbar_normal(vec3 n, vec3 pos, vec2 uv)
{
    vec3 q0 = dFdx(pos);
    vec3 q1 = dFdy(pos);
    vec2 st0 = dFdx(uv);
    vec2 st1 = dFdy(uv);
    vec3 s = q0 * st1.t - q1 * st0.t;
    vec3 t = -q0 * st1.s + q1 * st0.s;
    vec3 N = normalize(n);
    if (dot(s, s) < 1e-8 || dot(t, t) < 1e-8)
        return N;
    vec3 map_n = texture(normal_map, uv).xyz * 2.0 - 1.0;
    return normalize(mat3(normalize(s), normalize(t), N) * map_n);
}

uniform vec3 luz_dir;          // dirección HACIA la luz direccional
uniform vec3 luz_dir_color;
uniform float luz_ambiente;
uniform vec3 luz_ambiente_color;  // tinte del ambiente (de un .hdr)
uniform bool sin_luz;          // el actor se dibuja a color plano
                              // (lámparas, sprites brillantes)
uniform bool tonemap;          // HDR: comprime rgb >1 a pantalla
uniform float exposicion;      // cuanta luz HDR entra (1 = normal)
uniform int cantidad_puntuales;
uniform vec3 luz_posicion[MAX_LUCES];
uniform vec3 luz_color[MAX_LUCES];
uniform float luz_alcance[MAX_LUCES];

uniform bool usar_niebla;
uniform vec3 niebla_color;
uniform float niebla_inicio;
uniform float niebla_fin;
uniform vec3 cam_pos;

// shadow map de la direccional (pilas3d.sombras)
uniform sampler2D mapa_sombras;
uniform bool usar_sombras;
in vec4 v_pos_luz;

// factor de luz que llega: 1 = sol pleno, 0 = sombra total
float factor_sombra(vec3 n, vec3 hacia_luz)
{
    vec3 p = v_pos_luz.xyz / v_pos_luz.w * 0.5 + 0.5;
    if (p.z > 1.0 || p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0)
        return 1.0;                          // fuera del mapa
    // bias proporcional al ángulo (menos en granizo = menos acné)
    float bias = max(0.0007, 0.003 * (1.0 - dot(n, hacia_luz)));
    float suma = 0.0;
    vec2 texel = 1.0 / vec2(textureSize(mapa_sombras, 0));
    for (int x = -1; x <= 1; ++x)
        for (int y = -1; y <= 1; ++y)
            suma += step(p.z - bias,
                         texture(mapa_sombras,
                                 p.xy + vec2(x, y) * texel).r);
    return suma / 9.0;
}

out vec4 fragmento;

void main()
{
    vec4 base = usar_textura ? texture(textura, v_tex) : vec4(1.0);
    vec4 difuso = base * v_color;
    // Descarta píxeles transparentes (sprites/billboards).
    if (difuso.a < 0.1) discard;

    vec3 luz_rgb = vec3(1.0);
    if (!sin_luz && length(v_normal) > 0.001) {
        vec3 n = normalize(v_normal);
        if (usar_normal)
            n = perturbar_normal(v_normal, v_posicion, v_tex);
        // oclusión ambiental: solo atenúa la luz ambiente y parte
        // de las puntuales (aproximación educativa, no SSAO)
        float ao = usar_ao ? texture(ao_map, v_tex).r : 1.0;
        float rugosidad = usar_rugosidad
                          ? texture(rugosidad_map, v_tex).r : 1.0;
        luz_rgb = luz_ambiente * luz_ambiente_color * ao;
        vec3 hacia_luz = normalize(luz_dir);
        float dif_dir = max(dot(n, hacia_luz), 0.0);
        float sombra = usar_sombras ? factor_sombra(n, hacia_luz)
                                    : 1.0;
        luz_rgb += luz_dir_color * dif_dir * 0.65 * sombra;
        for (int i = 0; i < cantidad_puntuales; i++) {
            vec3 d = luz_posicion[i] - v_posicion;
            float aten = clamp(1.0 - length(d) / luz_alcance[i],
                             0.0, 1.0);
            luz_rgb += luz_color[i]
                       * max(dot(n, normalize(d)), 0.0)
                       * aten * aten * 0.65 * (0.5 + 0.5 * ao);
        }
        // especular Blinn-Phong solo de la direccional, guiado por
        // rugosidad (liso = brillo fino e intenso, rugoso = casi nada)
        if (dif_dir > 0.0) {
            vec3 vista = normalize(cam_pos - v_posicion);
            vec3 h = normalize(hacia_luz + vista);
            float pot = mix(64.0, 8.0, rugosidad);
            float inten = mix(0.4, 0.05, rugosidad);
            luz_rgb += luz_dir_color
                       * pow(max(dot(n, h), 0.0), pot) * inten
                       * sombra;
        }
    }
    vec3 rgb = difuso.rgb * luz_rgb;
    // Fondos HDR (texturas float GL_RGBA16F): curva de exposición
    // + paso a sRGB — solo donde el actor lo pide (domo del Cielo).
    if (tonemap) {
        rgb = vec3(1.0) - exp(-rgb * exposicion);
        rgb = pow(rgb, vec3(1.0 / 2.2));
    }
    // Niebla lineal solo sobre fragmentos iluminados (el cielo y las
    // líneas de debug no tienen normal y quedan limpios).
    if (usar_niebla && length(v_normal) > 0.001) {
        float dist = distance(v_posicion, cam_pos);
        float f = clamp((dist - niebla_inicio)
                        / (niebla_fin - niebla_inicio), 0.0, 1.0);
        rgb = mix(rgb, niebla_color, f);
    }
    fragmento = vec4(rgb, difuso.a);
}
""" % MAX_LUCES

_programa = None


def obtener_programa():
    """Retorna el ShaderProgram compartido (se compila una sola vez)."""
    global _programa
    if _programa is None:
        from pyglet.graphics.shader import Shader, ShaderProgram

        _programa = ShaderProgram(
            Shader(VERTEX_SHADER, "vertex"),
            Shader(FRAGMENT_SHADER, "fragment"),
        )
    return _programa
