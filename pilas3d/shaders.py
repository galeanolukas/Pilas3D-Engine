# -*- encoding: utf-8 -*-
"""Shaders GLSL compartidos por todos los actores.

Usa un único programa con iluminación difusa simple. Los vértices sin
normal (normales de longitud cero, como las líneas del piso o los ejes)
se dibujan con su color plano.
"""

VERTEX_SHADER = """#version 330 core

in vec3 position;
in vec3 normal;
in vec4 color;

uniform mat4 proyeccion;
uniform mat4 vista;
uniform mat4 modelo;

out vec4 v_color;

void main()
{
    gl_Position = proyeccion * vista * modelo * vec4(position, 1.0);

    vec3 n = normalize(mat3(modelo) * normal);
    vec3 luz = normalize(vec3(0.4, 0.8, 0.5));
    float difusa = max(dot(n, luz), 0.0);
    float factor = length(normal) < 0.001 ? 1.0 : (0.35 + 0.65 * difusa);

    v_color = vec4(color.rgb * factor, color.a);
}
"""

FRAGMENT_SHADER = """#version 330 core

in vec4 v_color;
out vec4 fragmento;

void main()
{
    fragmento = v_color;
}
"""

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
