"""Maakt de app-iconen (eenmalig). Gebruik: python fetcher/make_icons.py"""
import math
import struct
import zlib
from pathlib import Path

BG = (242, 80, 47)
FG = (255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "app" / "icons"

# drie afgeronde strepen die samen een F vormen, met de stip van de nieuwsfeed ernaast
BARS = [(-0.36, -0.40, -0.36, 0.40), (-0.36, -0.40, 0.42, -0.40), (-0.36, -0.02, 0.20, -0.02)]  # (x0, y0, x1, y1)
BAR_HALF_WIDTH = 0.09
DOT = (0.20, 0.31, 0.105)
CORNER = 0.42  # afronding van het gewone icoon; het maskable icoon vult het hele vlak (Android rondt het zelf af)


def inside_mark(x, y):
    for x0, y0, x1, y1 in BARS:
        cx, cy = min(max(x, x0), x1), min(max(y, y0), y1)
        if math.hypot(x - cx, y - cy) <= BAR_HALF_WIDTH:
            return True
    return math.hypot(x - DOT[0], y - DOT[1]) <= DOT[2]


def inside_shape(x, y):
    dx, dy = max(abs(x) - (1 - CORNER), 0), max(abs(y) - (1 - CORNER), 0)
    return math.hypot(dx, dy) <= CORNER


def pixel(px, py, size, rounded):
    # coördinaten -1..1, 16x supersampling voor zachte randen
    mark = shape = 0
    for sx in (0.125, 0.375, 0.625, 0.875):
        for sy in (0.125, 0.375, 0.625, 0.875):
            x = (px + sx) / size * 2 - 1
            y = (py + sy) / size * 2 - 1
            shape += not rounded or inside_shape(x, y)
            mark += inside_mark(x, y)
    a = mark / 16
    return bytes(round(BG[i] * (1 - a) + FG[i] * a) for i in range(3)) + bytes([round(shape / 16 * 255)])


def png(size, rounded):
    rows = b"".join(b"\x00" + b"".join(pixel(x, y, size, rounded) for x in range(size)) for y in range(size))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


OUT.mkdir(parents=True, exist_ok=True)
for s in (192, 512):
    (OUT / f"icon-{s}.png").write_bytes(png(s, rounded=True))
    (OUT / f"maskable-{s}.png").write_bytes(png(s, rounded=False))
print("Iconen gemaakt in", OUT)
