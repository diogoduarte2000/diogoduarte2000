import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter


WIDTH = 160
HEIGHT = 54
FRAME_COUNT = 48
SOURCE_WIDTH = 380
SOURCE_HEIGHT = 210
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


def draw_brain_model():
    size = (760, 420)
    cortex = Image.new("L", size, 0)
    cortex_draw = ImageDraw.Draw(cortex)
    outline = cubic_points(
        (178, 223),
        [
            ((157, 208), (161, 174), (185, 153)),
            ((177, 119), (213, 91), (251, 105)),
            ((268, 71), (315, 64), (341, 98)),
            ((372, 65), (412, 71), (429, 105)),
            ((464, 77), (507, 88), (512, 127)),
            ((552, 128), (574, 160), (555, 190)),
            ((580, 209), (569, 235), (539, 248)),
            ((517, 260), (488, 251), (468, 237)),
            ((447, 260), (412, 261), (390, 244)),
            ((366, 273), (330, 282), (306, 256)),
            ((277, 276), (238, 267), (226, 243)),
            ((203, 246), (186, 237), (178, 223)),
        ],
    )
    cortex_draw.polygon(outline, fill=255)

    cerebellum = Image.new("L", size, 0)
    cerebellum_draw = ImageDraw.Draw(cerebellum)
    cerebellum_outline = cubic_points(
        (468, 231),
        [
            ((480, 210), (511, 211), (527, 225)),
            ((553, 223), (574, 239), (568, 255)),
            ((582, 270), (565, 289), (545, 286)),
            ((528, 301), (497, 290), (489, 275)),
            ((469, 270), (459, 249), (468, 231)),
        ],
    )
    cerebellum_draw.polygon(cerebellum_outline, fill=255)

    stem = Image.new("L", size, 0)
    stem_draw = ImageDraw.Draw(stem)
    stem_outline = cubic_points(
        (433, 235),
        [
            ((448, 247), (454, 265), (457, 283)),
            ((464, 303), (466, 324), (455, 345)),
            ((447, 348), (437, 341), (439, 326)),
            ((436, 304), (429, 284), (423, 269)),
            ((417, 254), (421, 241), (433, 235)),
        ],
    )
    stem_draw.polygon(stem_outline, fill=255)

    mask = ImageChops.lighter(cortex, ImageChops.lighter(cerebellum, stem))
    grooves = Image.new("L", size, 0)
    groove_draw = ImageDraw.Draw(grooves)
    sulci = [
        ((229, 121), [((246, 139), (233, 165), (247, 185)), ((261, 202), (247, 221), (253, 245))]),
        ((285, 105), [((303, 124), (286, 143), (300, 160)), ((317, 178), (301, 201), (310, 226))]),
        ((351, 106), [((337, 128), (356, 147), (342, 166)), ((329, 188), (350, 207), (339, 231))]),
        ((394, 103), [((410, 124), (389, 145), (408, 164)), ((424, 183), (402, 201), (414, 228))]),
        ((459, 111), [((446, 133), (466, 148), (448, 167)), ((437, 183), (460, 201), (448, 219))]),
        ((510, 148), [((491, 163), (513, 178), (493, 195)), ((483, 208), (501, 220), (484, 236))]),
        ((267, 248), [((292, 235), (315, 242), (329, 263))]),
        ((353, 244), [((371, 226), (391, 230), (405, 249))]),
        ((485, 246), [((505, 238), (526, 243), (540, 254))]),
    ]
    for start, segments in sulci:
        groove_draw.line(cubic_points(start, segments), fill=255, width=15, joint="curve")
    for index in range(6):
        y = 237 + index * 8
        start = (485, y)
        segments = [
            ((505, y - 11), (531, y - 11), (554, y - 4)),
            ((562, y), (556, y + 3), (544, y + 4)),
        ]
        groove_draw.line(cubic_points(start, segments), fill=235, width=11, joint="curve")
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
            points.append((x, y, depth, dzdx, dzdy, groove_pixels[index] / 255))
    return points


def render_frame(frame_index, font, points):
    phase = frame_index * 2 * math.pi / FRAME_COUNT
    angle = 0.12 + 0.72 * math.sin(phase)
    sin_angle, cos_angle = math.sin(angle), math.cos(angle)
    z_buffer = [[-float("inf")] * WIDTH for _ in range(HEIGHT)]
    shades = [[0] * WIDTH for _ in range(HEIGHT)]
    light = (-0.45, 0.7, 0.65)

    for x, y, depth, dzdx, dzdy, groove in points:
        for side in (-1, 1):
            z = side * depth
            nx = -side * dzdx
            ny = -side * dzdy
            nz = float(side)
            normal_length = math.sqrt(nx * nx + ny * ny + nz * nz)
            nx /= normal_length
            ny /= normal_length
            nz /= normal_length
            rotated_x = (x - 190) * cos_angle - z * sin_angle
            rotated_z = (x - 190) * sin_angle + z * cos_angle
            rotated_nx = nx * cos_angle - nz * sin_angle
            rotated_nz = nx * sin_angle + nz * cos_angle
            if rotated_nz <= 0:
                continue

            perspective = 1 + rotated_z * 0.0015
            column = int(WIDTH / 2 + rotated_x * 0.42 * perspective)
            row = int(HEIGHT / 2 + (y - 105) * 0.26 * perspective)
            if not (0 <= column < WIDTH and 0 <= row < HEIGHT):
                continue
            if rotated_z <= z_buffer[row][column]:
                continue

            diffuse = rotated_nx * light[0] + ny * light[1] + rotated_nz * light[2]
            brightness = 0.18 + 0.82 * max(0, min(1, (diffuse + 1) / 2))
            shade = int(2 + brightness * 7 - groove * 7)
            z_buffer[row][column] = rotated_z
            shades[row][column] = max(1, min(len(CHARACTERS) - 1, shade))

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

    font = load_font(7)
    points = draw_brain_model()
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
