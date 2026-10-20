import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 100
HEIGHT = 32
FRAME_COUNT = 48
CHARACTERS = " .,:;!+*#%@"
COLORS = [
    (13, 17, 23),
    (92, 40, 16),
    (132, 53, 17),
    (173, 66, 17),
    (207, 78, 18),
    (231, 91, 22),
    (245, 117, 39),
    (255, 145, 69),
    (255, 181, 113),
    (255, 216, 170),
    (255, 239, 214),
]


def load_font(size):
    candidates = [
        "DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_frame(frame_index, font):
    angle_a = 0.2 + frame_index * 2 * math.pi / FRAME_COUNT
    angle_b = 0.2 + frame_index * 4 * math.pi / FRAME_COUNT
    z_buffer = [[-1.0] * WIDTH for _ in range(HEIGHT)]
    pixels = [[" "] * WIDTH for _ in range(HEIGHT)]
    sin_a, cos_a = math.sin(angle_a), math.cos(angle_a)
    sin_b, cos_b = math.sin(angle_b), math.cos(angle_b)
    light = (-0.4, 0.7, -0.6)

    for theta_step in range(256):
        theta = theta_step * 2 * math.pi / 256
        sin_theta, cos_theta = math.sin(theta), math.cos(theta)
        for phi_step in range(128):
            phi = phi_step * 2 * math.pi / 128
            sin_phi, cos_phi = math.sin(phi), math.cos(phi)
            radius = 1 + 0.42 * cos_phi
            x = radius * cos_theta
            y = radius * sin_theta
            z = 0.42 * sin_phi

            normal_x = cos_phi * cos_theta
            normal_y = cos_phi * sin_theta
            normal_z = sin_phi

            rotated_x = x * cos_b + z * sin_b
            rotated_z = -x * sin_b + z * cos_b
            rotated_y = y * cos_a - rotated_z * sin_a
            rotated_z = y * sin_a + rotated_z * cos_a
            rotated_normal_x = normal_x * cos_b + normal_z * sin_b
            rotated_normal_z = -normal_x * sin_b + normal_z * cos_b
            rotated_normal_y = normal_y * cos_a - rotated_normal_z * sin_a
            rotated_normal_z = normal_y * sin_a + rotated_normal_z * cos_a

            perspective = 1 / (3.8 - rotated_z)
            column = int(WIDTH / 2 + 120 * rotated_x * perspective)
            row = int(HEIGHT / 2 - 45 * rotated_y * perspective)
            diffuse = (
                rotated_normal_x * light[0]
                + rotated_normal_y * light[1]
                + rotated_normal_z * light[2]
            )

            if 0 <= column < WIDTH and 0 <= row < HEIGHT and rotated_z > z_buffer[row][column]:
                z_buffer[row][column] = rotated_z
                brightness = 0.12 + max(0, min(1, (diffuse + 1) / 2)) * 0.88
                shade = max(1, min(len(CHARACTERS) - 1, int(brightness * (len(CHARACTERS) - 1))))
                pixels[row][column] = CHARACTERS[shade]

    canvas = Image.new("RGB", (760, 420), (13, 17, 23))
    draw = ImageDraw.Draw(canvas)
    cell_width = draw.textlength("M", font=font)
    cell_height = font.size + 2
    start_x = (canvas.width - WIDTH * cell_width) / 2
    start_y = (canvas.height - HEIGHT * cell_height) / 2

    for row_index, row in enumerate(pixels):
        for column_index, character in enumerate(row):
            if character == " ":
                continue
            shade = CHARACTERS.index(character)
            draw.text(
                (start_x + column_index * cell_width, start_y + row_index * cell_height),
                character,
                font=font,
                fill=COLORS[shade],
            )
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Generate a looping ASCII torus GIF.")
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.parent.mkdir(parents=True, exist_ok=True)

    font = load_font(11)
    frames = [render_frame(index, font) for index in range(FRAME_COUNT)]
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
        optimize=True,
        disposal=2,
    )


if __name__ == "__main__":
    main()
