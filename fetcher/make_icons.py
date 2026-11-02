"""Maakt de app-iconen (eenmalig). Gebruik: python fetcher/make_icons.py"""
import math
import struct
import zlib
from pathlib import Path

BG = (242, 80, 47)
FG = (255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "app" / "icons"

# drie afgeronde balken (een nieuwsfeed) en een stip, binnen de veilige zone van Android-iconen
BARS = [(-0.42, -0.30, 0.42), (-0.42, 0.0, 0.16), (-0.42, 0.30, -0.10)]  # (x_start, y_midden, x_eind)
BAR_HALF_HEIGHT = 0.075
DOT = (0.30, 0.30, 0.10)


def inside_mark(x, y):
    for x0, ym, x1 in BARS:
        cx = min(max(x, x0), x1)
        if math.hypot(x - cx, y - ym) <= BAR_HALF_HEIGHT:
            return True
    return math.hypot(x - DOT[0], y - DOT[1]) <= DOT[2]


def pixel(px, py, size):
    # coördinaten -1..1, 4x supersampling voor zachte randen
    hits = 0
    for sx in (0.25, 0.75):
        for sy in (0.25, 0.75):
            x = (px + sx) / size * 2 - 1
            y = (py + sy) / size * 2 - 1
            if inside_mark(x, y):
                hits += 1
    a = hits / 4
    return bytes(round(BG[i] * (1 - a) + FG[i] * a) for i in range(3))


def png(size):
    rows = b"".join(b"\x00" + b"".join(pixel(x, y, size) for x in range(size)) for y in range(size))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


OUT.mkdir(parents=True, exist_ok=True)
for s in (192, 512):
    (OUT / f"icon-{s}.png").write_bytes(png(s))
print("Iconen gemaakt in", OUT)
