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
    phase = frame_index * 2 * math.pi / FRAME_COUNT
    pixels = [[" "] * WIDTH for _ in range(HEIGHT)]
    for row in range(HEIGHT):
        y = (row - (HEIGHT - 1) / 2) / (HEIGHT * 0.39)
        for column in range(WIDTH):
            x = (column - (WIDTH - 1) / 2) / (WIDTH * 0.37)
            center = 0.46 if x >= 0 else -0.46
            u = (x - center) / 0.59
            v = y / 0.76
            edge_wave = 1 + 0.035 * math.sin(10 * v + 3 * u + phase)
            if u * u + v * v >= edge_wave:
                continue

            fold_a = abs(u - 0.24 * math.sin(7 * v + phase))
            fold_b = abs(u + 0.30 * math.sin(6 * v - phase + 1.2))
            fold_c = abs(v - 0.24 * math.sin(7 * u + phase + 2.1))
            fold_d = abs(v + 0.28 * math.sin(6 * u - phase + 0.7))
            groove = min(fold_a, fold_b, fold_c * 0.72, fold_d * 0.72)

            light = 0.5 + 0.5 * math.cos(x * 1.8 - phase)
            brightness = 0.30 + 0.62 * light * (0.78 + 0.22 * (1 - abs(v)))
            shade = int(brightness * (len(CHARACTERS) - 1))
            if groove < 0.045:
                shade -= 3
            if abs(x) < 0.045 and abs(y) < 0.77:
                shade -= 4
            shade = max(1, min(len(CHARACTERS) - 1, shade))
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
    parser = argparse.ArgumentParser(description="Generate a looping ASCII brain GIF.")
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
