import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


WIDTH = 160
HEIGHT = 54
FRAME_COUNT = 48
SOURCE_WIDTH = 380
SOURCE_HEIGHT = 210
CHARACTERS = " .,:;!+*#%@"
COLORS = [
    (13, 17, 23),
    (91, 48, 13),
    (145, 75, 10),
    (187, 103, 10),
    (221, 133, 19),
    (242, 160, 29),
    (250, 185, 45),
    (255, 207, 69),
    (255, 222, 107),
    (255, 236, 158),
    (255, 246, 205),
]
BEAK_COLORS = [
    (13, 17, 23),
    (101, 39, 12),
    (157, 48, 12),
    (195, 59, 13),
    (220, 72, 15),
    (239, 91, 22),
    (248, 112, 31),
    (255, 134, 47),
    (255, 157, 76),
    (255, 185, 119),
    (255, 211, 165),
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


def cubic_points(start, segments, steps=18):
    points = [start]
    x0, y0 = start
    for control1, control2, end in segments:
        x1, y1 = control1
        x2, y2 = control2
        x3, y3 = end
        for step in range(1, steps + 1):
            t = step / steps
            inverse = 1 - t
            points.append(
                (
                    inverse**3 * x0 + 3 * inverse**2 * t * x1 + 3 * inverse * t**2 * x2 + t**3 * x3,
                    inverse**3 * y0 + 3 * inverse**2 * t * y1 + 3 * inverse * t**2 * y2 + t**3 * y3,
                )
            )
        x0, y0 = x3, y3
    return points


def draw_duck_model():
    size = (760, 420)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    outline = cubic_points(
        (112, 224),
        [
            ((132, 220), (162, 191), (198, 190)),
            ((238, 164), (304, 166), (353, 181)),
            ((375, 166), (390, 137), (394, 109)),
            ((399, 80), (424, 57), (451, 64)),
            ((480, 68), (497, 89), (494, 113)),
            ((514, 109), (539, 112), (559, 120)),
            ((571, 124), (568, 134), (557, 138)),
            ((538, 144), (513, 146), (495, 145)),
            ((487, 165), (472, 178), (452, 181)),
            ((466, 198), (489, 216), (488, 241)),
            ((487, 278), (443, 308), (374, 315)),
            ((316, 338), (242, 330), (201, 303)),
            ((156, 281), (127, 254), (112, 224)),
        ],
    )
    draw.polygon(outline, fill=255)

    grooves = Image.new("L", size, 0)
    groove_draw = ImageDraw.Draw(grooves)
    wing = cubic_points(
        (224, 253),
        [
            ((252, 221), (310, 210), (357, 221)),
            ((381, 227), (395, 243), (382, 257)),
        ],
    )
    groove_draw.line(wing, fill=180, width=8, joint="curve")
    groove_draw.ellipse((460, 89, 477, 106), fill=255)
    grooves = grooves.filter(ImageFilter.GaussianBlur(radius=1.6))
    grooves = ImageChops.multiply(grooves, mask)

    mask = mask.resize((SOURCE_WIDTH, SOURCE_HEIGHT), Image.Resampling.LANCZOS)
    grooves = grooves.resize((SOURCE_WIDTH, SOURCE_HEIGHT), Image.Resampling.LANCZOS)
    mask_pixels = list(mask.tobytes())
    groove_pixels = list(grooves.tobytes())
    distance = [[10000] * SOURCE_WIDTH for _ in range(SOURCE_HEIGHT)]

    for y in range(SOURCE_HEIGHT):
        row_offset = y * SOURCE_WIDTH
        for x in range(SOURCE_WIDTH):
            index = row_offset + x
            if mask_pixels[index] < 128:
                distance[y][x] = 0
                continue
            if (
                x == 0
                or x == SOURCE_WIDTH - 1
                or y == 0
                or y == SOURCE_HEIGHT - 1
                or mask_pixels[index - 1] < 128
                or mask_pixels[index + 1] < 128
                or mask_pixels[index - SOURCE_WIDTH] < 128
                or mask_pixels[index + SOURCE_WIDTH] < 128
            ):
                distance[y][x] = 1

    diagonal = math.sqrt(2)
    for y in range(SOURCE_HEIGHT):
        for x in range(SOURCE_WIDTH):
            value = distance[y][x]
            if x:
                value = min(value, distance[y][x - 1] + 1)
            if y:
                value = min(value, distance[y - 1][x] + 1)
                if x:
                    value = min(value, distance[y - 1][x - 1] + diagonal)
                if x + 1 < SOURCE_WIDTH:
                    value = min(value, distance[y - 1][x + 1] + diagonal)
            distance[y][x] = value
    for y in range(SOURCE_HEIGHT - 1, -1, -1):
        for x in range(SOURCE_WIDTH - 1, -1, -1):
            value = distance[y][x]
            if x + 1 < SOURCE_WIDTH:
                value = min(value, distance[y][x + 1] + 1)
            if y + 1 < SOURCE_HEIGHT:
                value = min(value, distance[y + 1][x] + 1)
                if x:
                    value = min(value, distance[y + 1][x - 1] + diagonal)
                if x + 1 < SOURCE_WIDTH:
                    value = min(value, distance[y + 1][x + 1] + diagonal)
            distance[y][x] = value

    points = []
    for y in range(1, SOURCE_HEIGHT - 1):
        row_offset = y * SOURCE_WIDTH
        for x in range(1, SOURCE_WIDTH - 1):
            index = row_offset + x
            if mask_pixels[index] < 128:
                continue
            depth = min(31.0, math.sqrt(distance[y][x]) * 5.2)
            dzdx = (math.sqrt(distance[y][x + 1]) - math.sqrt(distance[y][x - 1])) * 2.6
            dzdy = (math.sqrt(distance[y + 1][x]) - math.sqrt(distance[y - 1][x])) * 2.6
            beak = x >= SOURCE_WIDTH * 0.65 and SOURCE_HEIGHT * 0.28 <= y <= SOURCE_HEIGHT * 0.36
            points.append((x, y, depth, dzdx, dzdy, groove_pixels[index] / 255, beak))
    return points


def render_frame(frame_index, font, points):
    angle = frame_index * 2 * math.pi / FRAME_COUNT
    sin_angle, cos_angle = math.sin(angle), math.cos(angle)
    z_buffer = [[-float("inf")] * WIDTH for _ in range(HEIGHT)]
    shades = [[0] * WIDTH for _ in range(HEIGHT)]
    beak_pixels = [[False] * WIDTH for _ in range(HEIGHT)]
    light = (-0.45, 0.7, 0.65)

    for x, y, depth, dzdx, dzdy, groove, beak in points:
        for side in (-1, 1):
            z = side * depth
            nx = -side * dzdx
            ny = -side * dzdy
            nz = float(side)
            normal_length = math.sqrt(nx * nx + ny * ny + nz * nz)
            nx /= normal_length
            ny /= normal_length
            nz /= normal_length
            rotated_x = (x - 170) * cos_angle - z * sin_angle
            rotated_z = (x - 170) * sin_angle + z * cos_angle
            rotated_nx = nx * cos_angle - nz * sin_angle
            rotated_nz = nx * sin_angle + nz * cos_angle
            if rotated_nz <= 0:
                continue

            perspective = 1 + rotated_z * 0.0012
            column = int(WIDTH / 2 + rotated_x * 0.39 * perspective)
            row = int(HEIGHT / 2 + (y - 102) * 0.19 * perspective)
            if not (0 <= column < WIDTH and 0 <= row < HEIGHT):
                continue
            if rotated_z <= z_buffer[row][column]:
                continue

            diffuse = rotated_nx * light[0] + ny * light[1] + rotated_nz * light[2]
            brightness = 0.18 + 0.82 * max(0, min(1, (diffuse + 1) / 2))
            shade = int(2 + brightness * 7 - groove * 7)
            z_buffer[row][column] = rotated_z
            shades[row][column] = max(1, min(len(CHARACTERS) - 1, shade))
            beak_pixels[row][column] = beak

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
            palette = BEAK_COLORS if beak_pixels[row][column] else COLORS
            draw.text(
                (start_x + column * cell_width, start_y + row * cell_height),
                CHARACTERS[shade],
                font=font,
                fill=palette[shade],
            )
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Generate a rotating 3D ASCII debugging duck GIF.")
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.parent.mkdir(parents=True, exist_ok=True)

    font = load_font(7)
    points = draw_duck_model()
    frames = [render_frame(index, font, points) for index in range(FRAME_COUNT)]
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
