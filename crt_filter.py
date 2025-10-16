"""
CRT Filter Plugin for Pygame / Pygame-CE using ModernGL
-------------------------------------------------------
Drop this into your project, and wrap your rendering with:
    crt = CrtFilter(screen)
    crt.draw(game_surface)

- Provides curved screen distortion
- Scanlines, vignette, flicker, chromatic aberration
- Adjustable shader parameters

Requirements:
    pip install pygame moderngl numpy
"""

import time
import numpy as np
import pygame
import moderngl

VERT_SHADER = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 uv;
void main() {
    uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

FRAG_SHADER = """
#version 330
uniform sampler2D screen_tex;
uniform float time;
uniform vec2 resolution;
in vec2 uv;
out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    vec2 p = uv * 2.0 - 1.0;
    p.x *= resolution.x / resolution.y;

    float curve_strength = 0.12;
    float r2 = dot(p, p);
    vec2 distorted = uv + (p * r2) * curve_strength;

    if (distorted.x < 0.0 || distorted.x > 1.0 || distorted.y < 0.0 || distorted.y > 1.0) {
        fragColor = vec4(0.0);
        return;
    }

    float ca = 0.0025;
    vec2 ca_dir = vec2(1.0, 0.2);
    vec3 col;
    col.r = texture(screen_tex, distorted + ca_dir * ca).r;
    col.g = texture(screen_tex, distorted).g;
    col.b = texture(screen_tex, distorted - ca_dir * ca).b;

    float bright = clamp((col.r + col.g + col.b) / 3.0 - 0.6, 0.0, 1.0);
    col += pow(bright, 2.0) * 0.08;

    float scanline = sin((uv.y * resolution.y) * 1.5) * 0.5 + 0.5;
    col *= mix(0.94, 1.06, scanline * 0.5);

    float n = hash21(uv * resolution.xy + vec2(time));
    float flicker = 1.0 + (n - 0.5) * 0.02;
    col *= flicker;

    float vign = smoothstep(0.8, 0.35,
        length((uv - 0.5) * vec2(resolution.x/resolution.y, 1.0)));
    col *= vign;

    col = pow(col, vec3(0.95));
    fragColor = vec4(col, 1.0);
}
"""


class CrtFilter:
    """Drop-in CRT shader filter for Pygame."""

    def __init__(self, screen: pygame.Surface):
        # Expect an OpenGL-enabled Pygame display surface
        self.screen = screen
        self.width, self.height = screen.get_size()

        # Initialize ModernGL context
        self.ctx = moderngl.create_context(require=320)
        self.ctx.viewport = (0, 0, self.width, self.height)

        # Compile shader program
        self.prog = self.ctx.program(
            vertex_shader=VERT_SHADER, fragment_shader=FRAG_SHADER
        )

        # Fullscreen quad
        verts = np.array(
            [
                -1.0,
                -1.0,
                0.0,
                0.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                -1.0,
                1.0,
                0.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.0,
                1.0,
            ],
            dtype="f4",
        )

        vbo = self.ctx.buffer(verts.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, "in_pos", "in_uv")

        # Texture (will be updated each frame)
        self.texture = self.ctx.texture((self.width, self.height), 4, dtype="u1")
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture.repeat_x = False
        self.texture.repeat_y = False

        # Set shader uniforms
        self.prog["screen_tex"] = 0
        self.prog["resolution"].value = (float(self.width), float(self.height))

        self.start_time = time.time()

    def _surf_to_bytes(self, surf: pygame.Surface) -> bytes:
        """Convert Pygame surface to RGBA bytes (flipped)."""
        return pygame.image.tostring(surf, "RGBA", True)

    def draw(self, frame: pygame.Surface):
        """
        Draw a pygame surface (your rendered frame)
        through the CRT shader to the display.
        """
        tex_bytes = self._surf_to_bytes(frame)
        self.texture.write(tex_bytes)

        # Clear and render the shader
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.texture.use(location=0)
        self.prog["time"].value = float(time.time() - self.start_time)
        self.prog["resolution"].value = (float(self.width), float(self.height))
        self.vao.render(moderngl.TRIANGLES)

        # Swap buffers
        pygame.display.flip()
