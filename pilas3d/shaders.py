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
uniform vec2 uv_escala;
uniform vec2 uv_desplazamiento;
uniform float punto_tamano;    // tamaño en px para GL_POINTS

out vec4 v_color;
out vec2 v_tex;
out vec3 v_normal;
out vec3 v_posicion;

void main()
{
    gl_Position = proyeccion * vista * modelo * vec4(position, 1.0);
    v_posicion = vec3(modelo * vec4(position, 1.0));
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

uniform vec3 luz_dir;          // dirección HACIA la luz direccional
uniform vec3 luz_dir_color;
uniform float luz_ambiente;
uniform int cantidad_puntuales;
uniform vec3 luz_posicion[MAX_LUCES];
uniform vec3 luz_color[MAX_LUCES];
uniform float luz_alcance[MAX_LUCES];

out vec4 fragmento;

void main()
{
    vec4 base = usar_textura ? texture(textura, v_tex) : vec4(1.0);
    vec4 difuso = base * v_color;
    // Descarta píxeles transparentes (sprites/billboards).
    if (difuso.a < 0.1) discard;

    vec3 luz_rgb = vec3(1.0);
    if (length(v_normal) > 0.001) {
        vec3 n = normalize(v_normal);
        luz_rgb = vec3(luz_ambiente);
        luz_rgb += luz_dir_color
                   * max(dot(n, normalize(luz_dir)), 0.0) * 0.65;
        for (int i = 0; i < cantidad_puntuales; i++) {
            vec3 d = luz_posicion[i] - v_posicion;
            float aten = clamp(1.0 - length(d) / luz_alcance[i],
                             0.0, 1.0);
            luz_rgb += luz_color[i]
                       * max(dot(n, normalize(d)), 0.0)
                       * aten * aten * 0.65;
        }
    }
    fragmento = vec4(difuso.rgb * luz_rgb, difuso.a);
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
