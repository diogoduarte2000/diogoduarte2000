import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 120
HEIGHT = 40
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
    angle = frame_index * 2 * math.pi / FRAME_COUNT
    sin_angle, cos_angle = math.sin(angle), math.cos(angle)
    z_buffer = [[-float("inf")] * WIDTH for _ in range(HEIGHT)]
    shades = [[0] * WIDTH for _ in range(HEIGHT)]
    light = (-0.45, 0.65, 0.75)

    for latitude_step in range(161):
        latitude = -math.pi / 2 + latitude_step * math.pi / 160
        sin_lat, cos_lat = math.sin(latitude), math.cos(latitude)
        vertical = sin_lat
        width_at_latitude = cos_lat * (0.87 + 0.13 * max(0, vertical))
        depth_at_latitude = cos_lat * (0.90 + 0.10 * max(0, vertical))

        for longitude_step in range(321):
            longitude = -math.pi + longitude_step * 2 * math.pi / 320
            sin_lon, cos_lon = math.sin(longitude), math.cos(longitude)
            u = sin_lon
            v = latitude / (math.pi / 2)

            folds = (
                math.sin(5.5 * u + 1.4 * math.sin(4.0 * v + 0.3))
                + 0.65 * math.sin(8.5 * v + 1.7 * math.sin(3.2 * u - 0.5))
                + 0.35 * math.sin(12 * u - 6 * v)
            )
            sulcus = 0.070 * math.exp(-((abs(folds) / 0.16) ** 2))
            center_x = cos_lat * cos_lon
            central_fissure = 0.16 * math.exp(-((center_x / 0.065) ** 2)) * (0.65 + 0.35 * abs(v))
            ridge = 0.025 * folds
            radius = (1.0 + 0.035 * math.cos(6 * longitude + 1.2 * v)) * (
                1.0 - sulcus - central_fissure + ridge
            )

            x = 1.18 * width_at_latitude * cos_lon * radius
            y = 0.88 * vertical * (1 - 0.12 * max(0, -vertical)) * radius
            if vertical > 0.75:
                y -= 0.075 * math.exp(-((center_x / 0.16) ** 2)) * ((vertical - 0.75) / 0.25)
            z = 0.82 * depth_at_latitude * sin_lon * radius
            if vertical < -0.66:
                stem = (-vertical - 0.66) / 0.34
                y -= 0.22 * stem * stem
                x *= 1 - 0.30 * stem
                z *= 1 - 0.30 * stem

            rotated_x = x * cos_angle - z * sin_angle
            rotated_z = x * sin_angle + z * cos_angle
            perspective = 1 / (3.4 - rotated_z)
            column = int(WIDTH / 2 + 77 * rotated_x * perspective)
            row = int(HEIGHT / 2 - 43 * y * perspective)
            if not (0 <= column < WIDTH and 0 <= row < HEIGHT):
                continue
            if rotated_z <= z_buffer[row][column]:
                continue

            normal_x = cos_lat * cos_lon
            normal_y = sin_lat
            normal_z = cos_lat * sin_lon
            rotated_normal_x = normal_x * cos_angle - normal_z * sin_angle
            rotated_normal_z = normal_x * sin_angle + normal_z * cos_angle
            diffuse = (
                rotated_normal_x * light[0]
                + normal_y * light[1]
                + rotated_normal_z * light[2]
            )
            brightness = 0.12 + max(0, min(1, (diffuse + 1) / 2)) * 0.88
            shade = max(1, min(len(CHARACTERS) - 1, int(brightness * (len(CHARACTERS) - 1))))
            if central_fissure > 0.055 or sulcus > 0.045:
                shade = max(1, shade - 3)

            z_buffer[row][column] = rotated_z
            shades[row][column] = shade

    canvas = Image.new("RGB", (760, 420), (13, 17, 23))
    draw = ImageDraw.Draw(canvas)
    cell_width = draw.textlength("M", font=font)
    cell_height = font.size + 2
    start_x = (canvas.width - WIDTH * cell_width) / 2
    start_y = (canvas.height - HEIGHT * cell_height) / 2
    for row in range(HEIGHT):
        for column in range(WIDTH):
            shade = shades[row][column]
            if shade == 0:
                continue
            draw.text(
                (start_x + column * cell_width, start_y + row * cell_height),
                CHARACTERS[shade],
                font=font,
                fill=COLORS[shade],
            )
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Generate a rotating 3D ASCII brain GIF.")
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.parent.mkdir(parents=True, exist_ok=True)

    font = load_font(9)
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
